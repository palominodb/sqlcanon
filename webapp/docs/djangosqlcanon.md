Sqlcanon Web Application Component
==================================

The web application component is a Django-based web application that allows viewing of stored info about SQL statements. It also exposes APIs that receives data from the client component, for storage.


Requirements
------------

It is recommended to install the the web application and its requirements in an isolated Python environments.
virtualenv is a tool that can create such environments.

To install virtualenv:
```
$ pip install virtualenv
```

To create a virtual environment:
```
$ virtualenv venv --no-site-packages
```

To being using the virtual environment, it needs to be activated:
```
$ source venv/bin/activate
```
At this point, you can begin installing any new modules without affecting the system default Python or other virtual environments.

If you are done working in the virtual environment, you can deactivate it:
```
$ deactivate
```

The requirements.txt file contains the required components for the
web applicaton.

To install the requirements, run the following inside a virtual environment:
```
$ pip install -r requirements.txt
```

Note:
    stable-requirements.txt is also provided and can be used instead of requirements.txt if newer versions of packages causes issues.

    In Ubuntu Linux (tested on version 12.04), PIL does not build correctly due to missing files from expected locations.  A script has been provided to create symlinks. To run the script:
    ```
    $ ./install_requirements.sh
    ```


Setup
-----

### Configuration

Copy (webapp_root)/djangosqlcanon/djangosqlcanon/sample.local_settings.py to (webapp_root)/djangosqlcanon/djangosqlcanon/local_settings.py and edit the contents of the new file.  Provided correct values for each setting especially DATABASES. The comments for each setting will give you an idea about its purpose.

You will usually need to modify the DATABASES settings and provide values that are needed by the application to connect successfully to a database.  You can also use local_settings.py to override the default settings that are included in (webapp_root)djangosqlcanon/djangosqlcanon/settings.py.


### Database Initialization

To prepare the database for use:
```
$ cd (webapp_root)/djangosqlcanon/djangosqlcanon/
$ ./manage.py syncdb
```
Enter password when prompted, and continue with:
```
$ ./manage.py migrate
```


Running
-------

To start the web application's built-in HTTP server:
```
$ cd <webapp_root>/djangosqlcanon/
$ ./manage.py runserver [optional port number, or ipaddr:port]
```


Usage
-----

Browse to the URL where the server is running at, for example:
```
http://localhost:8000/
```
The startup page will present a view that allows the user to view explained statements, top queries based on selected filters, and last statement found within the provided number of minutes.
