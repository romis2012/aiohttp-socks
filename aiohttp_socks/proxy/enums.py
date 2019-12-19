from enum import Enum


class SocksVer(object):
    SOCKS4 = 1
    SOCKS5 = 2


class ProxyType(Enum):
    SOCKS4 = 1
    SOCKS5 = 2
    HTTP = 3
