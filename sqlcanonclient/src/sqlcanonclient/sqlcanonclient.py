#!/usr/bin/env python

import argparse
from datetime import datetime, timedelta
import pprint
import os
import re
import string
import sys
from sys import stdin
import time
import urllib
import urllib2

from construct.protocols.ipstack import ip_stack
import pcap
import mmh3
import sqlite3
import sqlparse
from sqlparse.tokens import Token

PP = pprint.PrettyPrinter(indent=4)

PROCESS_CAPTURED_STATEMENT_URL = 'http://localhost:8000/canonicalizer/process_captured_statement/'

STATEMENT_UNKNOWN = 'UNKNOWN'

QUERY_LOG_PATTERN_QUERY_START = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+'

QUERY_LOG_PATTERN_FULL_QUERY = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+(?P<query>.+(\n.+)*?)(?=((\d+\s\d+:\d+:\d+\s+)|(\s+\d+\s)|(\s*$)))'

# collapse target parts (for now target parts are in and values)
COLLAPSE_TARGET_PARTS = True

DB = './sqlcanon.db'

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
            dt = datetime.now()

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
                ('{0}'.format(stmt), None, None, [])
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

def process_log_file(log_file):
    """
    Processes contents of log file (mysql general log file format).
    """
    f = open(log_file)
    try:
        process_query_log(f)
    except Exception, e:
        raise
    finally:
        f.close()

def db_increment_canonicalized_query_count_from_results(results):
    """
    Increment db counts with data from results..
    """

    for result in results:
        query, _, canonicalized_query, _ = result
        print 'Query: {0}'.format(query)
        db_increment_canonicalized_statement_count(canonicalized_query)

def process_query_log(source,
                      canonicalize_sql_results_processor=db_increment_canonicalized_query_count_from_results):
    """
    Processes queries from source.

    source
        either file or stdin
    """

    try:
        line = ''
        lines_to_parse = ''
        parse_now = False
        exit_loop = False

        while True:
            try:
                if parse_now:
                    # search for query embedded in lines
                    pat = QUERY_LOG_PATTERN_FULL_QUERY
                    match = re.search(pat, lines_to_parse)
                    if match:
                        query = match.group('query')
                        canonicalize_sql_results = canonicalize_statement(query)
                        canonicalize_sql_results_processor(
                            canonicalize_sql_results)
                        lines_to_parse = ''
                    else:
                        #print 'Could not parse the following: {0}'.format(lines_to_parse)
                        pass

                    lines_to_parse = line if line else ''
                    if lines_to_parse:
                        # check if we can parse the recent line
                        match = re.search(pat, lines_to_parse)
                        if match:
                            query = match.group('query')
                            canonicalize_sql_results = canonicalize_statement(query)
                            canonicalize_sql_results_processor(
                                canonicalize_sql_results)
                            lines_to_parse = ''

                    parse_now = False

                    if exit_loop:
                        break

                line = source.readline()
                if not line:
                    # end of file, parse lines not yet parsed if present before exiting loop
                    if lines_to_parse:
                        parse_now = True
                        exit_loop = True
                        continue
                    break
                else:
                    # check if this line has the start of a query
                    pat = QUERY_LOG_PATTERN_QUERY_START
                    match = re.search(pat, line)
                    if match:
                        # found match, do we have lines that were not yet parsed?
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
    except Exception, e:
        print 'Exception in process_query_log: {0}'.format(e)
        raise

def process_query_log_from_stdin(
        canonicalize_sql_results_processor=db_increment_canonicalized_query_count_from_results):
    """
    Processes queries coming from stdin.
    """

    process_query_log(stdin)

QUERY_LISTER = QueryLister()

def append_statements_to_query_lister(results):
    """
    Append statements from canonicalize sql results to QUERY_LISTER.
    This method increments db counts too.
    """

    for result in results:
        statement, _, canonicalized_statement, _ = result
        canonicalized_statement = canonicalized_statement if canonicalized_statement else STATEMENT_UNKNOWN
        db_increment_canonicalized_statement_count(canonicalized_statement)
        QUERY_LISTER.append_statement(statement=statement,
            canonicalized_statement=canonicalized_statement)

def print_statements(listen_window_length):
    dt_now = datetime.now()
    result = QUERY_LISTER.get_list(
        dt_now - timedelta(minutes=listen_window_length),
        dt_now)
    print
    print '#### Queries found in the last {0} minutes:'.format(listen_window_length)
    if result:
        for dt, statement, canonicalized_statement, hash, count in result:
            print\
            dt.strftime('%Y-%m-%d %H:%M:%S %f'),\
            '[count:{0}{1}]'.format(count, '-unknown' if canonicalized_statement == STATEMENT_UNKNOWN else ''),\
            '[hash:{0}]'.format(int_to_hex_str(hash)),\
            statement
    else:
        print '(None)'

def query_log_listen(log_file, listen_frequency, listen_window_length,
                     canonicalize_sql_results_processor=append_statements_to_query_lister):
    """
    Listens for incoming queries from a mysql query log file display stats.
    """

    file = open(log_file)

    # Find the size of the file and move to the end
    st_results = os.stat(log_file)
    st_size = st_results[6]
    file.seek(st_size)

    try:
        line = ''
        lines_to_parse = ''
        parse_now = False
        exit_loop = False

        while True:
            try:
                if parse_now:
                    # search for query embedded in lines
                    pat = QUERY_LOG_PATTERN_FULL_QUERY
                    match = re.search(pat, lines_to_parse)
                    if match:
                        query = match.group('query')
                        canonicalize_sql_results = canonicalize_statement(query)
                        canonicalize_sql_results_processor(
                            canonicalize_sql_results)
                        lines_to_parse = ''
                    else:
                        #print 'Could not parse the following: {0}'.format(lines_to_parse)
                        pass

                    lines_to_parse = line if line else ''
                    if lines_to_parse:
                        # check if we can parse the recent line
                        match = re.search(pat, lines_to_parse)
                        if match:
                            query = match.group('query')
                            canonicalize_sql_results = canonicalize_statement(query)
                            canonicalize_sql_results_processor(
                                canonicalize_sql_results)
                            lines_to_parse = ''

                    parse_now = False

                    if exit_loop:
                        break

                where = file.tell()
                line = file.readline()
                if not line:
                    print_statements(listen_window_length)
                    time.sleep(listen_frequency)
                    file.seek(where)
                else:
                    # check if this line has the start of a query
                    pat = QUERY_LOG_PATTERN_QUERY_START
                    match = re.search(pat, line)
                    if match:
                        # found match, do we have lines that were not yet parsed?
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
    except Exception, e:
        print 'Exception in query_log_listen: {0}'.format(e)
        raise
    finally:
        file.close()

def db_increment_canonicalized_statement_count(canonicalized_statement,
                                               canonicalized_statement_hash=None,
                                               count=1):
    """
    Increments count on database.
    """

    if not canonicalized_statement:
        canonicalized_statement = STATEMENT_UNKNOWN
        # recompute canonicalized_statement_hash
        canonicalized_statement_hash = mmh3.hash(canonicalized_statement)

    if not canonicalized_statement_hash:
        canonicalized_statement_hash = mmh3.hash(canonicalized_statement)

    conn = sqlite3.connect(DB)
    with conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT instances FROM canonicalizedstatement WHERE hash = ?
            """, (canonicalized_statement_hash,))
        row = cur.fetchone()
        if row:
            count = row[0] + count
            cur.execute("""
                UPDATE canonicalizedstatement
                SET
                    instances = ?
                WHERE hash = ?
                """, (count, canonicalized_statement_hash))
        else:
            cur.execute("""
                INSERT INTO canonicalizedstatement(statement, hash, instances)
                VALUES(?, ?, ?)
                """, (canonicalized_statement, canonicalized_statement_hash, count))

    #try:
    #    info = CanonicalizedStatement.objects.get(
    #        hash=canonicalized_statement_hash)
    #    info.instances += count
    #    info.save()
    #except ObjectDoesNotExist:
    #    CanonicalizedStatement.objects.create(
    #        statement=canonicalized_statement,
    #        hash=canonicalized_statement_hash,
    #        instances=count)

def print_db_counts():
    """
    Prints counts stored on database.
    """

    print
    print 'Counts stored in database:'
    print '=' * 80

    item_count = 0

    conn = sqlite3.connect(DB)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT statement, hash, instances FROM canonicalizedstatement")
        while True:
            row = cur.fetchone()
            if not row:
                break
            item_count += 1
            #print '{0}. {1} => {2}'.format(item_count, row[1], row[0])
            print '{0}. [count={1}] [hash={2}] {3}'.format(
                item_count,
                row[2],
                int_to_hex_str(row[1]),
                row[0]
            )

    #statements = CanonicalizedStatement.objects.all()
    #for statement in statements:
    #    item_count += 1
    #    print '{0}. [count={1}] [hash={2}] {3}'.format(
    #        item_count,
    #        statement.instances,
    #        int_to_hex_str(statement.hash),
    #        statement.statement
    #    )

def init_db():
    """
    Creates canonicalizedstatement table if it does not exist yet.
    """

    conn = sqlite3.connect(DB)
    with conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS canonicalizedstatement(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                statement TEXT NOT NULL UNIQUE,
                hash INT NOT NULL UNIQUE,
                instances INT NOT NULL)
            """
        )



def process_packet(pktlen, data, timestamp):
    if not data:
        return

    print 'pktlen:', pktlen, 'dt:', datetime.fromtimestamp(timestamp)
    stack = ip_stack.parse(data)
    payload = stack.next.next.next
    print payload

    # MySQL queries start on the 6th char (?)
    payload = payload[5:]

    params = dict(statement=payload)
    params = urllib.urlencode(params)
    print params
    try:
        handler = urllib2.urlopen(PROCESS_CAPTURED_STATEMENT_URL, params)
        print 'handler.code:', handler.code
    except Exception, e:
        print 'Exception: {0}'.format(e)

def run_packet_sniffer(args):
    if not args.interface:
        print '--interface was not specified.'
        sys.exit()

    print 'Sending captured statements to: {0}'.format(PROCESS_CAPTURED_STATEMENT_URL)

    #if len(sys.argv) < 3:
    #    print 'usage: {0} <interface> <expr>'.format(sys.argv[0])
    #    sys.exit()

    p = pcap.pcapObject()
    #dev = sys.argv[1]
    dev = args.interface
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
    #p.setfilter(string.join(sys.argv[2:], ' '), 0, 0)
    p.setfilter(args.filter, 0, 0)

    print 'Press CTRL+C to end capture'
    try:
        while True:
            p.dispatch(1, process_packet)
    except KeyboardInterrupt:
        print # Empty line where ^C from CTRL+C is displayed
        print '%s' % sys.exc_type
        print 'shutting down'
        print '%d packets received, %d packets dropped, %d packets dropped by interface' % p.stats()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--db', help='database name (default: ./sqlcanon.db)')
    parser.add_argument('--print-db-counts', action='store_true', help='Prints counts stored in DB at the end of execution.')
    parser.add_argument('--log-file', help='Mysql query log file to process.')

    action = parser.add_mutually_exclusive_group()
    action.add_argument('--sniff', action='store_true', default=False, help='launch packet sniffer')
    action.add_argument('--listen', action='store_true', help='Opens up log file and waits for newly written data.')

    parser.add_argument('--interface', help='interface to sniff from')
    parser.add_argument('--filter', default='dst port 3306', help='pcap-filter')
    parser.add_argument(
        '--capture-url',
        help='URL of captured statement processor (default: http://localhost:8000/canonicalizer/process_captured_statement/)',
    )

    parser.add_argument('--listen-window-length', default=5, type=int, help='Length of period of query list filter in number of minutes. (default: 5)')



    args = parser.parse_args()

    if args.db:
        DB = args.db
    init_db()

    if args.capture_url:
        PROCESS_CAPTURED_STATEMENT_URL = args.capture_url

    try:
        if args.sniff:
            run_packet_sniffer(args)
            sys.exit()

        log_file = args.log_file
        listen = args.listen
        listen_window_length = args.listen_window_length

        if log_file and listen:
            print 'Listening for new data in {0} (window_length={1})...'.format(
                log_file, listen_window_length
            )
            query_log_listen(log_file=log_file, listen_frequency=1,
                listen_window_length=listen_window_length)
        elif log_file:
            print 'Processing contents from log file {0}...'.format(log_file)
            process_log_file(log_file)
        else:
            # read from pipe
            print 'Processing data from stdin...'
            process_query_log_from_stdin()

        if args.print_db_counts:
            print_db_counts()

    except Exception, e:
        print 'An error has occurred: {0}'.format(e)
