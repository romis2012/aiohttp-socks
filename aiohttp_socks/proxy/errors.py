class ProxyError(Exception):
    pass


class ProxyConnectionError(OSError):
    pass


SocksError = ProxyError
SocksConnectionError = ProxyConnectionError
