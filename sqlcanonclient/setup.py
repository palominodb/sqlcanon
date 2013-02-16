#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name='sqlcanonclient',
    version='0.1',
    package_dir={'':'src'},
    packages=find_packages('src'),
    dependency_links=[
        'http://sourceforge.net/projects/pylibpcap/files/pylibpcap/0.6.4/pylibpcap-0.6.4.tar.gz/download#egg=pylibpcap-0.6.4'
    ],
    install_requires=[
        'MySQL-python==1.2.4',
        'sqlparse==0.1.6',
        'mmh3==2.0',
        'construct==2.06',
        'pylibpcap==0.6.4'],
    entry_points={
        'console_scripts': [
            'sqlcanonclient = sqlcanonclient.sqlcanonclient:main',
        ]
    }
    #scripts=[
    #    'src/sqlcanonclient/sqlcanonclient.py',
    #],
)
