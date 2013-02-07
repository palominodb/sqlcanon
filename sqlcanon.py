#!/usr/bin/env python

from datetime import datetime, timedelta
import os
import re
from sys import stdin
import time

import sqlite3
import sqlparse
from sqlparse.tokens import Token

from query_lister import QueryLister

QUERY_LOG_PATTERN_QUERY_START = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+'

QUERY_LOG_PATTERN_FULL_QUERY = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+(?P<query>.+(\n.+)*?)(?=((\d+\s\d+:\d+:\d+\s+)|(\s+\d+\s)|(\s*$)))'

# collapse target parts (for now target parts are in and values)
COLLAPSE_TARGET_PARTS = True

# settings
SETTINGS = {}

def canonicalizer_default(token):
    """
    Default canonicalizer.

    Returns data in this format (normalized sql, paramtererized sql, values)
    """
    return (token.normalized, token.normalized, [])

def canonicalizer_whitespace(token):
    """
    Reduces whitespaces into a single space.

    Returns data in this format (normalized sql, paramtererized sql, values)
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
    parameterized = '%d'
    values = [int(token.value)]
    return (normalized, parameterized, values)

def canonicalizer_number_float(token):
    """
    Canonicalizes float numbers.
    """

    normalized = token.normalized
    parameterized = '%f'
    values = [float(token.value)]
    return (normalized, parameterized, values)

def canonicalizer_string_single(token):
    """
    Canonicalizes strings with single quotes.
    """

    normalized = token.normalized
    parameterized = '%s'
    values = [token.value.strip("'").replace(r"\'", "'")]
    return (normalized, parameterized, values)

def canonicalizer_string_symbol(token):
    """
    Canonicalizes strings with quotes (double).

    Turns enclosing double quotes to single quotes.
    Replaces content: \" to "
    """

    normalized = r"""'{0}'""".format(token.normalized.strip('"').replace(r'\"', '"'))
    parameterized = '%s'
    values = [token.value.strip('"').replace(r'\"', '"')]
    return (normalized, parameterized, values)

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
    parameterized = ''
    values = []

    for child_token in token.tokens:
        if child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
            child_token_index = token.token_index(child_token)
            next_child_token = token.token_next(child_token_index, skip_ws=False)
            prev_child_token = token.token_prev(child_token_index, skip_ws=False)
            if ((prev_child_token and prev_child_token.ttype in (Token.Keyword,)) or
                (next_child_token and next_child_token.ttype in (Token.Keyword,))):
                # maintain a single space if previous or next token is a keyword
                c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
            else:
                c_normalized, c_parameterized, c_values = ('', '', [])
        else:
            c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        parameterized += c_parameterized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, parameterized, values)

def canonicalizer_where(token):
    """
    Canonicalizes where clause.

    Consecutive whitespaces are reduced to one.
    """

    assert token.is_group()

    normalized = ''
    parameterized = ''
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
                c_normalized, c_parameterized, c_values = ('', '', [])
        elif COLLAPSE_TARGET_PARTS and child_token.ttype in (Token.Keyword,):
            if child_token.normalized == 'IN':
                found_in_keyword = True
            else:
                if found_in_keyword:
                    found_new_keyword_after_in_keyword = True
            c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
        elif COLLAPSE_TARGET_PARTS and child_token.is_group() and \
            type(child_token) is sqlparse.sql.Parenthesis and \
            found_in_keyword and not found_new_keyword_after_in_keyword:
            c_normalized, c_parameterized, c_values = ('(N)', '(N)', [])
        else:
            c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        parameterized += c_parameterized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, parameterized, values)

def canonicalizer_identifier_list(token):
    """
    Canonicalizes IdentifierList token.

    Whitespaces are canonicalized to empty string.
    """

    assert token.is_group()

    normalized = ''
    parameterized = ''
    values = []

    for child_token in token.tokens:
        if child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
            c_normalized, c_parameterized, c_values = ('', '', [])
        else:
            c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        parameterized += c_parameterized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, parameterized, values)

def canonicalizer_comparison(token):
    """
    Canonicalizes Comparison token.

    Whitespaces are canonicalized to empty string.
    """

    assert token.is_group()

    normalized = ''
    parameterized = ''
    values = []

    for child_token in token.tokens:
        if child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
            c_normalized, c_parameterized, c_values = ('', '', [])
        else:
            c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        parameterized += c_parameterized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, parameterized, values)

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
    parameterized = ''
    values = []

    for child_token in token.tokens:
        if type(child_token) is sqlparse.sql.Identifier:
            name = child_token.normalized
            if name.upper() in SQL_FUNCTIONS:
                c_normalized, c_parameterized, c_values = (
                    name.upper(), name.upper(), [])
            else:
                c_normalized, c_parameterized, c_values = (name, name, [])
        elif child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
            c_normalized, c_parameterized, c_values = ('', '', [])
        else:
            c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
        normalized += c_normalized
        parameterized += c_parameterized
        for c_value in c_values:
            values.append(c_value)

    return (normalized, parameterized, values)

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
    parameterized = ''
    values = []
    if token.ttype and CANONICALIZERS.has_key(token.ttype):
        normalized, parameterized, values = CANONICALIZERS[token.ttype](token)
    elif token.is_group():
        if CANONICALIZERS_BY_CLASS_TYPE.has_key(type(token)):
            normalized, parameterized, values = CANONICALIZERS_BY_CLASS_TYPE[type(token)](token)
        else:
            for child_token in token.tokens:
                c_normalized, c_parameterized, c_values = canonicalize_token(child_token)
                normalized += c_normalized
                parameterized += c_parameterized
                for c_value in c_values:
                    values.append(c_value)
    else:
        # no assigned canonicalizer for token? use default
        normalized, parameterized, values = canonicalizer_default(token)

    return (normalized, parameterized, values)

def canonicalizer_statement_insert(stmt):
    """
    Canonicalizes insert statements.
    """

    assert stmt.get_type() == 'INSERT'

    normalized = ''
    parameterized = ''
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
            t_normalized, t_parameterized, t_values = ('', '', [])
        elif (type(token) is sqlparse.sql.Identifier) and prev_token.ttype in (Token.Operator,):
            t_normalized, t_parameterized, t_values = (token.normalized, token.normalized, [])
        elif COLLAPSE_TARGET_PARTS and token.ttype in (Token.Keyword,):
            if token.normalized == 'VALUES':
                found_values_keyword = True
                #print 'found VALUES keyword: {0}'.format(token.normalized)
            else:
                if found_values_keyword:
                    found_new_keyword_afer_values_keyword = True
            t_normalized, t_parameterized, t_values = canonicalize_token(token)
        elif COLLAPSE_TARGET_PARTS and token.is_group() and \
            type(token) is sqlparse.sql.Parenthesis and \
            found_values_keyword and not found_new_keyword_afer_values_keyword:

            if not first_parenthesis_after_values_keyword:
                first_parenthesis_after_values_keyword = token
            if first_parenthesis_after_values_keyword == token:
                t_normalized, t_parameterized, t_values = ('(N)', '(N)', [])
            else:
                t_normalized, t_parameterized, t_values = ('', '', [])
        elif COLLAPSE_TARGET_PARTS and token.ttype in (Token.Punctuation,) \
            and found_values_keyword and not found_new_keyword_afer_values_keyword:
            t_normalized, t_parameterized, t_values = ('', '', [])
        else:
            t_normalized, t_parameterized, t_values = canonicalize_token(token)
        normalized += t_normalized
        parameterized += t_parameterized
        for t_value in t_values:
            values.append(t_value)

    normalized = normalized.strip(' ;')
    parameterized = parameterized.strip(' ;')

    return (normalized, parameterized, values)

def canonicalize_sql(sql):
    """
    Canonicalizes sql statement(s).

    Returns a list of (orig sql, canonicalized sql, parameterized sql, values for parameterized sql)
    """
    result = []

    parsed = sqlparse.parse(sql)

    for stmt in parsed:
        #print 'stmt => {0} <='.format(stmt)
        #print 'stmt.tokens => {0}'.format(stmt.tokens)
        if stmt.get_type() == 'INSERT':
            #print 'stmt.get_type() => {0}'.format(stmt.get_type())
            stmt_normalized, stmt_parameterized, stmt_values = canonicalizer_statement_insert(stmt)
            result.append(('{0}'.format(stmt), stmt_normalized, stmt_parameterized, stmt_values))
            continue
        elif stmt.get_type() == 'UNKNOWN':
            #print 'UNKNOWN: => {0} <='.format(stmt)
            result.append(
                ('{0}'.format(stmt), None, None, [])
            )
            continue

        normalized = ''
        parameterized = ''
        values = []
        for token in stmt.tokens:
            token_index = stmt.token_index(token)
            next_token = stmt.token_next(token_index, skip_ws=False)
            prev_token = stmt.token_prev(token_index, skip_ws=False)
            if (token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline) and
                next_token and
                next_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline)):
                t_normalized, t_parameterized, t_values = ('', '', [])
            elif (type(token) is sqlparse.sql.Identifier) and prev_token.ttype in (Token.Operator,):
                t_normalized, t_parameterized, t_values = (token.normalized, token.normalized, [])
            else:
                t_normalized, t_parameterized, t_values = canonicalize_token(token)
            normalized += t_normalized
            parameterized += t_parameterized
            for t_value in t_values:
                values.append(t_value)

        normalized = normalized.strip(' ;')
        parameterized = parameterized.strip(' ;')

        result.append(
            ('{0}'.format(stmt), normalized, parameterized, values)
        )
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
        db_increment_canonicalized_query_count(
            canonicalized_query if canonicalized_query else 'UNKNOWN')

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
                        canonicalize_sql_results = canonicalize_sql(query)
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
                            canonicalize_sql_results = canonicalize_sql(query)
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

def append_queries_to_query_lister(results):
    """
    Append queries in canonicalize_sql_results to QUERY_LISTER.
    This method increments db counts too.
    """

    for result in results:
        query, _, canonicalized_query, _ = result
        db_increment_canonicalized_query_count(
            canonicalized_query if canonicalized_query else 'UNKNOWN')
        QUERY_LISTER.append_query(query=query,
            canonicalized_query=canonicalized_query)

def print_queries(listen_window_length):
    dt_now = datetime.now()
    result = QUERY_LISTER.get_list(
        dt_now - timedelta(minutes=listen_window_length),
        dt_now)
    print
    print '#### Queries found in the last {0} minutes:'.format(listen_window_length)
    if result:
        for dt, query, canonicalized_query, count in result:
            print dt.strftime('%Y-%m-%d %H:%M:%S %f'), '[{0}{1}]'.format(count, '' if canonicalized_query else '-unknown'), query
    else:
        print '(None)'

def query_log_listen(log_file, listen_frequency, listen_window_length,
                     canonicalize_sql_results_processor=append_queries_to_query_lister):
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
                        canonicalize_sql_results = canonicalize_sql(query)
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
                            canonicalize_sql_results = canonicalize_sql(query)
                            canonicalize_sql_results_processor(
                                canonicalize_sql_results)
                            lines_to_parse = ''

                    parse_now = False

                    if exit_loop:
                        break

                where = file.tell()
                line = file.readline()
                if not line:
                    print_queries(listen_window_length)
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

def db_increment_canonicalized_query_count(canonicalized_query, count=1):
    """
    Increments count on database.
    """

    conn = sqlite3.connect(SETTINGS['DB'])
    with conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS counts(id INTEGER PRIMARY KEY AUTOINCREMENT, statement TEXT UNIQUE, instances INT)")

        cur.execute("SELECT instances FROM counts WHERE statement = ?", (canonicalized_query,))
        row = cur.fetchone()
        if row:
            count = row[0] + count
            cur.execute("UPDATE counts SET instances = ? WHERE statement = ?", (count, canonicalized_query))
        else:
            cur.execute("INSERT INTO counts(statement, instances) VALUES(?, ?)", (canonicalized_query, count))

def print_db_counts():
    """
    Prints counts stored on database.
    """

    print
    print 'Counts stored in database:'
    print '=' * 80
    item_count = 0
    conn = sqlite3.connect(SETTINGS['DB'])
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT statement, instances FROM counts")
        while True:
            row = cur.fetchone()
            if not row:
                break
            item_count += 1
            print '{0}. {1} => {2}'.format(item_count, row[1], row[0])

def init_db():
    """
    Creates counts table if it does not exist yet.
    """

    conn = sqlite3.connect(SETTINGS['DB'])
    with conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS counts(id INTEGER PRIMARY KEY AUTOINCREMENT, statement TEXT UNIQUE, instances INT)")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='sqlcanon.db', help='The database to use. (default: sqlcannon.db)')
    parser.add_argument('--disable-collapsed-mode', action='store_true', help='Disable collapsed mode.')
    parser.add_argument('--listen', action='store_true', help='Opens up log file and waits for newly written data.')
    parser.add_argument('--listen-frequency', default=1, type=int, help='Listening frequency in number of seconds. (default: 1)')
    parser.add_argument('--listen-window-length', default=5, type=int, help='Length of period of query list filter in number of minutes. (default: 5)')
    parser.add_argument('--log-file', help='Mysql query log file to process.')
    parser.add_argument('--print-db-counts', action='store_true', help='Prints counts stored in DB at the end of execution.')

    args = parser.parse_args()

    if args.disable_collapsed_mode:
        COLLAPSE_TARGET_PARTS = False

    SETTINGS['DB'] = args.db
    init_db()

    if args.log_file and args.listen:
        print 'Listening for new data in {0} (frequency={1}, window_length={2})...'.format(
            args.log_file, args.listen_frequency, args.listen_window_length)
        query_log_listen(log_file=args.log_file,
            listen_frequency=args.listen_frequency,
            listen_window_length=args.listen_window_length)
    elif args.log_file:
        print 'Processing contents from log file {0}...'.format(args.log_file)
        process_log_file(args.log_file)
    else:
        # read from pipe
        print 'Processing data from stdin...'
        process_query_log_from_stdin()

    if args.print_db_counts:
        print_db_counts()
