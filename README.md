sqlcanon
========

Canonicalize SQL statements
-- normalize whitespace and quoting
-- normalize IN() and VALUES() clauses


Notes
=====

** Locations **

sqlcanon - server/Django web application
sqlcanonclient - sqlcanon client setup and source files

** Installation of requirements **

$ pip install -r requirements.txt

It is recommended to create a virtual environment and install the requirements there.

** Database initialization **

$ python manage.py syncdb
$ python manage.py migrate

** To run built-in http server to accept statements captured by sqlcanonclient: **

$ python manage.py runserver

** To run sniffer: **

$ sudo python sqlcanonclient.py --sniff --interface <interface> --filter <filter>

Example: $ sudo python sqlcanonclient.py --sniff --interface lo --filter="dst port 3306"

Note: To execute EXPLAIN statements, supply values for:
      --mysql-host, --mysql-db, --mysql-user, --mysql-password

Try connecting to mysql and try some statements: $ mysql -h 127.0.0.1 -u <user>

** Web app pages **

The homepage contains link to view info about captured statements: http://localhost:8000/

** Management console commands **

Most stuff that was previously on sqlcanon.py has been converted as Django management console command.

See command help for info:

$ python manage.py canonicalize -h
