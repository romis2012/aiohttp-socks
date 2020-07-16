__title__ = 'aiohttp-socks'
__version__ = '0.5.1'

from .core_socks import (
    ProxyError,
    ProxyTimeoutError,
    ProxyConnectionError,
    ProxyType
)

from .connector import (
    ProxyConnector,
    ChainProxyConnector,
    ProxyInfo
)
from .utils import open_connection, create_connection

__all__ = (
    '__title__',
    '__version__',
    'ProxyConnector',
    'ChainProxyConnector',
    'ProxyInfo',
    'ProxyType',
    'ProxyError',
    'ProxyConnectionError',
    'ProxyTimeoutError',
    'open_connection',
    'create_connection'
)
