#!/usr/bin/env python
import unittest
import sqlcanon

class CanonicalizeSqlTests(unittest.TestCase):

    def test_canonicalize_sql_1(self):
        sql = 'select * from foo where id = 1'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [
            (
                # original sql
                sql,

                # canonicalized sql
                u'SELECT * FROM `foo` WHERE `id`=1',

                # parameterized sql
                u'SELECT * FROM `foo` WHERE `id`=%d',

                # values for parameterized sql
                [1]
            )
        ]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_2(self):
        sql = 'select * from foo where id in ( 1, 2, 3 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [
            (
                # original sql
                sql,

                # canonicalized sql
                u'SELECT * FROM `foo` WHERE `id` IN (1,2,3)',

                # parameterized sql
                u'SELECT * FROM `foo` WHERE `id` IN (%d,%d,%d)',

                # values for parameterized sql
                [1, 2, 3]
            )
        ]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_3(self):
        sql = 'insert into bar values ( \'string\', 25, 50.00 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [
            (
                # original sql
                sql,

                # canonicalized sql
                u'INSERT INTO `bar` VALUES (\'string\',25,50.00)',

                # parameterized sql
                u'INSERT INTO `bar` VALUES (%s,%d,%f)',

                # values for parameterized sql
                ['string', 25, 50.00]
            )
        ]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_4(self):
        sql = 'insert into foo ( col1, col2, col3 ) values ( 50.00, \'string\', 25 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [
            (
                # original sql
                sql,

                # canonicalized sql
                u'INSERT INTO `foo` (`col1`,`col2`,`col3`) VALUES (50.00,\'string\',25)',

                # parameterized sql
                u'INSERT INTO `foo` (`col1`,`col2`,`col3`) VALUES (%f,%s,%d)',

                # values for parameterized sql
                [50.00, 'string', 25]
            )
        ]
        self.assertEqual(ret, expected_ret)

if __name__ == '__main__':
    unittest.main()