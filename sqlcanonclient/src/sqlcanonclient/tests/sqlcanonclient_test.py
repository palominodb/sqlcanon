#!/usr/bin/env python

import argparse
import codecs
import os
import pprint
import sqlite3
import tempfile
import unittest

import MySQLdb
import yaml

import sqlcanonclient


TEST_MYSQL_DB = 'sqlcanonclient_test'

FILE_DIR = os.path.abspath(os.path.dirname(__file__))

pp = pprint.pprint


class QueryCanonicalizationTest(unittest.TestCase):

    def _test_canonicalize_statement(self, original_queries, parameterized_queries):
        for original, parameterized in zip(original_queries, parameterized_queries):
            ret = sqlcanonclient.canonicalize_statement(original)
            self.assertEqual(parameterized, ret[0][2])

    def test_canonicalize_selects(self):
        original_queries = (
            ur'select * from foo where id = 1',
            ur'select * from foo where id in ( 1, 2, 3 )',
            ur"""
                SELECT count(order_id) as cnt
                FROM orders
                WHERE user_id = 24142085
                AND order_type_ IN (3, 1)
            """)
        parameterized_queries = (
            ur'SELECT * FROM `foo` WHERE `id`=%d',
            ur'SELECT * FROM `foo` WHERE `id` IN (N)',
            ur'SELECT COUNT(`order_id`) AS `cnt` FROM `orders` WHERE `user_id`=%d AND `order_type_` IN (N)')
        self._test_canonicalize_statement(original_queries, parameterized_queries)

    def test_canonicalize_inserts(self):
        original_queries = (
            ur"insert into people(name, phone, email) values ('Jay', '123', 'jay@jay.com'),('Elmer', '234', 'elmer@elmer.com')",
            ur"insert into bar values ( \'string\', 25, 50.00 )"
            )
        parameterized_queries = (
            ur"INSERT INTO people(`name`,`phone`,`email`) VALUES (N)",
            ur"INSERT INTO `bar` VALUES (N)")
        self._test_canonicalize_statement(original_queries, parameterized_queries)


class MysqlSlowQueryLogParsingTest(unittest.TestCase):
    def setUp(self):
        tmpf = tempfile.NamedTemporaryFile(delete=False)
        self.db = tmpf.name
        tmpf.close()

        self.conn = MySQLdb.connect()
        c = self.conn.cursor()
        c.execute('CREATE SCHEMA %s;' % (TEST_MYSQL_DB,))
        c.execute('USE %s;' % (TEST_MYSQL_DB,))
        c.execute("""
            CREATE TABLE table1 (
                id int(11) NOT NULL AUTO_INCREMENT,
                name varchar(255) DEFAULT NULL UNIQUE,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB CHARACTER SET=utf8;
            """)
        c.execute("""
            INSERT INTO table1 (name)
            VALUES ('name1'), ('name2'), ('name3')
            """)
        c.close()

    def tearDown(self):
        c = self.conn.cursor()
        c.execute('DROP SCHEMA %s' % (TEST_MYSQL_DB,))
        c.close()
        self.conn.close()

    def test_mysql_slow_query_log_parse_contents(self):
        test_log_file = os.path.join(FILE_DIR, 'data', 'mysql-slow.log')
        class FakeOptions:
            def __init__(self):
                self.stand_alone = True
                self.server_id = 1
                self.type = 's'
                self.file = test_log_file
        sqlcanonclient.OPTIONS = FakeOptions()
        sqlcanonclient.LocalData.init_db(self.db)
        sqlcanonclient.DataManager.set_last_db_used(None)
        sqlcanonclient.EXPLAIN_OPTIONS = {}

        slow_query_log_processor = sqlcanonclient.SlowQueryLogProcessor()
        with codecs.open(test_log_file, encoding='utf_8', errors='replace') as f:
            slow_query_log_processor.process_log_contents(f)

        conn = sqlite3.connect(self.db)
        with conn:
            c = conn.cursor()

            c.execute("""
                select
                    statement, server_id, canonicalized_statement,
                    query_time, lock_time, rows_sent, rows_examined, rows_affected,
                    rows_read, bytes_sent, tmp_tables, tmp_disk_tables,
                    tmp_table_sizes
                from statements""")
            rows = c.fetchall()
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row,
                (
                    u"select * from table1 where name in ('name1', 'name2')\n",
                    1,
                    u"SELECT * FROM `table1` WHERE `name` IN (N)",
                    0.000253, 0.000033, 123, 456, 789,
                    12, 345, 678, 901,
                    234
                ))

            c.execute('select * from explained_statements')
            rows = c.fetchall()
            self.assertEqual(len(rows), 1)

            c.execute('select * from explain_results')
            rows = c.fetchall()
            self.assertTrue(len(rows) > 0)


if __name__ == '__main__':
    unittest.main(verbose=2)
