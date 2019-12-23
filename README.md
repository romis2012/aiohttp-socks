## aiohttp-socks

[![Build Status](https://travis-ci.org/romis2012/aiohttp-socks.svg?branch=master)](https://travis-ci.org/romis2012/aiohttp-socks)
[![Coverage Status](https://coveralls.io/repos/github/romis2012/aiohttp-socks/badge.svg?branch=master&_=x)](https://coveralls.io/github/romis2012/aiohttp-socks?branch=master)
[![PyPI version](https://badge.fury.io/py/aiohttp-socks.svg)](https://badge.fury.io/py/aiohttp-socks)

Proxy connector for [aiohttp](https://github.com/aio-libs/aiohttp). 
SOCKS4(a), SOCKS5, HTTP (tunneling), Proxy chains are supported.

## Requirements
- Python >= 3.5.3
- aiohttp >= 2.3.2

## Installation
```
pip install aiohttp_socks
```

## Usage

#### aiohttp usage:
```python
import aiohttp
from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector


async def fetch(url):
    # We have added http proxy support, so SocksConnector has been deprecated
    # connector = SocksConnector.from_url('socks5://user:password@127.0.0.1:1080')
    connector = ProxyConnector.from_url('socks5://user:password@127.0.0.1:1080')
    
    ### or use ProxyConnector constructor
    # connector = ProxyConnector(
    #     proxy_type=ProxyType.SOCKS5,
    #     host='127.0.0.1',
    #     port=1080,
    #     username='user',
    #     password='password',
    #     rdns=True
    # )
    
    ### proxy chaining (since ver 0.3.3)
    # connector = ChainProxyConnector.from_urls([
    #     'socks5://user:password@127.0.0.1:1080',
    #     'socks4://127.0.0.1:1081',
    #     'http://user:password@127.0.0.1:3128',
    # ])
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as response:
            return await response.text()
```

#### aiohttp-socks also provides `open_connection` and `create_connection` functions:

```python
from aiohttp_socks import open_connection

async def fetch():
    reader, writer = await open_connection(
        proxy_url='socks5://user:password@127.0.0.1:1080',
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


