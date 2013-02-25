Applications
============

sqlcanon - server, a Django web application
sqlcanonclient - a CLI application


sqlcanon
--------

### Installation of Requirements

Change directory to sqlcanon:
`$ cd sqlcanon`

Activate your virtual environment and install the project requirements:

In Ubuntu 12.04 you can use the bash script to install the project requirements including the required libraries for building PIL:
`(env)$ ./install_requirements.sh`
If you have a different OS, ensure first the PIL can find the required libraries for your OS, then run the following:
`(env)$ pip install -r requirements.txt`

### Database Initialization

Run the following commands:
`(env)$ python manage.py syncdb
(env)$ python manage.py migrate`

### Running

**To deploy it using a webserver**

sqlcanon is a Django project, to deploy it using a web server, please refer to Django documentation.

**To run it using the built-in server**

Syntax:
`python manage.py runserver [options] [optional port number, or ipaddr:port]`

Run with default:
`(env)$ python manage.py runserver`
The server will be accessible via: http://localhost:8000/

### Web pages

Homepage:
http://localhost:8000/

Admin page:
http://localhost:8000/admin/


sqlcanonclient
--------------

This application canonicalizes SQL statements (normalizes whitespace and quoting, normalizes IN() and VALUES() clauses) and can collect data about the statement and save locally or send them to sqlcanon server.

### Installation of Requirements

Go to sqlcanonclient source directory:
`(env)$ cd sqlcanonclient/src/sqlcanonclient`

Install requirements:
`(env)$ pip install -r requirements.txt`

### Sample Usages:

View options:
`(env)$ ./sqlcanonclient.py -h`

Launch packet sniffer and send data to server (run as root, privileges to capture packet data are required):
`(env)$ ./sqlcanonclient.py -l -i lo`

Listen from loopback interface, provide options for running EXPLAIN,:
`(env)$ ./sqlcanonclient.py -l -i lo -e h=127.0.0.1,u=root,p=pass`

Listen from loopback interface, provide options and ask password for running EXPLAIN,:
`(env)$ ./sqlcanonclient.py -l -i lo -e h=127.0.0.1,u=root,p`

Read MySQL slow-query log file:
`(env)$ ./sqlcanonclient.py /var/log/mysql/mysql-slow.log`

Read MySQL general query log file:
`(env)$ ./sqlcanonclient.py -t g /var/log/mysql/mysql.log`

Read MySQL general query log via stdin:
`(env)$ cat /var/log/mysql/mysql.log | ./sqlcanonclient.py -t g`


