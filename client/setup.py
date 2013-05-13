#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name='sqlcanonclient',
    version='0.1',
    packages=find_packages(),
    dependency_links=[
        'http://sourceforge.net/projects/pylibpcap/files/pylibpcap/0.6.4/pylibpcap-0.6.4.tar.gz/download#egg=pylibpcap-0.6.4'
    ],
    install_requires=[
        'argparse>=1.2.1',
        'MySQL-python>=1.2.4',
        'sqlparse>=0.1.7',
        'mmh3>=2.2',
        'construct>=2.5.1',
        'pylibpcap==0.6.4',
        'PyYAML>=3.10',
        'python-dateutil>=1.5,!=2.0'],
    entry_points={
        'console_scripts': [
            'sqlcanonclient = sqlcanonclient.sqlcanonclient:main',
        ]
    }
)
