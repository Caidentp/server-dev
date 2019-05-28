#!/usr/bin/python

""""""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst'), 'r') as f:
    long_description = f.read()


setup(
    name='server-dev',

    version='1.0.0',

    description='',
    long_description=long_description,

    url='',
    project_urls={
        'Documentation': 'https://caidenpyle.com/api_docs'
    },

    author='Caiden Pyle',
    author_email='caiden.pyle@netapp.com',

    license='MIT',

    classifiers=[
        'Development Status :: 1 - Planning',

        'Operating System :: POSIX :: Linux',

        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',

        'Topic :: Utilities',
        'Topic :: System :: Systems Administration',
        'Topic :: Software Development :: Libraries :: Application Frameworks',

        'License :: Freeware',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],

    keywords='solidfire iscsi fibre channel storage api',

    packages=['serverdev'],
)
