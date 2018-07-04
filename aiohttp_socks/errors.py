# -*- coding: utf-8 -*-
class SocksError(Exception):
    pass


class NoAcceptableAuthMethods(SocksError):
    pass


class UnknownAuthMethod(SocksError):
    pass


class LoginAuthenticationFailed(SocksError):
    pass


class InvalidServerVersion(SocksError):
    pass


class InvalidServerReply(SocksError):
    pass


class SocksConnectionError(OSError):
    pass
