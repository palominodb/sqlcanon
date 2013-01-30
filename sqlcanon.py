import re

def canonicalize_sql(sql):
    """
    Normalizes whitespace, quoting, and case.
    Parameterizes sql.

    Returns a tuple in this format:
        (parameterized sql, values)

        values
            - can be a single value or a tuple
    """

    # try checking for SELECTs first
    pat = r'^\s*select'
    m = re.search(pat, sql, re.IGNORECASE)
    if m:
        # we have a SELECT statement

        # sample pattern:
        #   SELECT * FROM `bob` WHERE `id` = 100
        pat = r'^\s*select\s+(\*)\s+from\s+`?([^\s`]+)`?\s+where\s+`?([^\s`]+)`?\s*=\s*(\d+)\s*$'
        m = re.search(pat, sql, re.IGNORECASE)
        if m:
            field_list = m.group(1)
            table_name = m.group(2)
            where_cond_field = m.group(3)
            where_cond_val = m.group(4)
            canon_sql = 'SELECT {0} FROM `{1}` WHERE `{2}` = %d'.format(
                field_list, table_name, where_cond_field)
            return (canon_sql, where_cond_val)

    # TODO: test other patterns here for whitespaces, quotes, case, field list, table list, complex conditions
    # This project looks interesting and can probably be used to parse more complicated patterns:
    #   https://github.com/andialbrecht/sqlparse


if __name__ == '__main__':
    # test data
    sqls = [
        'select * from abc where id = 1',
        'select * from def where id = 2',
        'select * from def where id = 3',
        'select * from ghi where id = 4',
    ]

    canon_sqls = {}

    for sql in sqls:
        ret = canonicalize_sql(sql)
        if ret:
            canon_sql, val = ret
            if canon_sqls.has_key(canon_sql):
                canon_sqls[canon_sql] = canon_sqls[canon_sql] + 1
            else:
                canon_sqls[canon_sql] = 1

    for key in canon_sqls:
        print 'SQL: {0}'.format(key)
        print 'Count: {0}'.format(canon_sqls[key])
        print

