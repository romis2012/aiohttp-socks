class ProxyError(Exception):
    pass


class NoAcceptableAuthMethods(ProxyError):
    pass


class UnknownAuthMethod(ProxyError):
    pass


class LoginAuthenticationFailed(ProxyError):
    pass


class InvalidServerVersion(ProxyError):
    pass


class InvalidServerReply(ProxyError):
    pass


class ProxyConnectionError(OSError):
    pass


SocksError = ProxyError
SocksConnectionError = ProxyConnectionError
