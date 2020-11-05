import warnings

from python_socks import (
    ProxyError,
    ProxyConnectionError,
    ProxyType
)

from .connector import ProxyConnector


class SocksVer(object):
    SOCKS4 = 1
    SOCKS5 = 2


def _warn_about_connector():
    """
    Deprecated. use : func.

    Args:
    """
    warnings.warn('SocksConnector is deprecated. '
                  'Use ProxyConnector instead.', DeprecationWarning,
                  stacklevel=3)


class SocksConnector(ProxyConnector):
    def __init__(self, socks_ver=SocksVer.SOCKS5, **kwargs):
        """
        Initialize the proxy

        Args:
            self: (todo): write your description
            socks_ver: (todo): write your description
            SocksVer: (todo): write your description
            SOCKS5: (todo): write your description
        """
        _warn_about_connector()  # noqa

        if 'proxy_type' in kwargs:  # from_url
            super().__init__(**kwargs)
        else:
            super().__init__(proxy_type=ProxyType(socks_ver), **kwargs)

    @classmethod
    def from_url(cls, url, **kwargs):
        """
        Create a connection from a url.

        Args:
            cls: (todo): write your description
            url: (str): write your description
        """
        _warn_about_connector()  # noqa
        return super().from_url(url, **kwargs)


SocksError = ProxyError
SocksConnectionError = ProxyConnectionError
