#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import os.path
import sys

sys.path.insert(0, os.path.abspath('.'))

setup(
    name='enaml_coverage_plugin',
    author_email='m.dartiailh@gmail.com',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ],
    zip_safe=False,
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={'': ['*.enaml', '*.txt']},
)
