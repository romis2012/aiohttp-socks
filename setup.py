#!/usr/bin/env python
import codecs
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = None

with codecs.open(os.path.join(os.path.abspath(os.path.dirname(
        __file__)), 'aiohttp_socks', '__init__.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

if sys.version_info < (3, 5, 3):
    raise RuntimeError("aiohttp_socks requires Python 3.5.3+")

with open('README.md') as f:
    long_description = f.read()

setup(
    name='aiohttp_socks',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=version,
    license='Apache 2',
    url='https://github.com/romis2012/aiohttp-socks',
    description='Proxy connector for aiohttp',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['aiohttp_socks', 'aiohttp_socks.proxy'],
    keywords='asyncio aiohttp socks socks5 socks4 http proxy',
    install_requires=[
        'aiohttp>=2.3.2',
        'attrs>=19.2.0',
    ],
)
