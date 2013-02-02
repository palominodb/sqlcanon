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
                sql,
                u'SELECT * FROM `foo` WHERE `id` IN (1,2,3)',
                u'SELECT * FROM `foo` WHERE `id` IN (%d,%d,%d)',
                [1, 2, 3]
            )
        ]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_3(self):
        sql = 'insert into bar values ( \'string\', 25, 50.00 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [
            (
                sql,
                u'INSERT INTO `bar` VALUES (\'string\',25,50.00)',
                u'INSERT INTO `bar` VALUES (%s,%d,%f)',
                ['string', 25, 50.00]
            )
        ]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_4(self):
        sql = 'insert into foo ( col1, col2, col3 ) values ( 50.00, \'string\', 25 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [
            (
                sql,
                u'INSERT INTO foo(`col1`,`col2`,`col3`) VALUES (50.00,\'string\',25)',
                u'INSERT INTO foo(`col1`,`col2`,`col3`) VALUES (%f,%s,%d)',
                [50.00, 'string', 25]
            )
        ]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_5(self):
        self.maxDiff = None
        sql = r"""insert into foo.bar ( a, b , c) values ( 'ab\'c' ,  "d\"ef"  , 'ghi'  )"""
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [
            (
                sql,
                ur"""INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES ('ab\'c','d"ef','ghi')""",
                ur'INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (%s,%s,%s)',
                ["ab'c", 'd"ef', 'ghi']
            )
        ]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_6(self):
        self.maxDiff = None
        sql = r"""
            select t1.c1, t2.c1
            from t1, t2
            where t1.id = t2.id and (t1.id = 1 or t1.id = 2)
            """
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=1 OR `t1`.`id`=2)",
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=%d OR `t1`.`id`=%d)",
            [1, 2]
        )]
        self.assertEqual(ret, expected_ret)


if __name__ == '__main__':
    unittest.main()