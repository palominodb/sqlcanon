#!/usr/bin/env python

from datetime import datetime, timedelta
import pprint
import string
import unittest
from unittest import TestCase

import sqlcanonclient as c


PP = pprint.PrettyPrinter(indent=4)


class CanonicalizeSqlTests(TestCase):

    def test_canonicalize_statement_1(self):
        sql = u'select * from foo where id = 1'
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            # original sql
            c.query_strip(sql),

            # canonicalized sql
            u'SELECT * FROM `foo` WHERE `id`=1',

            # parameterized sql
            u'SELECT * FROM `foo` WHERE `id`=%d',

            # values for parameterized sql
            [1]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_2(self):
        sql = 'select * from foo where id in ( 1, 2, 3 )'
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u'SELECT * FROM `foo` WHERE `id` IN (N)',
            u'SELECT * FROM `foo` WHERE `id` IN (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_3(self):
        sql = 'insert into bar values ( \'string\', 25, 50.00 )'
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u'INSERT INTO `bar` VALUES (N)',
            u'INSERT INTO `bar` VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_4(self):
        sql = 'insert into foo ( col1, col2, col3 ) values ( 50.00, \'string\', 25 )'
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u'INSERT INTO foo(`col1`,`col2`,`col3`) VALUES (N)',
            u'INSERT INTO foo(`col1`,`col2`,`col3`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_5(self):
        sql = r"""insert into foo.bar ( a, b , c) values ( 'ab\'c' ,  "d\"ef"  , 'ghi'  )"""
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            ur"INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (N)",
            ur'INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_6(self):
        sql = r"""
            select t1.c1, t2.c1
            from t1, t2
            where t1.id = t2.id and (t1.id = 1 or t1.id = 2)
            """
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=1 OR `t1`.`id`=2)",
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=%d OR `t1`.`id`=%d)",
            [1, 2]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_7(self):
        sql = r"""
            select
                t1.c1 ,
                t2.c1
            from
                t1 ,
                t2
            where
                t1.id = t2.id
                and
                (
                    t1.id = 1
                    or
                    t1.id = 2
                )
            """
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=1 OR `t1`.`id`=2)",
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=%d OR `t1`.`id`=%d)",
            [1, 2]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_8(self):
        sql = r"""
            select
                t1.c1 ,
                t2.c1
            from
                t1 ,
                t2
            where
                t1.id  =  t2.id
                and
                (
                    t1.id   =   1
                    or
                    t1.id   =   2
                )
                and
                t1.c1   >   5

            """
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=1 OR `t1`.`id`=2) AND `t1`.`c1`>5",
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=%d OR `t1`.`id`=%d) AND `t1`.`c1`>%d",
            [1, 2, 5]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_9(self):
        sql = r'select @@version_comment  limit  1'
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u"SELECT @@version_comment LIMIT 1",
            u"SELECT @@version_comment LIMIT %d",
            [1]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_10(self):
        sql = 'select * from foo where id in ( 1, 2, 3 )'
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u'SELECT * FROM `foo` WHERE `id` IN (N)',
            u'SELECT * FROM `foo` WHERE `id` IN (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_11(self):
        sql = 'insert into bar values ( \'string\', 25, 50.00 )'
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            u'INSERT INTO `bar` VALUES (N)',
            u'INSERT INTO `bar` VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_12(self):
        sql = r"""insert into foo.bar ( a, b , c) values ( 'ab\'c' ,  "d\"ef"  , 'ghi'  )"""
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            ur"""INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (N)""",
            ur'INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_13(self):
        sql = ur"""
            insert into people(name, phone, email) values ('Jay', '123', 'jay@jay.com'),('Elmer', '234', 'elmer@elmer.com')
        """
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            ur"""INSERT INTO people(`name`,`phone`,`email`) VALUES (N)""",
            ur'INSERT INTO people(`name`,`phone`,`email`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_14(self):
        sql = r"""
            insert into people(name, phone, email) values ('Bob', '456', 'bob@bob.com')
        """
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            ur"""INSERT INTO people(`name`,`phone`,`email`) VALUES (N)""",
            ur'INSERT INTO people(`name`,`phone`,`email`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_15(self):
        sql = r"""
            select * from people where name in ('Jay', 'Elmer')
        """
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_statement_16(self):
        sql = r"""
            select * from  people where name in ('Jay', 'Elmer', 'Bob')
        """
        ret = c.canonicalize_statement(sql)
        expected_ret = [(
            c.query_strip(sql),
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            []
            )]
        self.assertEqual(ret, expected_ret)

class QueryListerTests(TestCase):
    def setUp(self, *args, **kwargs):
        self.queries = queries = [
            """insert into people(name, phone, email) values ('Jay', '123', 'jay@jay.com'),
                ('Elmer', '234', 'elmer@elmer.com')""",
            """insert into people(name, phone, email) values ('Bob', '456', 'bob@bob.com')""",
            """select * from people""",
            """select * from people where name in ('Jay', 'Elmer')""",
            """select * from  people where name in ('Jay', 'Elmer', 'Bob')""",
            """select * from people where name in ('J', 'E')"""
        ]

        self.dt_now = dt_now = datetime.now()
        self.dts = dts = [
            dt_now - timedelta(minutes=5),
            dt_now - timedelta(minutes=4),
            dt_now - timedelta(minutes=3),
            dt_now - timedelta(minutes=2),
            dt_now - timedelta(minutes=1),
            dt_now,
            ]

        self.lister = lister = c.QueryLister()

        for dt, query in zip(dts, queries):
            query, __, canonicalized_query, __ = c.canonicalize_statement(query)[0]
            lister.append_statement(statement=query, canonicalized_statement=canonicalized_query, dt=dt)


    def tearDown(self):
        pass

    def test_get_list_1(self):

        result = self.lister.get_list(self.dt_now - timedelta(minutes=5),
            self.dt_now - timedelta(minutes=3))
        self.assertEqual(len(result), 3)
        counts = zip(*result)[4]
        self.assertEqual(counts, (2, 2, 1))

    def test_get_list_2(self):
        result = self.lister.get_list(self.dt_now - timedelta(minutes=4),
            self.dt_now - timedelta(minutes=2))
        self.assertEqual(len(result), 3)
        counts = zip(*result)[4]
        self.assertEqual(counts, (1, 1, 1))

    def test_get_list_3(self):
        result = self.lister.get_list(self.dt_now - timedelta(minutes=3),
            self.dt_now - timedelta(minutes=1))
        self.assertEqual(len(result), 3)
        counts = zip(*result)[4]
        self.assertEqual(counts, (1, 2, 2))

    def test_get_list_4(self):
        result = self.lister.get_list(self.dt_now - timedelta(minutes=2),
            self.dt_now)
        self.assertEqual(len(result), 3)
        counts = zip(*result)[4]
        self.assertEqual(counts, (3, 3, 3))

    def test_get_list_5(self):
        result = self.lister.get_list(self.dt_now - timedelta(minutes=1),
            self.dt_now + timedelta(minutes=1))
        self.assertEqual(len(result), 2)
        counts = zip(*result)[4]
        self.assertEqual(counts, (2, 2))

    def test_get_list_6(self):
        result = self.lister.get_list(self.dt_now,
            self.dt_now + timedelta(minutes=2))
        self.assertEqual(len(result), 1)
        counts = zip(*result)[4]
        self.assertEqual(counts, (1,))

    def test_get_list_7(self):
        result = self.lister.get_list(self.dt_now + timedelta(minutes=1),
            self.dt_now + timedelta(minutes=3))
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()