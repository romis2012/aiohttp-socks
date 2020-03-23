class ProxyError(Exception):
    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code


class ProxyConnectionError(OSError):
    pass


SocksError = ProxyError
SocksConnectionError = ProxyConnectionError
