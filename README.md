## aiohttp-socks

[![Build Status](https://travis-ci.org/romis2012/aiohttp-socks.svg?branch=master)](https://travis-ci.org/romis2012/aiohttp-socks)
[![Coverage Status](https://coveralls.io/repos/github/romis2012/aiohttp-socks/badge.svg?branch=master)](https://coveralls.io/github/romis2012/aiohttp-socks?branch=master)
[![PyPI version](https://badge.fury.io/py/aiohttp-socks.svg)](https://badge.fury.io/py/aiohttp-socks)

SOCKS proxy connector for [aiohttp](https://github.com/aio-libs/aiohttp). SOCKS4(a) and SOCKS5 are supported.

## Requirements
- Python >= 3.5.3
- aiohttp >= 2.3.2  # including v3.x

## Installation
```
pip install aiohttp_socks
```

## Usage

#### aiohttp usage:
```python
import aiohttp
from aiohttp_socks import SocksConnector, SocksVer


async def fetch(url):
    connector = SocksConnector.from_url('socks5://user:password@127.0.0.1:1080')
    ### or use SocksConnector constructor
    # connector = SocksConnector(
    #     socks_ver=SocksVer.SOCKS5,
    #     host='127.0.0.1',
    #     port=1080,
    #     username='user',
    #     password='password',
    #     rdns=True
    # )
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as response:
            return await response.text()
```

#### aiohttp-socks also provides `open_connection` and `create_connection` functions:

```python
from aiohttp_socks import open_connection

async def fetch():
    reader, writer = await open_connection(
        socks_url='socks5://user:password@127.0.0.1:1080',
        host='check-host.net',
        port=80
    )
    request = (b"GET /ip HTTP/1.1\r\n"
               b"Host: check-host.net\r\n"
               b"Connection: close\r\n\r\n")

    writer.write(request)
    return await reader.read(-1)
```

## Why yet another SOCKS connector for aiohttp

Unlike [aiosocksy](https://github.com/romis2012/aiosocksy), aiohttp_socks has only single point of integration with aiohttp. 
This makes it easier to maintain compatibility with new aiohttp versions.


