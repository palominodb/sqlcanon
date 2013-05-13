Sqlcanon Server REST API
========================

For every resource, common attributes are the following:
* list endpoint - allows retrieval of list of resources. Individual resource can be retrieved by appending primary key, for example, /api/v1/explained_statement/1/
* schema - retrieves info about the resource such as the supported fields, allowed HTTP methods, and allowed fields for filtering

HTTP status code should be checked for every API calls. In most cases when error occurs, the *error_message* field will be included in the content.


Statement Data
--------------

List endpoint:
```
/api/v1/statement_data/
```

Schema:
```
/api/v1/statement_data/schema/
```


### Get Top Queries
API:
```
POST /api/v1/statement_data/get_top_queries/
```
POST data should be a JSON object in the form:
```
{
    "n": 1,             # top limit
    "column": "",       # column to be used in ordering
                        # choices:
                        #   count
                        #   total_query_time
                        #   total_lock_time
                        #   total_rows_read
                        #   avg_query_time
                        #   avg_lock_time
                        #   avg_rows_read
    "hostname": "",     # hostname to be used in filtering
                        # set to "__none__" to filter hostnames
                        #   that are None
    "schema": ""        # schema to be used in filtering
                        # set to "__none__" to filter schemas
                        #   that are None
}
```

Sample usage and output:
```
$ curl -u admin:admin -H 'Content-Type: applicaton/json' -X POST -d '{"n": 5, "column": "count"}' http://localhost:8000/api/v1/statement_data/get_top_queries/

{
    "objects": [
        {
            "avg_lock_time": 0.0,
            "avg_query_time": 9.057777777777777e-05,
            "avg_rows_read": null,
            "canonicalized_statement": "SELECT @@version_comment LIMIT %d",
            "canonicalized_statement_hash": 1776896760,
            "count": 45,
            "total_lock_time": 0.0,
            "total_query_time": 0.004076,
            "total_rows_read": null
        },
        {
            "avg_lock_time": 0.0,
            "avg_query_time": 8.580000000000003e-05,
            "avg_rows_read": 1.0,
            "canonicalized_statement": "SELECT @@session.tx_isolation",
            "canonicalized_statement_hash": -385871481,
            "count": 40,
            "total_lock_time": 0.0,
            "total_query_time": 0.003432000000000001,
            "total_rows_read": 40
        },
        {
            "avg_lock_time": 3.6153846153846145e-05,
            "avg_query_time": 0.00026423076923076926,
            "avg_rows_read": 20.6923,
            "canonicalized_statement": "UNKNOWN",
            "canonicalized_statement_hash": -1360639565,
            "count": 26,
            "total_lock_time": 0.0009399999999999999,
            "total_query_time": 0.006870000000000001,
            "total_rows_read": 538
        }
    ]
}
```


### Get Last Statements
API:
```
POST /api/v1/statement_data/get_last_statements/
```
POST data should be a JSON object in the form:
```
{
    "n": 1      # minutes
}
```

Sample usage and output:
```
$ curl -u admin:admin -H 'Content-Type: application/json' -X POST -d '{"n": 5}' http://localhost:8000/api/v1/statement_data/get_last_statements/

{
    "objects": [
        {
            "count": 1,
            "statement_data": {
                "canonicalized_statement": "SELECT COUNT(*) FROM `mysql`.`user` WHERE USER=%s AND `password`=%s",
                "canonicalized_statement_hash": 1423110813,
                "canonicalized_statement_hostname_hash": -157160433,
                "dt__count": 1,
                "dt__max": "2013-03-22T23:50:29",
                "server_id": 4,
                "statement": "SELECT count(*) FROM mysql.user WHERE user='root' and password=''"
            }
        },
        {
            "count": 1,
            "statement_data": {
                "canonicalized_statement": "SELECT concat(%s,`TABLE_SCHEMA`,%s, TABLE_NAME,%s) FROM `information_schema`.`TABLES` WHERE `ENGINE`=%s",
                "canonicalized_statement_hash": -399793793,
                "canonicalized_statement_hostname_hash": 357645071,
                "dt__count": 1,
                "dt__max": "2013-03-22T23:50:29",
                "server_id": 4,
                "statement": "select concat('select count(*) into @discard from `',\n                    TABLE_SCHEMA, '`.`', TABLE_NAME, '`') \n      from information_schema.TABLES where ENGINE='MyISAM'"
            }
        }
    ]
}
```


Explained Statement
-------------------

List endpoint:
```
/api/v1/explained_statement/
```

Schema:
```
/api/v1/explained_statement/schema/
```


Explain Result
--------------

List endpoint:
```
/api/v1/explain_result/
```

Schema:
```
/api/v1/explain_result/schema/
```
