#!/usr/bin/env python
import os
import re
import sys

from setuptools import setup

if sys.version_info < (3, 6, 0):
    raise RuntimeError('aiohttp-socks requires Python 3.6+')


def get_version():
    here = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(here, 'aiohttp_socks', '__init__.py')
    contents = open(filename).read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


def get_long_description():
    with open('README.md', mode='r', encoding='utf8') as f:
        return f.read()


setup(
    name='aiohttp_socks',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=get_version(),
    license='Apache 2',
    url='https://github.com/romis2012/aiohttp-socks',
    description='Proxy connector for aiohttp',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    packages=['aiohttp_socks'],
    keywords='asyncio aiohttp socks socks5 socks4 http proxy',
    install_requires=[
        'aiohttp>=2.3.2',
        'python-socks[asyncio]>=2.4.3,<3.0.0',
    ],
)
