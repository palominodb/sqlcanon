#!/usr/bin/env python
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
    values = [token.value.strip("'")]
    return (normalized, parameterized, values)

def canonicalizer_string_symbol(token):
    """
    Canonicalizes strings with quotes (double).
    """

    normalized = token.normalized
    parameterized = '%s'
    values = [token.value.strip('"')]
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

    #print 'token.ttype = {0}'.format(token.ttype)
    #print 'type(token) = {0}'.format(type(token))
    #print 'token.normalized = <{0}>'.format(token.normalized)
    #print 'child tokens:', token.tokens
    for child_token in token.tokens:
        #print 'child_token.ttype = {0}'.format(child_token.ttype)
        #print 'type(child_token) = {0}'.format(type(child_token))
        #print 'child_token.normalized = <{0}>'.format(child_token.normalized)
        #print 'child_token.is_group() = {0}'.format(child_token.is_group())
        if child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
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

    #print 'token.ttype = {0}'.format(token.ttype)
    #print 'type(token) = {0}'.format(type(token))
    #print 'token.normalized = <{0}>'.format(token.normalized)
    #print 'child tokens:', token.tokens
    for child_token in token.tokens:
        #print 'child_token.ttype = {0}'.format(child_token.ttype)
        #print 'type(child_token) = {0}'.format(type(child_token))
        #print 'child_token.normalized = <{0}>'.format(child_token.normalized)
        #print 'child_token.is_group() = {0}'.format(child_token.is_group())
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

    #print 'token.ttype = {0}'.format(token.ttype)
    #print 'type(token) = {0}'.format(type(token))
    #print 'token.normalized = <{0}>'.format(token.normalized)
    #print 'child tokens:', token.tokens
    for child_token in token.tokens:
        #print 'child_token.ttype = {0}'.format(child_token.ttype)
        #print 'type(child_token) = {0}'.format(type(child_token))
        #print 'child_token.normalized = <{0}>'.format(child_token.normalized)
        #print 'child_token.is_group() = {0}'.format(child_token.is_group())
        if child_token.ttype in (Token.Text.Whitespace, Token.Text.Whitespace.Newline):
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
    sqlparse.sql.Comparison: canonicalizer_comparison
}


def canonicalize_token(token):
    """
    Canonicalize a sql statement token.
    """

    normalized = ''
    parameterized = ''
    values = []
    if token.ttype and CANONICALIZERS.has_key(token.ttype):
        normalized, parameterized, values = CANONICALIZERS[token.ttype](token)
    elif token.is_group():
        if CANONICALIZERS_BY_CLASS_TYPE.has_key(type(token)):
            normalized, parameterized, values = CANONICALIZERS_BY_CLASS_TYPE[type(token)](token)
        else:
            #print 'token.ttype = {0}'.format(token.ttype)
            #print 'type(token) = {0}'.format(type(token))
            #print 'token.normalized = <{0}>'.format(token.normalized)
            #print 'child tokens:', token.tokens
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
        if stmt.get_type() == 'UNKNOWN':
            result.append(
                ('{0}'.format(stmt), None, None, [])
            )
            continue

        normalized = ''
        parameterized = ''
        values = []
        for token in stmt.tokens:
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

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlfile', help="process sql statements contained in an sql file")
    args = parser.parse_args()

    parameterized_sql_counts = {}

    print '#' * 80

    if args.sqlfile:
        # contents of sqlfile will be one sql statement per line

        try:
            f = open(args.sqlfile)
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                print line
                ret = canonicalize_sql(line)
                for data in ret:
                    if data[2]:
                        parameterized_sql = data[2]
                    else:
                        parameterized_sql = 'UNKNOWN'
                    if parameterized_sql_counts.has_key(parameterized_sql):
                        parameterized_sql_counts[parameterized_sql] += 1
                    else:
                        parameterized_sql_counts[parameterized_sql] = 1

            # show results
            print
            print 'stats:'
            print '=' * 80
            for k, v in parameterized_sql_counts.iteritems():
                print '{0} {1}'.format(v, k)
        except Exception, e:
            print 'An error has occurred: {0}'.format(e)