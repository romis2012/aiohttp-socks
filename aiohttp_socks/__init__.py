__title__ = 'aiohttp-socks'
__version__ = '0.4.1'

from .proxy import SocksVer, ProxyType
from .connector import (
    SocksConnector, ProxyConnector,
    ChainProxyConnector, ProxyInfo
)
from .utils import open_connection, create_connection
from .proxy.errors import (
    ProxyError, ProxyConnectionError, ProxyTimeoutError,
    SocksError, SocksConnectionError,
)

__all__ = (
    '__title__',
    '__version__',
    'SocksConnector',
    'ProxyConnector',
    'ChainProxyConnector',
    'ProxyInfo',
    'SocksVer',
    'ProxyType',
    'ProxyError',
    'ProxyConnectionError',
    'ProxyTimeoutError',
    'SocksError',
    'SocksConnectionError',
    'open_connection',
    'create_connection'
)
