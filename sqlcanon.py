#!/usr/bin/env python
import re
import sqlparse
from sqlparse.tokens import Token

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
    for child_token in token.tokens:
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
    print 'canonicalizer_function'
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

    print 'token.ttype = {0}'.format(token.ttype)
    print 'type(token) = {0}'.format(type(token))
    print 'token.normalized = <{0}>'.format(token.normalized)
    print 'child tokens: {0}'.format(token.tokens if token.is_group() else None)

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

def canonicalize_sql(sql):
    """
    Canonicalizes sql statement(s).

    Returns a list of (orig sql, canonicalized sql, parameterized sql, values for parameterized sql)
    """
    result = []

    parsed = sqlparse.parse(sql)

    for stmt in parsed:
        print 'stmt => {0} <='.format(stmt)
        print 'stmt.tokens => {0}'.format(stmt.tokens)
        if stmt.get_type() == 'UNKNOWN':
            print 'UNKNOWN: => {0} <='.format(stmt)
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

def process_mysql_log_file(mysql_log_file):
    """
    Processes contents of log file (mysql general log file format).
    """

    counts = {}
    f = open(mysql_log_file)
    try:
        line = ''
        lines_to_parse = ''
        parse_now = False
        exit_loop = False
        query_count = 0
        while True:
            if parse_now:
                # search for query embedded in lines
                pat = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+(?P<query>.+(\n.+)*?)(?=((\d+\s\d+:\d+:\d+\s+)|(\s+\d+\s)|(\s*$)))'
                match = re.search(pat, lines_to_parse)
                if match:
                    print 'lines_to_parse => {0}'.format(lines_to_parse)
                    query = match.group('query')
                    print 'query => {0}'.format(query)
                    query_count += 1
                    print '{0}. {1}'.format(query_count, query)
                    ret = canonicalize_sql(query)
                    for data in ret:
                        if data[2]:
                            parameterized_sql = data[2]
                        else:
                            parameterized_sql = 'UNKNOWN'
                        if counts.has_key(parameterized_sql):
                            counts[parameterized_sql] += 1
                        else:
                            counts[parameterized_sql] = 1
                parse_now = False
                lines_to_parse = line if line else ''
                if exit_loop:
                    break
            line = f.readline()
            if not line:
                # end of file, parse lines not yet parsed if present before exiting loop
                if lines_to_parse:
                    parse_now = True
                    exit_loop = True
                    continue
                break
            else:
                # check this line has the start of a query
                pat = r'((\d+\s\d+:\d+:\d+\s+)|(\s+))\d+\sQuery\s+'
                match = re.search(pat, line)
                if match:
                    # found match, do we have unparsed lines?
                    # if yes, parse them now,
                    # then set lines_to_parse = line
                    parse_now = True
                    continue
                else:
                    lines_to_parse += line
    except Exception, e:
        print 'An error has occurred: {0}'.format(e)
    f.close()
    return counts

def process_sql_file(sql_file):
    """
    Processes contents of an sql file.
    One sql statement per line is assumged.
    """

    counts = {}
    f = open(sql_file)
    try:
        line_count = 0
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            line_count += 1
            print '{0}. {1}'.format(line_count, line)
            ret = canonicalize_sql(line)
            for data in ret:
                if data[2]:
                    parameterized_sql = data[2]
                else:
                    parameterized_sql = 'UNKNOWN'
                if counts.has_key(parameterized_sql):
                    counts[parameterized_sql] += 1
                else:
                    counts[parameterized_sql] = 1
    except Exception, e:
        print 'An error has occurred: {0}'.format(e)
    f.close()
    return counts

if __name__ == '__main__':
    import argparse

    print '#### sqlcanon: start ####\n'

    parser = argparse.ArgumentParser()
    parser.add_argument('--sql_file', help='process sql statements contained in an sql file (one statement per line)')
    parser.add_argument('--mysql_log_file', help='process queries from a mysql log file (mysql general log file format)')
    args = parser.parse_args()

    parameterized_sql_counts = {}

    show_results = False

    if args.sql_file:
        # contents of sql file will be one sql statement per line

        try:
            parameterized_sql_counts = process_sql_file(args.sql_file)
            show_results = True
        except Exception, e:
            print 'An error has occurred: {0}'.format(e)

    if args.mysql_log_file:

        try:
            parameterized_sql_counts = process_mysql_log_file(args.mysql_log_file)
            show_results = True
        except Exception, e:
            print 'An error has occurred: {0}'.format(e)

    if show_results:
        print
        print 'stats:'
        print '=' * 80
        item_count = 0
        for k, v in parameterized_sql_counts.iteritems():
            item_count += 1
            print '{0}. {1} - {2}'.format(item_count, v, k)
