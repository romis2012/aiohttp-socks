## aiohttp-socks

SOCKS proxy connector for [aiohttp](https://github.com/aio-libs/aiohttp). SOCKS4(a) and SOCKS5 are supported.

## Requirements
- Python >= 3.5.3
- aiohttp >= 2.3.2  # including v3.x

## Installation
```
pip install aiohttp_socks
```

## Usage

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
    #     password='password'
    # )
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as response:
            return await response.text()
```

#### Why yet another SOCKS connector for aiohttp

Unlike [aiosocksy](https://github.com/romis2012/aiosocksy)/[aiosocks](https://github.com/nibrag/aiosocks) , aiohttp_socks has only single point of integration with aiohttp. 
This makes it easier to maintain compatibility with new aiohttp versions.


