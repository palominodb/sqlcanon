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

### Requirements Installation
```
$ virtualenv <envs_dir>/sqlcanon
$ source <envs_dir>/sqlcanon/bin/activate
$ cd <sqlcanon_src_root_dir>/sqlcanon
$ ./install_requirements.sh
```

### Sqlcanon Server Database Configuration
You can edit `<src_root_dir>/sqlcanon/sqlcanon/settings.py` or create `<src_root_dir>/sqlcanon/sqlcanon/local_settings.py` to override settings specified in `settings.py`.
`settings.py` or `location_settings.py` should contain the following lines with the correct values:
```
DATABASES = {
    'default': {
        # Choices: 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.' + 'mysql',

        # Or path to database file if using sqlite3.
        'NAME': 'sqlcanon_dev',

        # Not used with sqlite3.
        'USER': '',

        # Not used with sqlite3.
        'PASSWORD': '',

        # Set to empty string for localhost. Not used with sqlite3.
        'HOST': '',

        # Set to empty string for default. Not used with sqlite3.
        'PORT': '',
    }
}
```
**Supported Database Engines**
MySQL: django.db.backends.mysql
sqlite3: django.db.backends.sqlite3


### Database Initialization
```
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
usage: sqlcanonclient.py [-h] [-t {s,g}] [-d DB] [-s]
                         [--server-base-url SERVER_BASE_URL]
                         [--save-statement-data-path SAVE_STATEMENT_DATA_PATH]
                         [--save-explained-statement-path SAVE_EXPLAINED_STATEMENT_PATH]
                         [-e EXPLAIN_OPTIONS]
                         [-l | --local-run-last-statements | --print-top-queries PRINT_TOP_QUERIES]
                         [--sliding-window-length SLIDING_WINDOW_LENGTH]
                         [-i INTERFACE] [-f FILTER] [--encoding ENCODING]
                         [--encoding-errors {strict,ignore,replace}]
                         [-S SERVER_ID] [-C CONFIG] [--no-skip-unknowns]
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
                        [h=<host>][,P=<port>][,u=<user>][,p=<passwd>][,d=<db>]
                        (default: h=127.0.0.1)
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
  -S SERVER_ID, --server-id SERVER_ID
                        Server ID. (default: 1)
  -C CONFIG, --config CONFIG
                        Name of configuration file to use. (default:
                        ./config.yml)
  --no-skip-unknowns    Any value other than 0 will skip processing of non
                        DDL/DML statements. (default: False)
```

### Configration File
If you specify a configuration file via `-C` or `--config`, the values from the file will be load and will override the values from the command line arguments. You have to use the longer versions of the option names and convert dashes into underscores in the configuration file. The following is a sample content:
```
# input file, if not specified, stdin will be used instead
file: /var/log/mysql/mysql-slow.log

# contents of input file
# values: s|g
#   s - MySQL slow query log
#   g - MySQL general query log
type: s

# Local sqlite3 database, used in stand-alone mode
db: /tmp/sqlcanonclient.db

# Run in stand_alone mode?
stand_alone: False

# Server base url, used when not in stand-alone mode
server_base_url: http://localhost:8000

# Server paths: save statement
save_statement_data_path: /save-statement-data/

# Server paths: save explained statement
save_explained_statement_path: /save_explained_statement_path/

# DSN to be used when executing EXPLAIN statements in the form:
# h=<host>,u=<user>,p=<passwd>,d=<db>
explain_options: h=127.0.0.1

# Run packet sniffer?
sniff: False

# Interface to listen to, when running packet sniffer.
interface: lo0

# An pcap-filter expression used to filter packets.
# The default 'dst port 3306' will suffice to for listening packets with destination port 3306.
filter: dst port 3306

# Run a sliding window of last statements? (requires stand_alone=True)
local_run_last_statements: False

# The value specified here is in minutes and is used with local_run_last_statements option.
# A value of 5 means 'display statements found in the last 5 minutes'.
sliding_window_length: 5

# The value N used to print top N queries. (requires stand_alone=True if N > 0)
print_top_queries: 0

# String encoding
# default: utf_8
encoding: utf_8

# String encoding error handling scheme.
# values: strict|ignore|replace
encoding_errors: replace

# Server ID
server_id: 1
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

# print top 5 queries (based on the count of canonicalized statement-hostname hash, in descending order)
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
# On another terminal, connect a mysql client to test capture
# Client was listening on lo interface, connect mysql client to loopback address
$ mysql -h 127.0.0.1

# Listen from interface 'eth0', filter packets by destination port 3306
$ ./sqlcanonclient.py -l -i eth0 -f dst port 3306
$ mysql -h 192.168.2.101
```

### Running Unit Tests
```
$ cd <sqlcanon_src_root_dir>/sqlcanonclient/src/sqlcanonclient
$ python -m unittest -v tests
```

Utilities
---------

### dosql.py (<root>/sqlcanonclient/src/sqlcanonclient/dosql.py)

This script creates random data that can be used for testing.
It can also perform selects to trigger MySQL logging.

#### Usage
```
usage: dosql.py [-h] [-H HOST] [-P PORT] [-u USER] [-p PASSWD] [-d DB]
                {inserts,selects}

positional arguments:
  {inserts,selects}     method to run.

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  db host (default: localhost)
  -P PORT, --port PORT  db port (default: None)
  -u USER, --user USER  db user (default: sandbox)
  -p PASSWD, --passwd PASSWD
                        db password (default: sandbox)
  -d DB, --db DB        db name (default: sandbox)
```

*Sample Usage*
```
# Perform inserts
$ ./dosql.py -H localhost -u sandbox -p sandbox -d sandbox inserts

# Perform selects
$ ./dosql.py -H localhost -u sandbox -p sandbox -d sandbox selects
```
