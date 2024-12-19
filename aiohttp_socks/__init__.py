__title__ = 'aiohttp-socks'
__version__ = '0.9.1'

from python_socks import (  # type: ignore
    ProxyConnectionError,
    ProxyError,
    ProxyTimeoutError,
    ProxyType,
)

from .connector import ChainProxyConnector, ProxyConnector, ProxyInfo

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
)
