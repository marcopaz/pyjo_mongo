#!/usr/bin/env python
from setuptools import setup, find_packages
import re

with open('pyjo_mongo/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)
if not version:
    raise RuntimeError('Cannot find version information')

setup(
    name='pyjo_mongo',
    version=version,
    description='Pyjo for MongoDB',
    url='https://github.com/marcopaz/pyjo_mongo',
    download_url='https://github.com/marcopaz/pyjo_mongo/archive/{}.tar.gz'.format(version),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Marco Pazzaglia',
    author_email='marco@pazzaglia.me',
    packages=find_packages(),
    package_data={'': ['LICENSE']},
    test_suite="tests",
    install_requires=[
        'pyjo',
        'pymongo',
    ],
)
