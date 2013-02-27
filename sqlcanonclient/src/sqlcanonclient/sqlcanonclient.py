#!/usr/bin/env python

import argparse
import datetime
import getpass
import itertools
import json
import pprint
import os
import re
import socket
import sys
from sys import stdin
import tempfile
import time
import traceback
import urllib
import urllib2

from construct.protocols.ipstack import ip_stack
import pcap
import mmh3
import MySQLdb
import sqlite3
import sqlparse
from sqlparse.tokens import Token

STATEMENT_DATA_MAX_ROWS = 1024

PP = pprint.PrettyPrinter(indent=4)

ARGS = None

STATEMENT_UNKNOWN = 'UNKNOWN'

QUERY_LOG_PATTERN_QUERY_START = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+'

QUERY_LOG_PATTERN_FULL_QUERY = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+(?P<query>.+(\n.+)*?)(?=((\d+\s\d+:\d+:\d+\s+)|(\s+\d+\s)|(\s*$)))'

# collapse target parts (for now target parts are in and values)
COLLAPSE_TARGET_PARTS = True

HOSTNAME = socket.gethostname()

EXPLAIN_OPTIONS = None

class url_request(object):
    """wrapper for urllib2"""

    def __init__(self, url, data=None, headers={}):
        request = urllib2.Request(url, data=data, headers=headers)
        try:
            self._response = urllib2.urlopen(request).read()
            self._code = 200
        except urllib2.URLError, e:
            self._response = e.read()
            self._code = e.code

    @property
    def content(self):
        return self._response

    @property
    def code(self):
        return self._code

def int_to_hex_str(n):
    """
    Returns hex representation of a number.
    """

    return '%08X' % (n & 0xFFFFFFFF,)

class QueryLister:
    def __init__(self):
        """
        Initialization.
        """

        # list item will be a list in the following format:
        #     [dt, statement, canonicalized_query, hash, count]
        #
        #     dt:
        #         statement date/time
        #     statement:
        #         statement
        #     canonicalized_statement:
        #         canonicalized statement
        #     hash:
        #         hash of canonicalized_statement
        #     count:
        #         for a given window, number of instances of statements, that are similar to this statement, found
        self.statement_list = []


    def append_statement(self, statement, canonicalized_statement, dt=None):
        """
        Appends statement to list.
        """

        if not dt:
            dt = datetime.datetime.now()

        # order of items on list is expected to be ordered by datetime in ascending order
        # do not allow violation of this rule
        if self.statement_list:
            assert self.statement_list[len(self.statement_list) - 1][0] <= dt

        self.statement_list.append([dt, statement, canonicalized_statement, mmh3.hash(canonicalized_statement), 0])

    def get_list(self, dt_start, dt_end, remove_older_items=True):
        """
        Returns part of the list (filtered by datetime start and end) with updated count field.

        dt_start
            filter: datetime start
        dt_end
            filter: datetime end
        remove_older_items:
            exclude items whose datetime is < dt_start
        """

        assert dt_start <= dt_end

        # Store counts here.
        # This will look like:
        #     counts = {
        #         1234: {  # hash
        #             'count': 3,
        #             'indices': [0, 1, 4]   # indices of list items who have the same canonicalized statement
        #         },
        #         5678: {
        #             'count': 2,
        #             'indices': [2, 3]
        #         }
        #     }
        counts = {}

        # store the indices of the items that will be included in
        # the final result
        list_indices = []

        # calculate counts
        for index, statement_list_item in enumerate(self.statement_list):
            dt, query, canonicalized_query, hash, count = statement_list_item

            if(dt_start <= dt <= dt_end):
                list_indices.append(index)
                if counts.has_key(hash):
                    counts[hash]['count'] += 1
                else:
                    counts[hash] = dict(count=1, indices=[])

                # remember indices of queries that have the same canonicalized statement
                counts[hash]['indices'].append(index)

        # reflect counts in result (statement_list subset)
        for hash, info in counts.iteritems():
            count = info['count']
            indices = info['indices']
            for index in indices:
                self.statement_list[index][4] = count

        if list_indices:
            result = self.statement_list[min(list_indices):max(list_indices) + 1]
        else:
            result = []

        if remove_older_items:
            if list_indices and min(list_indices) < len(self.statement_list):
                self.statement_list = self.statement_list[min(list_indices):]
            else:
                self.statement_list = []

        return result

def canonicalizer_default(token):
    """
    Default canonicalizer.

    Returns data in this format (normalized statement, canonicalized statement, values)
    """
    return (token.normalized, token.normalized, [])

def canonicalizer_whitespace(token):
    """
    Reduces whitespaces into a single space.

    Returns data in this format (normalized statement, canonicalized statement, values)
    """
    return (' ', ' ', [])

def canonicalizer_name(token):
    """
    Quotes names always.
    """

    if token.normalized.startswith('@'):
        normalized = token.normalized
    else:
        normalized = '`{0}`'.format(token.normalized.strip(' `'))
    return (normalized, normalized, [])

def canonicalizer_number_integer(token):
    """
    Canonicalizes integer numbers.
    """

    normalized = token.normalized
    canonicalized = '%d'
    values = [int(token.value)]
    return (normalized, canonicalized, values)

def canonicalizer_number_float(token):
    """
    Canonicalizes float numbers.
    """

    normalized = token.normalized
    canonicalized = '%f'
    values = [float(token.value)]
    return (normalized, canonicalized, values)

def canonicalizer_string_single(token):
    """
    Canonicalizes strings with single quotes.
    """

    normalized = token.normalized
    canonicalized = '%s'
    values = [token.value.strip("'").replace(r"\'", "'")]
    return (normalized, canonicalized, values)

def canonicalizer_string_symbol(token):
    """
    Canonicalizes strings with quotes (double).

    Turns enclosing double quotes to single quotes.
    Replaces content: \" to "
    """

    normalized = r"""'{0}'""".format(token.normalized.strip('"').replace(r'\"', '"'))
    canonicalized = '%s'
    values = [token.value.strip('"').replace(r'\"', '"')]
    return (normalized, canonicalized, values)

# canonicalizers based on token type
CANONICALIZERS = {
    Token.Text.Whitespace: canonicalizer_whitespace,
    Token.Text.Whitespace.Newline: canonicalizer_whitespace,
    Token.Name: canonicalizer_name,
    Token.Literal.Number.Integer: canonicalizer_number_integer,
    Token.Literal.Number.Float: canonicalizer_number_float,
    Token.Literal.String.Single: canonicalizer_string_single,
    Token.Literal.String.Symbol: canonicalizer_string_symbol,
    }

def canonicalizer_parenthesis(token):
    """
    Canonicalizes parenthesis token.

    Whitespaces are canonicalized to empty string.
    """

    assert token.is_group()

    normalized = ''
    canonicalized = ''
    values = []

    for child_token in token.tokens:
        if child_token.ttype in (Token.Text.Whitespace,
                                 Token.Text.Whitespace.Newline):
            child_token_index = token.token_index(child_token)
            next_child_token = token.token_next(child_token_index, skip_ws=False)
            prev_child_token = token.token_prev(child_token_index, skip_ws=False)
            if ((prev_child_token and prev_child_token.ttype in (Token.Keyword,)) or
                (next_child_token and next_child_token.ttype in (Token.Keyword,))):
                # maintain a single space if previous or next token is a keyword
                c_normalized, c_canonicalized, c_values = canonicalize_token(
                    child_token)
            else:
                c_normalized, c_canonicalized, c_values = ('', '', [])
        else:
            c_normalized, c_canonicalized, c_values = canonicalize_token(
                child_token)
        normalized += c_normalized
        canonicalized += c_canonicalized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, canonicalized, values)

def canonicalizer_where(token):
    """
    Canonicalizes where clause.

    Consecutive whitespaces are reduced to one.
    """

    assert token.is_group()

    normalized = ''
    canonicalized = ''
    values = []

    found_in_keyword = False
    found_new_keyword_after_in_keyword = False

    for child_token in token.tokens:
        #print 'child_token.ttype = {0}'.format(child_token.ttype)
        #print 'type(child_token) = {0}'.format(type(child_token))
        #print 'child_token.normalized = <{0}>'.format(child_token.normalized)
        #print 'child_token child tokens: {0}'.format(child_token.tokens if child_token.is_group() else None)
        child_token_index = token.token_index(child_token)
        next_child_token = token.token_next(child_token_index, skip_ws=False)
        next_nonws_token = token.token_next(child_token_index)
        prev_nonws_token = token.token_prev(child_token_index)
        if (child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline) and
            (
                (next_child_token and next_child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline)) or
                (next_nonws_token and next_nonws_token.ttype in (Token.Operator.Comparison,)) or
                (prev_nonws_token and prev_nonws_token.ttype in (Token.Operator.Comparison,))
                )):
            c_normalized, c_canonicalized, c_values = ('', '', [])
        elif COLLAPSE_TARGET_PARTS and child_token.ttype in (Token.Keyword,):
            if child_token.normalized == 'IN':
                found_in_keyword = True
            else:
                if found_in_keyword:
                    found_new_keyword_after_in_keyword = True
            c_normalized, c_canonicalized, c_values = canonicalize_token(child_token)
        elif COLLAPSE_TARGET_PARTS and child_token.is_group() and\
             type(child_token) is sqlparse.sql.Parenthesis and\
             found_in_keyword and not found_new_keyword_after_in_keyword:
            c_normalized, c_canonicalized, c_values = ('(N)', '(N)', [])
        else:
            c_normalized, c_canonicalized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        canonicalized += c_canonicalized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, canonicalized, values)

def canonicalizer_identifier_list(token):
    """
    Canonicalizes IdentifierList token.

    Whitespaces are canonicalized to empty string.
    """

    assert token.is_group()

    normalized = ''
    canonicalized = ''
    values = []

    for child_token in token.tokens:
        if child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
            c_normalized, c_canonicalized, c_values = ('', '', [])
        else:
            c_normalized, c_canonicalized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        canonicalized += c_canonicalized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, canonicalized, values)

def canonicalizer_comparison(token):
    """
    Canonicalizes Comparison token.

    Whitespaces are canonicalized to empty string.
    """

    assert token.is_group()

    normalized = ''
    canonicalized = ''
    values = []

    for child_token in token.tokens:
        if child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
            c_normalized, c_canonicalized, c_values = ('', '', [])
        else:
            c_normalized, c_canonicalized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        canonicalized += c_canonicalized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, canonicalized, values)

SQL_FUNCTIONS = ('AVG', 'BIT_AND', 'BIT_OR', 'BIT_XOR', 'COUNT', 'GROUP_CONCAT',
                 'MAX', 'MIN', 'STD', 'STDDEV_POP', 'STDDEV_SAMP', 'STDDEV', 'SUM',
                 'VAR_POP', 'VAR_SAMP', 'VARIANCE', )

def canonicalizer_function(token):
    """
    Canonicalizes Function token.

    Identifier part is checked and if it is one of the SQL functions
    like COUNT, it is converted to uppercase and not quoted.
    Whitespaces are canonicalized to empty string.
    """
    #print 'canonicalizer_function'
    assert token.is_group()

    normalized = ''
    canonicalized = ''
    values = []

    for child_token in token.tokens:
        if type(child_token) is sqlparse.sql.Identifier:
            name = child_token.normalized
            if name.upper() in SQL_FUNCTIONS:
                c_normalized, c_canonicalized, c_values = (
                    name.upper(), name.upper(), [])
            else:
                c_normalized, c_canonicalized, c_values = (name, name, [])
        elif child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
            c_normalized, c_canonicalized, c_values = ('', '', [])
        else:
            c_normalized, c_canonicalized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        canonicalized += c_canonicalized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, canonicalized, values)

CANONICALIZERS_BY_CLASS_TYPE = {
    sqlparse.sql.Parenthesis: canonicalizer_parenthesis,
    sqlparse.sql.IdentifierList: canonicalizer_identifier_list,
    sqlparse.sql.Comparison: canonicalizer_comparison,
    sqlparse.sql.Function: canonicalizer_function,
    sqlparse.sql.Where: canonicalizer_where,
    }


def canonicalize_token(token):
    """
    Canonicalize a sql statement token.
    """

    #print 'token.ttype = {0}'.format(token.ttype)
    #print 'type(token) = {0}'.format(type(token))
    #print 'token.normalized = <{0}>'.format(token.normalized)
    #print 'child tokens: {0}'.format(token.tokens if token.is_group() else None)

    normalized = ''
    canonicalized = ''
    values = []
    if token.ttype and CANONICALIZERS.has_key(token.ttype):
        normalized, canonicalized, values = CANONICALIZERS[token.ttype](token)
    elif token.is_group():
        if CANONICALIZERS_BY_CLASS_TYPE.has_key(type(token)):
            normalized, canonicalized, values = CANONICALIZERS_BY_CLASS_TYPE[type(token)](token)
        else:
            for child_token in token.tokens:
                c_normalized, c_canonicalized, c_values = canonicalize_token(child_token)
                normalized += c_normalized
                canonicalized += c_canonicalized
                for c_value in c_values:
                    values.append(c_value)
    else:
        # no assigned canonicalizer for token? use default
        normalized, canonicalized, values = canonicalizer_default(token)

    return (normalized, canonicalized, values)

def canonicalizer_statement_insert(stmt):
    """
    Canonicalizes insert statements.
    """

    assert stmt.get_type() == 'INSERT'

    normalized = ''
    canonicalized = ''
    values = []

    found_values_keyword = False
    first_parenthesis_after_values_keyword = None
    found_new_keyword_afer_values_keyword = False

    for token in stmt.tokens:
        #print 'token.ttype = {0}'.format(token.ttype)
        #print 'type(token) = {0}'.format(type(token))
        #print 'token.normalized = <{0}>'.format(token.normalized)
        #print 'child tokens: {0}'.format(token.tokens if token.is_group() else None)

        token_index = stmt.token_index(token)
        next_token = stmt.token_next(token_index, skip_ws=False)
        prev_token = stmt.token_prev(token_index, skip_ws=False)
        if (token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline) and
            next_token and
            next_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline)):
            t_normalized, t_canonicalized, t_values = ('', '', [])
        elif (type(token) is sqlparse.sql.Identifier) and prev_token.ttype in (Token.Operator,):
            t_normalized, t_canonicalized, t_values = (token.normalized, token.normalized, [])
        elif COLLAPSE_TARGET_PARTS and token.ttype in (Token.Keyword,):
            if token.normalized == 'VALUES':
                found_values_keyword = True
                #print 'found VALUES keyword: {0}'.format(token.normalized)
            else:
                if found_values_keyword:
                    found_new_keyword_afer_values_keyword = True
            t_normalized, t_canonicalized, t_values = canonicalize_token(token)
        elif COLLAPSE_TARGET_PARTS and token.is_group() and\
             type(token) is sqlparse.sql.Parenthesis and\
             found_values_keyword and not found_new_keyword_afer_values_keyword:

            if not first_parenthesis_after_values_keyword:
                first_parenthesis_after_values_keyword = token
            if first_parenthesis_after_values_keyword == token:
                t_normalized, t_canonicalized, t_values = ('(N)', '(N)', [])
            else:
                t_normalized, t_canonicalized, t_values = ('', '', [])
        elif COLLAPSE_TARGET_PARTS and token.ttype in (Token.Punctuation,)\
             and found_values_keyword and not found_new_keyword_afer_values_keyword:
            t_normalized, t_canonicalized, t_values = ('', '', [])
        else:
            t_normalized, t_canonicalized, t_values = canonicalize_token(token)
        normalized += t_normalized
        canonicalized += t_canonicalized
        for t_value in t_values:
            values.append(t_value)

    normalized = normalized.strip(' ;')
    canonicalized = canonicalized.strip(' ;')

    return (normalized, canonicalized, values)

def canonicalize_statement(statement):
    """
    Canonicalizes statement(s).

    Returns a list of
        (
            original statement,
            normalized statement,
            canonicalized statement,
            values for canonicalized statement
        )
    """
    result = []

    parsed = sqlparse.parse(statement)

    for stmt in parsed:
        #print 'stmt => {0} <='.format(stmt)
        #print 'stmt.tokens => {0}'.format(stmt.tokens)
        if stmt.get_type() == 'INSERT':
            #print 'stmt.get_type() => {0}'.format(stmt.get_type())
            stmt_normalized, stmt_canonicalized, stmt_values = canonicalizer_statement_insert(stmt)
            result.append(('{0}'.format(stmt), stmt_normalized, stmt_canonicalized, stmt_values))
            continue
        elif stmt.get_type() == STATEMENT_UNKNOWN:
            #print 'UNKNOWN: => {0} <='.format(stmt)
            result.append(
                ('{0}'.format(stmt), '{0}'.format(stmt), STATEMENT_UNKNOWN, [])
            )
            continue

        normalized = ''
        canonicalized = ''
        values = []
        for token in stmt.tokens:
            token_index = stmt.token_index(token)
            next_token = stmt.token_next(token_index, skip_ws=False)
            prev_token = stmt.token_prev(token_index, skip_ws=False)
            if (token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline) and
                next_token and
                next_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline)):
                t_normalized, t_canonicalized, t_values = ('', '', [])
            elif (type(token) is sqlparse.sql.Identifier) and prev_token.ttype in (Token.Operator,):
                t_normalized, t_canonicalized, t_values = (token.normalized, token.normalized, [])
            else:
                t_normalized, t_canonicalized, t_values = canonicalize_token(token)
            normalized += t_normalized
            canonicalized += t_canonicalized
            for t_value in t_values:
                values.append(t_value)

        normalized = normalized.strip(' ;')
        canonicalized = canonicalized.strip(' ;')

        result.append((
            '{0}'.format(stmt),
            normalized,
            canonicalized,
            values))
    return result


class QueryLogItemParser(object):
    """Query log item parser."""

    def __init__(self):
        super(QueryLogItemParser, self).__init__()

        self.dt = None
        self.query_time = None
        self.lock_time = None
        self.rows_sent = None
        self.rows_examined = None
        self.statement = None

    def parse_statement(self, lines_to_parse):
        self.statement = lines_to_parse.strip(' ;')
        return self.statement


def process_packet(pktlen, data, timestamp):
    if not data:
        return

    print 'pktlen:', pktlen, 'dt:', (
        datetime.datetime.fromtimestamp(timestamp))
    stack = ip_stack.parse(data)
    payload = stack.next.next.next
    print payload
    print

    try:
        # MySQL queries start on the 6th char (?)
        payload = payload[5:]
        log_item_parser = QueryLogItemParser()
        if log_item_parser.parse_statement(payload):
            print log_item_parser.statement
            DataManager.save_data(log_item_parser)

    except Exception, e:
        print 'ERROR: {0}'.format(e)


def run_packet_sniffer():

    p = pcap.pcapObject()
    dev = ARGS.interface
    net, mask = pcap.lookupnet(dev)
    print 'net:', net, 'mask:', mask

    # sample dev:
    #     eth0
    #     wlan0
    #     lo
    p.open_live(dev, 1600, 0, 100)

    # sample filter:
    #     dst port 3306
    # see: http://www.manpagez.com/man/7/pcap-filter/
    p.setfilter(ARGS.filter, 0, 0)

    print 'Press CTRL+C to end capture'
    try:
        while True:
            p.dispatch(1, process_packet)
    except KeyboardInterrupt:
        print # Empty line where ^C from CTRL+C is displayed
        print '%s' % sys.exc_type
        print 'shutting down'
        print '%d packets received, %d packets dropped, %d packets dropped by interface' % p.stats()


class SlowQueryLogItemParser(object):
    """Slow query log item parser."""

    def __init__(self):
        super(SlowQueryLogItemParser, self).__init__()

        self.dt = None
        self.query_time = None
        self.lock_time = None
        self.rows_sent = None
        self.rows_examined = None
        self.statement = None

        self.line_time_info = None
        self.line_user_info = None
        self.line_statement = None
        self.line_administrator_command = None

        self.line_header_data = []
        self.header_data = {}

    def parse_time_info(self, line):
        """Parses time info."""

        __, __, date_str, time_str = line.split()
        self.dt = datetime.datetime.strptime(
            ' '.join([date_str, time_str]), '%y%m%d %H:%M:%S')

    def parse_user_info(self, line):
        """Parses user info."""

        # Just store it for now.
        self.line_user_info = line

    def parse_administrator_command(self, line):
        # Just store it for now
        self.line_administator_command = line

    def parse_header_data(self, line, source):
        """Parses header data."""

        self.line_header_data = []
        self.header_data = {}
        while True:
            # make sure it starts with #
            if line.startswith('#'):
                self.line_header_data.append(line)
                if line.startswith('# Time'):
                    self.parse_time_info(line)
                elif line.startswith('# User@Host'):
                    self.parse_user_info(line)
                elif line.startswith('# administrator command'):
                    self.parse_administrator_command(line)
                else:
                    line = line[1:]
                    words = [word.lower().strip().rstrip(':')
                        for word in line.split()]
                    i = iter(words)
                    self.header_data.update(dict(itertools.izip(i, i)))
                line = source.readline()
            else:
                # Line does not start with #,
                # this means that this is the end of the variables
                # section, we exit the loop and return the last line
                # read so that the next parser can process it.
                break
        # be sure to return the last line read
        return line

    def parse_statement(self, line, source):
        """Parses statement."""

        statement = line

        # statement could span multiple lines
        while True:
            line = source.readline()
            if line:
                if line.rstrip().endswith('started with:'):
                    break

                if line.startswith('#'):
                    # this is the start of another query header
                    break
                else:
                    # add this line to statement
                    statement += line
            else:
                break

        self.statement = statement

        # make sure to return the last read line from file
        return line


class SlowQueryLogProcessor(object):
    """Encapsulates operations on MySQL slow query log."""

    def __init__(self):
        super(SlowQueryLogProcessor, self).__init__()

    def process_log_contents(self, source):
        """Process contents of MySQL slow query log."""

        last_dt = None
        line = source.readline()
        while True:
            if not line:
                break

            if line.rstrip().endswith('started with:'):
                # ignore current and the next two lines
                line = source.readline()
                line = source.readline()

                # this next line is the one that needs processing
                line = source.readline()

                # loop again so we could recheck lines to ignore
                continue

            if line.startswith('# '):
                log_item_parser = SlowQueryLogItemParser()
                line = log_item_parser.parse_header_data(line, source)

                for k,v in log_item_parser.header_data.iteritems():
                    print '{0}: {1}'.format(k, v),
                print

                # read statement
                line = log_item_parser.parse_statement(line, source)

                # TODO: do something about strings causing UnicodeDecodeError

                print log_item_parser.statement

                try:
                    DataManager.save_data(log_item_parser)
                except Exception, e:
                    print 'ERROR: {0}'.format(e)

            else:
                line = source.readline()


class LocalData:
    """Encapsulates local data operations."""

    DB = None

    @staticmethod
    def init_db(db):
        LocalData.DB = db

        conn = sqlite3.connect(db)
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS statementdata(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dt TEXT,
                    statement TEXT,
                    hostname TEXT,
                    canonicalized_statement TEXT,
                    canonicalized_statement_hash INT,
                    canonicalized_statement_hostname_hash INT,
                    query_time REAL,
                    lock_time REAL,
                    rows_sent INT,
                    rows_examined INT,
                    rows_affected INT,
                    rows_read INT,
                    bytes_sent INT,
                    tmp_tables INT,
                    tmp_disk_tables INT,
                    tmp_table_sizes INT,
                    sequence_id INT,
                    last_updated TEXT
                )
                """)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS explainedstatement(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dt TEXT,
                    statement TEXT,
                    hostname TEXT,
                    canonicalized_statement TEXT,
                    canonicalized_statement_hash INT,
                    canonicalized_statement_hostname_hash INT,
                    db TEXT
                )
                """)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS explainresult(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    explained_statement_id INT,
                    select_id INT,
                    select_type TEXT,
                    `table` TEXT,
                    type TEXT,
                    possible_keys TEXT,
                    key TEXT,
                    key_len INT,
                    ref TEXT,
                    rows INT,
                    extra TEXT
                )
                """)
            cur.close()

    @staticmethod
    def save_statement_data(
            dt, statement, hostname,
            canonicalized_statement, canonicalized_statement_hash,
            canonicalized_statement_hostname_hash,
            header_data):
        """Saves statement data.

        Statement data are stored as RRD.
        """

        if dt is None:
            dt = datetime.datetime.now()

        is_select_statement = canonicalized_statement.startswith('SELECT ')
        first_seen = False

        conn = sqlite3.connect(LocalData.DB)
        with conn:
            cur = conn.cursor()

            if is_select_statement:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM statementdata
                    WHERE canonicalized_statement_hostname_hash=?
                    """, (canonicalized_statement_hostname_hash,))
                row = cur.fetchone()
                count = 0
                if row:
                    count = row[0]
                first_seen = not count

            insert_sql = (
                """
                INSERT INTO statementdata(
                    dt, statement, hostname,
                    canonicalized_statement,
                    canonicalized_statement_hash,
                    canonicalized_statement_hostname_hash,
                    query_time, lock_time, rows_sent, rows_examined,
                    rows_affected, rows_read, bytes_sent,
                    tmp_tables, tmp_disk_tables, tmp_table_sizes,
                    sequence_id, last_updated)
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)
            update_sql = (
                """
                UPDATE statementdata
                SET
                    dt = ?,
                    statement = ?,
                    hostname = ?,
                    canonicalized_statement = ?,
                    canonicalized_statement_hash = ?,
                    canonicalized_statement_hostname_hash = ?,
                    query_time = ?,
                    lock_time = ?,
                    rows_sent = ?,
                    rows_examined = ?,
                    rows_affected = ?,
                    rows_read = ?,
                    bytes_sent = ?,
                    tmp_tables = ?,
                    tmp_disk_tables = ?,
                    tmp_table_sizes = ?,
                    last_updated = ?
                WHERE sequence_id = ?
                """)

            # calculate the next sequence id to use
            cur.execute(
                """
                SELECT sequence_id FROM statementdata
                ORDER BY last_updated DESC
                """)
            row = cur.fetchone()
            if row:
                sequence_id = (
                    (row[0] + 1) % STATEMENT_DATA_MAX_ROWS)
            else:
                sequence_id = 1

            cur.execute(
                """
                SELECT COUNT(*) FROM statementdata WHERE sequence_id = ?
                """, (sequence_id, ))
            row = cur.fetchone()
            last_updated = datetime.datetime.now()
            header_data_keys = (
                'query_time', 'lock_time', 'rows_sent',
                'rows_examined', 'rows_affected', 'rows_read',
                'bytes_sent', 'tmp_tables', 'tmp_disk_tables',
                'tmp_table_sizes')
            data = [
                dt, statement, hostname,
                canonicalized_statement,
                canonicalized_statement_hash,
                canonicalized_statement_hostname_hash]
            data.extend(
                [header_data.get(k) for k in header_data_keys])
            if row and int(row[0]):
                data.extend((last_updated, sequence_id))
                cur.execute(update_sql, data)
            else:
                data.extend((sequence_id, last_updated))
                cur.execute(insert_sql, data)

            # run an explain if first seen
            if first_seen:
                cur.execute(
                    """
                    SELECT dt, statement, hostname, canonicalized_statement,
                        canonicalized_statement_hash,
                        canonicalized_statement_hostname_hash
                    FROM statementdata
                    WHERE sequence_id=?
                    """, (sequence_id, ))
                statement_data_row = list(cur.fetchone())
                statement_data_row.append(DataManager.get_last_db_used())

                try:
                    mysql_conn = MySQLdb.connect(
                        **DataManager.get_explain_connection_options())
                    with mysql_conn:
                        mysql_cur = mysql_conn.cursor()

                        cur.execute(
                            """
                            INSERT INTO explainedstatement(
                                dt, statement, hostname,
                                canonicalized_statement,
                                canonicalized_statement_hash,
                                canonicalized_statement_hostname_hash,
                                db)
                            VALUES (?,?,?,?,?,?,?)
                            """, statement_data_row)
                        explained_statement_id = cur.lastrowid

                        try:
                            explain_rows = DataManager.run_explain(
                                statement, mysql_cur)
                            for explain_row in explain_rows:
                                values = (
                                    explained_statement_id,
                                    explain_row['select_id'],
                                    explain_row['select_type'],
                                    explain_row['table'],
                                    explain_row['type'],
                                    explain_row['possible_keys'],
                                    explain_row['key'],
                                    explain_row['key_len'],
                                    explain_row['ref'],
                                    explain_row['rows'],
                                    explain_row['extra'])
                                cur.execute(
                                    """
                                    INSERT INTO explainresult(
                                        explained_statement_id,
                                        select_id,
                                        select_type,
                                        `table`,
                                        type,
                                        possible_keys,
                                        key,
                                        key_len,
                                        ref,
                                        rows,
                                        extra)
                                    VALUES
                                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, values)

                        except Exception, e:
                            print 'ERROR: {0}'.format(e)

                        mysql_cur.close()
                except Exception, e:
                    print 'ERROR: {0}'.format(e)

            cur.close()


class ServerData:
    """Encapsulates server submissions."""

    @staticmethod
    def save_statement_data(
            statement, hostname,
            canonicalized_statement, canonicalized_statement_hash,
            canonicalized_statement_hostname_hash,
            header_data):
        params = dict(
            statement=statement,
            hostname=hostname,
            canonicalized_statement=canonicalized_statement,
            canonicalized_statement_hash=canonicalized_statement_hash,
            canonicalized_statement_hostname_hash=
                canonicalized_statement_hostname_hash
        )
        header_data_keys = (
            'query_time', 'lock_time', 'rows_sent', 'rows_examined',
            'rows_affected', 'rows_read', 'bytes_sent',
            'tmp_tables', 'tmp_disk_tables', 'tmp_table_sizes')
        for k in header_data_keys:
            if k in header_data:
                params[k] = header_data[k]

        urlencoded_params = urllib.urlencode(params)
        try:
            response = url_request(
                ARGS.server_base_url + ARGS.save_statement_data_path,
                data=urlencoded_params)
            return response
        except Exception, e:
            return None

    @staticmethod
    def save_explained_statement(
            statement_data_id, explain_rows, db=None):
        params = dict(
            statement_data_id=statement_data_id,
            explain_rows=json.dumps(explain_rows),
        )
        if db:
            params['db'] = db
        urlencoded_params = urllib.urlencode(params)
        try:
            response = url_request(
                ARGS.server_base_url + ARGS.save_explained_statement_path,
                data=urlencoded_params)
            return response
        except Exception, e:
            return None

    @staticmethod
    def process_explain_requests(save_statement_data_response_content):
        response = json.loads(save_statement_data_response_content)
        explain_items = response.get('explain', [])
        if explain_items:
            conn = MySQLdb.connect(
                **DataManager.get_explain_connection_options())
            with conn:
                cur = conn.cursor()
                for explain_item in explain_items:
                    statement = explain_item['statement']
                    statement_data_id = explain_item['statement_data_id']

                    try:
                        explain_rows = DataManager.run_explain(
                            statement, cur)

                        ServerData.save_explained_statement(
                            statement_data_id,
                            explain_rows,
                            DataManager._last_db_used)

                    except Exception, e:
                        print ((
                            'ServerData.process_explain_requests() > '
                            'error while running EXPLAIN: {0}')
                            .format(e))


class DataManager:
    _last_db_used = None

    @staticmethod
    def set_last_db_used(last_db_used):
        DataManager._last_db_used = last_db_used

    @staticmethod
    def get_last_db_used():
        return DataManager._last_db_used

    @staticmethod
    def save_data(log_item_parser):
        results = canonicalize_statement(log_item_parser.statement)
        for (statement, normalized_statement, canonicalized_statement,
             __) in results:
            if normalized_statement.lower().startswith('use '):
                DataManager.set_last_db_used(
                    normalized_statement[4:].strip('; '))

            DataManager.save_statement_data(
                log_item_parser.dt,
                statement,
                HOSTNAME,
                canonicalized_statement,
                mmh3.hash(canonicalized_statement),
                mmh3.hash(
                    '{0}{1}'.format(canonicalized_statement, HOSTNAME)),
                log_item_parser.header_data)


    @staticmethod
    def save_statement_data(
        dt, statement, hostname,
        canonicalized_statement, canonicalized_statement_hash,
        canonicalized_statement_hostname_hash,
        header_data):

        if ARGS.stand_alone:
            LocalData.save_statement_data(
                dt, statement, hostname,
                canonicalized_statement, canonicalized_statement_hash,
                canonicalized_statement_hostname_hash,
                header_data)
        else:
            response = ServerData.save_statement_data(
                statement, hostname,
                canonicalized_statement, canonicalized_statement_hash,
                canonicalized_statement_hostname_hash,
                header_data)
            if response:
                try:
                    ServerData.process_explain_requests(response.content)
                except Exception, e:
                    print 'ERROR: {0}'.format(e)

    @staticmethod
    def get_explain_connection_options():
        connection_options = {}
        if 'h' in EXPLAIN_OPTIONS:
            connection_options['host'] = EXPLAIN_OPTIONS['h']
        if 'u' in EXPLAIN_OPTIONS:
            connection_options['user'] = EXPLAIN_OPTIONS['u']
        if 'p' in EXPLAIN_OPTIONS and EXPLAIN_OPTIONS['p']:
            connection_options['passwd'] = EXPLAIN_OPTIONS['p']
        if 'd' in EXPLAIN_OPTIONS:
            connection_options['db'] = EXPLAIN_OPTIONS['d']
        elif DataManager._last_db_used:
            connection_options['db'] = DataManager._last_db_used
        return connection_options

    @staticmethod
    def run_explain(statement, cursor):
        sql = 'EXPLAIN {0}'.format(statement)
        print 'Running:', sql
        cursor.execute(sql)
        fetched_rows = cursor.fetchall()
        explain_rows = []
        columns = [
            'select_id',
            'select_type',
            'table',
            'type',
            'possible_keys',
            'key',
            'key_len',
            'ref',
            'rows',
            'extra']
        for fetched_row in fetched_rows:
            explain_rows.append(dict(zip(columns, fetched_row)))
        return explain_rows


class GeneralQueryLogItemParser(object):
    """General query log item parser."""

    QUERY_LOG_PATTERN_FULL_QUERY = (
        r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+(?P<query>.+(\n.+)*?)'
        r'(?=((\d+\s\d+:\d+:\d+\s+)|(\s+\d+\s)|(\s*$)))')

    def __init__(self):
        super(GeneralQueryLogItemParser, self).__init__()

        self.dt = None
        self.query_time = None
        self.lock_time = None
        self.rows_sent = None
        self.rows_examined = None
        self.statement = None

        self._full_query_pattern = re.compile(
            GeneralQueryLogItemParser.QUERY_LOG_PATTERN_FULL_QUERY)

    def parse_statement(self, lines_to_parse):
        # search for query embedded in lines
        match = self._full_query_pattern.match(lines_to_parse)
        if match:
            self.statement = match.group('query')
        else:
            self.statement = None
        return self.statement


class GeneralQueryLogProcessor(object):
    """Encapsulates operations on MySQL general query log."""

    QUERY_LOG_PATTERN_QUERY_START = (
        r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+')

    def __init__(self):
        super(GeneralQueryLogProcessor, self).__init__()
        self._query_start_pattern = re.compile(
            GeneralQueryLogProcessor.QUERY_LOG_PATTERN_QUERY_START)

    def process_log_contents(self, source):
        """Process contents of MySQL general query log."""
        line = ''
        lines_to_parse = ''
        parse_now = False
        exit_loop = False

        while True:
            try:
                if parse_now:
                    log_item_parser = GeneralQueryLogItemParser()
                    if log_item_parser.parse_statement(lines_to_parse):
                        print log_item_parser.statement
                        DataManager.save_data(log_item_parser)
                        lines_to_parse = ''
                    else:
                        # could not parse current line(s)
                        pass

                    lines_to_parse = line if line else ''
                    if lines_to_parse:
                        # check if we can parse the recent line
                        if log_item_parser.parse_statement(lines_to_parse):
                            print log_item_parser.statement
                            DataManager.save_data(log_item_parser)
                            lines_to_parse = ''

                    parse_now = False

                    if exit_loop:
                        break

                line = source.readline()
                if not line:
                    # end of file, parse lines not yet parsed if present
                    # before exiting loop
                    if lines_to_parse:
                        parse_now = True
                        exit_loop = True
                        continue
                    break
                else:
                    # check if this line has the start of a query
                    match = self._query_start_pattern.match(line)
                    if match:
                        # found match, do we have lines that were not
                        # yet parsed?
                        # if yes, parse them now,
                        # then set lines_to_parse = line
                        parse_now = True
                        continue
                    else:
                        lines_to_parse += line
            except (KeyboardInterrupt, SystemExit):
                if lines_to_parse:
                    parse_now = True
                    exit_loop = True
                    continue
                break


def print_top_queries(n):
    """Prints top N queries."""
    conn = sqlite3.connect(LocalData.DB)
    with conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                canonicalized_statement,
                hostname,
                canonicalized_statement_hostname_hash,
                COUNT(id)
            FROM statementdata
            GROUP BY
                canonicalized_statement,
                hostname,
                canonicalized_statement_hostname_hash
            ORDER BY COUNT(id) DESC
            LIMIT ?
            """, (n,))
        rows = cur.fetchall()

        print 'Top {0} Queries:'.format(n)
        for row in rows:
            print '{0} | {1} | {2}'.format(
                int_to_hex_str(row[2]), str(row[3]).rjust(4), row[0])


def local_run_last_statements(window_length):
    """Shows a sliding window of last statements seen."""

    conn = sqlite3.connect(LocalData.DB)
    with conn:
        cur = conn.cursor()
        while True:
            try:
                dt = datetime.datetime.now()
                dt_start = dt - datetime.timedelta(minutes=window_length)
                cur.execute(
                    """
                    SELECT
                        canonicalized_statement,
                        hostname,
                        canonicalized_statement_hostname_hash,
                        canonicalized_statement_hash,
                        statement,
                        MAX(dt),
                        COUNT(dt)
                    FROM statementdata
                    WHERE (dt>=?) AND (dt<=?)
                    GROUP BY
                        canonicalized_statement,
                        hostname,
                        canonicalized_statement_hostname_hash,
                        canonicalized_statement_hash,
                        statement
                    ORDER BY MAX(dt)
                    """, (dt_start, dt))

                rows = cur.fetchall()
                row_count = len(rows)

                # calculate counts
                counts = {}
                for row in rows:
                    canonicalized_statement_hostname_hash = row[2]
                    if canonicalized_statement_hostname_hash in counts:
                        counts[canonicalized_statement_hostname_hash] += (
                            row[6])
                    else:
                        counts[canonicalized_statement_hostname_hash] = (
                            row[6])

                statements = []
                print (
                    'Statements found in the last {0} minute(s): '
                    '{1} statement(s)').format(
                    window_length, row_count)
                for row in rows:
                    canonicalized_statement_hostname_hash = row[2]
                    count = counts[canonicalized_statement_hostname_hash]
                    print '{0} | {1} | {2} | {3} '.format(
                        row[5], int_to_hex_str(row[2]), str(count).rjust(4),
                        row[4])
                print
                print

                time.sleep(1)

            except (KeyboardInterrupt, SystemExit):
                break
        cur.close()



def main():
    default_db = '%s/sqlcanonclient.db' % tempfile.gettempdir()

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'file', nargs='?',
        help='MySQL log file to open, if not specified stdin will be used.')
    parser.add_argument(
        '-t', '--type', choices='sg',
        help='Log file format -- s: slow query log, g: general query log',
        default='s',)

    parser.add_argument(
        '-d', '--db', help='database name', default=default_db)

    parser.add_argument(
        '-s', '--stand-alone',
        action='store_true',
        help='Run as stand alone (will not send data to server).')
    parser.add_argument(
        '--server-base-url',
        help='Server base URL.',
        default='http://localhost:8000')
    parser.add_argument(
        '--save-statement-data-path',
        help='URL to be used for saving statement data.',
        default='/save-statement-data/',)
    parser.add_argument(
        '--save-explained-statement-path',
        help='URL to be used for saving explain statement.',
        default='/save-explained-statement/',)
    parser.add_argument(
        '-e', '--explain-options',
        help='Explain MySQL options: h=<host>,u=<user>,p=<passwd>,d=<db>',
        default='h=127.0.0.1,u=root')

    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        '-l', '--sniff',
        action='store_true', default=False,
        help='launch packet sniffer')
    action.add_argument(
        '--local-run-last-statements', action='store_true',
        help='In stand alone mode, prints last seen statements')
    action.add_argument(
        '--print-top-queries',
        help='Prints top queries stored on local data.',
        default=0)

    # local-run-last-statements options
    parser.add_argument(
        '--sliding-window-length', type=int,
        help='Length of period in number of minutes.',
        default=5)

    # packet sniffer options
    parser.add_argument(
        '-i', '--interface',
        help='interface to sniff from', default='lo0')
    parser.add_argument(
        '-f', '--filter', help='pcap-filter', default='dst port 3306',)

    global ARGS
    ARGS = parser.parse_args()

    if ARGS.local_run_last_statements and not ARGS.stand_alone:
        print 'Stand alone required.'
        sys.exit()

    if ARGS.print_top_queries and not ARGS.stand_alone:
        print 'Stand alone required.'
        sys.exit()

    if ARGS.stand_alone:
        LocalData.init_db(ARGS.db)

    DataManager.set_last_db_used(None)

    # parse explain options
    global EXPLAIN_OPTIONS
    if ARGS.explain_options:
        EXPLAIN_OPTIONS = dict(
            [(i[0].strip(), i[2].strip())
                for i in [word.partition('=')
                    for word in ARGS.explain_options.split(',')]])
    if 'p' in EXPLAIN_OPTIONS and not EXPLAIN_OPTIONS['p']:
        EXPLAIN_OPTIONS['p'] = getpass.getpass(
            'Enter MySQL password for EXPLAIN operations:')
    else:
        EXPLAIN_OPTIONS['p'] = None

    is_file_slow_query_log = (ARGS.type == 's')
    is_file_general_query_log = (ARGS.type == 'g')

    try:
        if ARGS.sniff:
            run_packet_sniffer()
            sys.exit()

        if ARGS.local_run_last_statements:
            local_run_last_statements(ARGS.sliding_window_length)
            sys.exit()

        if ARGS.print_top_queries:
            print_top_queries(ARGS.print_top_queries)
            sys.exit()

        if is_file_slow_query_log and ARGS.file:
            print (
                'MySQL slow query log file = {0}'
                .format(ARGS.file))
            slow_query_log_processor = SlowQueryLogProcessor()
            with open(ARGS.file) as f:
                slow_query_log_processor.process_log_contents(f)

        elif is_file_slow_query_log and not ARGS.file:
            print 'Reading MySQL slow query log from stdin...'
            query_log_processor = SlowQueryLogProcessor()
            query_log_processor.process_log_contents(stdin)

        elif is_file_general_query_log and ARGS.file:
            print (
                'MySQL general query log file = {0}'
                .format(ARGS.file))
            query_log_processor = GeneralQueryLogProcessor()
            with open(ARGS.file) as f:
                query_log_processor.process_log_contents(f)

        elif is_file_general_query_log and not ARGS.file :
            print 'Reading MySQL general query log from stdin...'
            query_log_processor = GeneralQueryLogProcessor()
            query_log_processor.process_log_contents(stdin)

    except Exception, e:
        print 'An error has occurred: {0}'.format(e)
        traceback.print_exc()


if __name__ == '__main__':
    main()
