Sqlcanon Documentation
======================


Description
-----------

Sqlcanon is a tool that canonicalizes statements read from either log files, stdin or captured packets.

When applicable (especially when reading from log files) it also extracts additional data found and saved for reporting purposes.

Currently it has two parts: sqlcanonclient and sqlcanon server.  Sqlcanonclient is the one responsible for canonicalizing and extracting data. It has the option to pass data to sqlcanon server (in client-server mode) or just store them locally (stand-alone mode).


Current Features
----------------

* Process MySQL slow query log
* Process MySQL general query log
* Process statements from captured packets
* Process statements from stdin
* Captured statements are stored as RRD.


Running sqlcanon server
-----------------------

If this is the first time that you will run sqlcanon server, you will need to install its requirements first.
It is recommended that virtual environment is used.

### Requirements installation and database initialization
```
$ virtualenv <envs_dir>/sqlcanon
$ source <envs_dir>/sqlcanon/bin/activate
$ cd <sqlcanon_src_root_dir>/sqlcanon
$ ./install_requirements.sh
$ ./manage.py syncdb
# Enter admin account/password when prompted
$ ./manage.py migrate
```

### Running using built-in server
```
$ cd <sqlcanon_src_root_dir>/sqlcanon
$ python manage.py runserver [optional port number, or ipaddr:port]
```

Using sqlcanonclient
--------------------

### Requirements installation
```
$ virtualenv <envs_dir>/sqlcanonclient
$ source <envs_dir>/sqlcanonclient/bin/activate
$ cd <sqlcanon_src_root_dir>/sqlcanonclient/src/sqlcanonclient
$ pip install -r requirements.txt
```

### Usage
```
sqlcanonclient.py [-h] [-t {s,g}] [-d DB] [-s]
                  [--server-base-url SERVER_BASE_URL]
                  [--save-statement-data-path SAVE_STATEMENT_DATA_PATH]
                  [--save-explained-statement-path SAVE_EXPLAINED_STATEMENT_PATH]
                  [-e EXPLAIN_OPTIONS]
                  [-l | --local-run-last-statements | --print-top-queries PRINT_TOP_QUERIES]
                  [--sliding-window-length SLIDING_WINDOW_LENGTH]
                  [-i INTERFACE] [-f FILTER]
                  [file]

positional arguments:
  file                  MySQL log file to open, if not specified stdin will be
                        used. (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -t {s,g}, --type {s,g}
                        Log file format -- s: slow query log, g: general query
                        log (default: s)
  -d DB, --db DB        database name (default: /tmp/sqlcanonclient.db)
  -s, --stand-alone     Run as stand alone (will not send data to server).
                        (default: False)
  --server-base-url SERVER_BASE_URL
                        Server base URL. (default: http://localhost:8000)
  --save-statement-data-path SAVE_STATEMENT_DATA_PATH
                        URL to be used for saving statement data. (default:
                        /save-statement-data/)
  --save-explained-statement-path SAVE_EXPLAINED_STATEMENT_PATH
                        URL to be used for saving explain statement. (default:
                        /save-explained-statement/)
  -e EXPLAIN_OPTIONS, --explain-options EXPLAIN_OPTIONS
                        Explain MySQL options:
                        h=<host>,u=<user>,p=<passwd>,d=<db> (default:
                        h=127.0.0.1,u=root)
  -l, --sniff           launch packet sniffer (default: False)
  --local-run-last-statements
                        In stand alone mode, prints last seen statements
                        (default: False)
  --print-top-queries PRINT_TOP_QUERIES
                        Prints top queries stored on local data. (default: 0)
  --sliding-window-length SLIDING_WINDOW_LENGTH
                        Length of period in number of minutes. (default: 5)
  -i INTERFACE, --interface INTERFACE
                        interface to sniff from (default: lo0)
  -f FILTER, --filter FILTER
                        pcap-filter (default: dst port 3306)
  --encoding ENCODING   String encoding. (default: utf_8)
  --encoding-errors {strict,ignore,replace}
                        String encoding error handling scheme. (default:
                        replace)

```

### Processing MySQL slow query log


#### Client-server mode:

```
$ ./sqlcanonclient.py /var/log/mysql/mysql-slow.log
```

The above command will process the contents of the specified slow query log and will send data to the sqlcanon server using the default --server-base-url value. If you specified ipaddr:port option when running sqlcanon server, you need to provide this to the sqlcanon client using --server-base-url.
In client-server mode, sqlcanonclient will not attempt to save data locally, it will instead pass it to the sqlcanon server.  When sqlcanon server receives data it will ask sqlcanonclient to run an EXPLAIN for statements that were seen for the first time.  The sqlcanon will run EXPLAIN using the connection options specified in --explain-options. The resulting rows will be sent to and stored by the sqlcanon server.

#### Viewing data in client-server mode:

To view data stored by sqlcanon server, access the server admin page:
```
http://localhost:8000/admin/
# or use ipaddr:port if you specified it during runserver
```

Other data views such as last statements found and top queries are found under:
```
http://localhost:8000/
```

#### Stand-alone mode:
In stand-alone mode you simply use -s option and optionally the name of the sqlite database to be used for storing data locally.

```
$ ./sqlcanonclient.py -s -d ./data.db /var/log/mysql/mysql-slow.log

# from stdin variation
$ cat /var/log/mysql/mysql-slow.log | ./sqlcanonclient.py -s -d ./data.db
```

The above command will run sqlcanonclient in stand-alone mode (sqlcanon server is not needed).  If -d option is not specified, it will use a temporary sqlite database to store data.

#### Viewing data in stand-alone mode:

Current data views present on sqlcanon client are last statements seen and top queries:
```
# continously display last seen statements for the last 5 minutes (usually ran under on another terminal window)
$ ./sqlcanonclient.py -s -d ./data.db --local-run-last-statements --sliding-window-length 5

# print top 5 queries
$ ./sqlcanonclient.py -s -d ./data.db --print top-queries 5
```

Currently sqlcanonclient has no capability to display rows stored on local tables.
To check locally stored data, you can use sqlite3 to open the db file.


### Processing MySQL general query log

client-server mode:
```
$ ./sqlcanonclient.py -t g /var/log/mysql/mysql.log
```

stand-alone mode:
```
$ ./sqlcanonclient.py -s -d ./data.db -t g /var/log/mysql/mysql.log

# from stdin variation
$ cat /var/log/mysql/mysql.log | ./sqlcanonclient.py -s -d ./data.db -t g
```

### To read statements from captured packets

```
# sqlcanonclient needs user with privilege to capture packet data to run sniffer.
# Listen from interface 'lo' (loopback)
$ ./sqlcanonclient.py -l -i lo

# Listen from interface 'eth0', filter packets by destination port 3306
$ ./sqlcanonclient.py -l -i eth0 -f dst port 3306
```


