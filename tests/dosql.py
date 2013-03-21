#!/usr/bin/env python
import random
import string
import MySQLdb
import argparse


conn = None


def rnd_str(size=8):
    return ''.join(random.choice(string.letters + string.digits) for x in range(size))


def rnd_digit():
    return random.choice(string.digits)


def rnd_widgets():
    return 'widgets%s' % (rnd_digit(),)


def create_tables(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id int NOT NULL PRIMARY KEY AUTO_INCREMENT,
            name varchar(255),
            pod varchar(255)
        )
        """)
    for i in range(10):
        c.execute("""
            CREATE TABLE IF NOT EXISTS widgets%s (
                id int NOT NULL PRIMARY KEY AUTO_INCREMENT,
                name varchar(255),
                foo varchar(255)
            )
            """ % (i,))


def qt(s):
    return "'" + s + "'"


def insert_several():
    c = conn.cursor()
    create_tables(c)
    for i in range(100):
        query = "INSERT INTO clusters (name, pod) VALUES (%s, %s)"
        name = rnd_str()
        pod = rnd_str()
        print query % (qt(name), qt(pod))
        c.execute(query, [name, pod])

        for j in range(10):
            query = "INSERT INTO %s (name, foo) VALUES (%%s, %%s)" % (rnd_widgets(),)
            name = rnd_str()
            foo = rnd_str()
            print query % (qt(name), qt(foo))
            c.execute(query, [name, foo])
inserts = insert_several


def do_select():
    c = conn.cursor()
    for i in range(5):
        w = rnd_widgets()
        query = """
           SELECT * FROM %s
           WHERE %s.id IN (1, 3, 5, 7, 9)
            """ % (w, w)
        print query
        c.execute(query)

        w = rnd_widgets()
        query = """
           SELECT c.*, w.name FROM clusters c,
           %s w
           where c.name like %%s and w.id between c.id - 2 and c.id + 2;
            """ % (w,)
        v1 = '%%%s%%' % (rnd_str(),)
        print query % (qt(v1),)
        c.execute(query, [v1])

        w = rnd_widgets()
        query = """
            SELECT * FROM %s where foo like %%s;
            """ % (w,)
        v1 = '%%%s%%' % (rnd_str(),)
        print query % (qt(v1),)
        c.execute(query, [v1])

        w = rnd_widgets()
        query = """
            SELECT * FROM clusters c
            INNER JOIN %s w
            ON c.name = w.name
            WHERE c.pod <= %%s AND c.pod >= %%s AND w.name in (%%s, %%s, %%s)
            """ % (w, )
        v1, v2, v3, v4, v5 = map(lambda x: rnd_str(), range(5))
        print query % (qt(v1), qt(v2), qt(v3), qt(v4), qt(v5))
        c.execute(query, [v1, v2, v3, v4, v5])

        w = rnd_widgets()
        query = """
            SELECT name, count(*) FROM %s
            GROUP BY name
            """ % (w, )
        print query
        c.execute(query)

        w = rnd_widgets()
        query = """
            SELECT foo, count(*) FROM %s
            GROUP BY foo
            HAVING count(*) > 3 OR count(*) = 1
            ORDER BY count(*) DESC
            """ % (w, )
        print query
        c.execute(query)

        w1 = rnd_widgets()
        w2 = rnd_widgets()
        query = """
            SELECT foo, count(*) FROM %s
            GROUP BY foo
            HAVING count(*) > 3 OR count(*) = 1
            UNION
            SELECT foo, count(*) FROM %s
            GROUP BY foo
            HAVING count(*) > 3 OR count(*) = 1
            ORDER BY count(*) DESC
            LIMIT 20
            """ % (w1, w2)
        print query
        c.execute(query)
selects = do_select


def main():
    global conn

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'method',
        choices=['inserts', 'selects'],
        help='method to run.')
    parser.add_argument('-H', '--host', default='localhost', help='db host')
    parser.add_argument('-P', '--port', type=int, help='db port')
    parser.add_argument('-u', '--user', default='sandbox', help='db user')
    parser.add_argument('-p', '--passwd', default='sandbox', help='db password')
    parser.add_argument('-d', '--db', default='sandbox', help='db name')

    args = parser.parse_args()

    opts = dict(host=args.host, user=args.user, passwd=args.passwd, db=args.db)
    if args.port:
        opts.update(dict(port=args.port))
    conn = MySQLdb.connect(**opts)

    src = globals().copy()
    src.update(locals())
    m = src.get(args.method)
    if not m:
        raise Exception('Method %s not implemented.' % (args.method, ))
    with conn:
        m()


if __name__ == '__main__':
    main()
