#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest
import sqlcanon

class CanonicalizeSqlTests(unittest.TestCase):

    def test_canonicalize_sql_1(self):
        sqlcanon.COLLAPSE_TARGET_PARTS = False
        sql = 'select * from foo where id = 1'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            # original sql
            sql,

            # canonicalized sql
            u'SELECT * FROM `foo` WHERE `id`=1',

            # parameterized sql
            u'SELECT * FROM `foo` WHERE `id`=%d',

            # values for parameterized sql
            [1]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_2(self):
        sqlcanon.COLLAPSE_TARGET_PARTS = False
        sql = 'select * from foo where id in ( 1, 2, 3 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u'SELECT * FROM `foo` WHERE `id` IN (1,2,3)',
            u'SELECT * FROM `foo` WHERE `id` IN (%d,%d,%d)',
            [1, 2, 3]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_3(self):
        sqlcanon.COLLAPSE_TARGET_PARTS = False
        sql = 'insert into bar values ( \'string\', 25, 50.00 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u'INSERT INTO `bar` VALUES (\'string\',25,50.00)',
            u'INSERT INTO `bar` VALUES (%s,%d,%f)',
            ['string', 25, 50.00]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_4(self):
        sqlcanon.COLLAPSE_TARGET_PARTS = False
        sql = 'insert into foo ( col1, col2, col3 ) values ( 50.00, \'string\', 25 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u'INSERT INTO foo(`col1`,`col2`,`col3`) VALUES (50.00,\'string\',25)',
            u'INSERT INTO foo(`col1`,`col2`,`col3`) VALUES (%f,%s,%d)',
            [50.00, 'string', 25]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_5(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = False
        sql = r"""insert into foo.bar ( a, b , c) values ( 'ab\'c' ,  "d\"ef"  , 'ghi'  )"""
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            ur"""INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES ('ab\'c','d"ef','ghi')""",
            ur'INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (%s,%s,%s)',
            ["ab'c", 'd"ef', 'ghi']
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_6(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = False
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

    def test_canonicalize_sql_7(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = False
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
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=1 OR `t1`.`id`=2)",
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=%d OR `t1`.`id`=%d)",
            [1, 2]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_8(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = False
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
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=1 OR `t1`.`id`=2) AND `t1`.`c1`>5",
            u"SELECT `t1`.`c1`,`t2`.`c1` FROM `t1`,`t2` WHERE `t1`.`id`=`t2`.`id` AND (`t1`.`id`=%d OR `t1`.`id`=%d) AND `t1`.`c1`>%d",
            [1, 2, 5]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_9(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = False
        sql = r'select @@version_comment  limit  1'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u"SELECT @@version_comment LIMIT 1",
            u"SELECT @@version_comment LIMIT %d",
            [1]
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_10(self):
        sqlcanon.COLLAPSE_TARGET_PARTS = True
        sql = 'select * from foo where id in ( 1, 2, 3 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u'SELECT * FROM `foo` WHERE `id` IN (N)',
            u'SELECT * FROM `foo` WHERE `id` IN (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_11(self):
        sqlcanon.COLLAPSE_TARGET_PARTS = True
        sql = 'insert into bar values ( \'string\', 25, 50.00 )'
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            u'INSERT INTO `bar` VALUES (N)',
            u'INSERT INTO `bar` VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_12(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = True
        sql = r"""insert into foo.bar ( a, b , c) values ( 'ab\'c' ,  "d\"ef"  , 'ghi'  )"""
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            ur"""INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (N)""",
            ur'INSERT INTO `foo`.bar(`a`,`b`,`c`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_13(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = True
        sql = r"""
            insert into people(name, phone, email) values ('Jay', '123', 'jay@jay.com'),('Elmer', '234', 'elmer@elmer.com')
        """
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            ur"""INSERT INTO people(`name`,`phone`,`email`) VALUES (N)""",
            ur'INSERT INTO people(`name`,`phone`,`email`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_14(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = True
        sql = r"""
            insert into people(name, phone, email) values ('Bob', '456', 'bob@bob.com')
        """
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            ur"""INSERT INTO people(`name`,`phone`,`email`) VALUES (N)""",
            ur'INSERT INTO people(`name`,`phone`,`email`) VALUES (N)',
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_15(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = True
        sql = r"""
            select * from people where name in ('Jay', 'Elmer')
        """
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            []
            )]
        self.assertEqual(ret, expected_ret)

    def test_canonicalize_sql_16(self):
        self.maxDiff = None
        sqlcanon.COLLAPSE_TARGET_PARTS = True
        sql = r"""
            select * from  people where name in ('Jay', 'Elmer', 'Bob')
        """
        ret = sqlcanon.canonicalize_sql(sql)
        expected_ret = [(
            sql,
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            ur"SELECT * FROM `people` WHERE `name` IN (N)",
            []
            )]
        self.assertEqual(ret, expected_ret)

if __name__ == '__main__':
    unittest.main()