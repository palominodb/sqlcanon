import unittest
import sqlcanon


class CanonicalizeSqlTests(unittest.TestCase):

    CANON_SQL1 = 'SELECT * FROM `bob` WHERE `id` = %d'

    def assert_if_equal_to_canon_sql1(self, sql):
        ret = sqlcanon.canonicalize_sql(sql)
        self.assertIsNotNone(ret, msg='sqlcanon.canonicalize_sql returned None.')
        if ret:
            canon_sql, val = ret
            self.assertEqual(canon_sql, self.CANON_SQL1)

    def test_canonicalize_sql_simple_select_whitespace(self):
        sql = r'  SELECT   *   FROM   `bob`    WHERE   `id`   =     100   '
        self.assert_if_equal_to_canon_sql1(sql)

    def test_canonicalize_sql_simple_select_case(self):
        sql = r'select * From `bob` WheRE `id` = 100'
        self.assert_if_equal_to_canon_sql1(sql)

    def test_canonicalize_sql_simple_select_quoting(self):
        sql = r'select * from bob where id = 100'
        self.assert_if_equal_to_canon_sql1(sql)

    def test_canonicalize_sql_mixed_whitespace_case_quoting(self):
        sql = r'  Select  * FrOM  bob   where    `id` =  100  '
        self.assert_if_equal_to_canon_sql1(sql)

    def test_canonicalize_sql_select_in_1(self):
        sql = r'select * from `bob` where `id` in (1,2,3)'
        expected_canon_sql = r'SELECT * FROM `bob` WHERE `id` IN (%d, %d, %d)'
        ret = sqlcanon.canonicalize_sql(sql)
        self.assertIsNotNone(ret, msg='sqlcanon.canonicalize_sql returned None.')
        if ret:
            canon_sql, val = ret
            self.assertEqual(canon_sql, expected_canon_sql)

    def test_canonicalize_sql_select_in_2(self):
        sql = r'select * from `bob` where `id` in (3,2,1)'
        expected_canon_sql = r'SELECT * FROM `bob` WHERE `id` IN (%d, %d, %d)'
        ret = sqlcanon.canonicalize_sql(sql)
        self.assertIsNotNone(ret, msg='sqlcanon.canonicalize_sql returned None.')
        if ret:
            canon_sql, val = ret
            self.assertEqual(canon_sql, expected_canon_sql)


if __name__ == '__main__':
    unittest.main()