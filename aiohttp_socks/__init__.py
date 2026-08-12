__title__ = "aiohttp-socks"
__version__ = "0.12.0"

from python_socks import ProxyType

from ._deprecated import (
    SocksConnectionError,
    SocksConnector,
    SocksError,
    SocksVer,
)
from ._errors import (
    ProxyConnectionError,
    ProxyError,
    ProxyTimeoutError,
)
from .connector import ChainProxyConnector, ProxyConnector, ProxyInfo
from .utils import create_connection, open_connection

__all__ = (
    "ChainProxyConnector",
    "ProxyConnectionError",
    "ProxyConnector",
    "ProxyError",
    "ProxyInfo",
    "ProxyTimeoutError",
    "ProxyType",
    "SocksConnectionError",
    "SocksConnector",
    "SocksError",
    "SocksVer",
    "__title__",
    "__version__",
    "create_connection",
    "open_connection",
)
