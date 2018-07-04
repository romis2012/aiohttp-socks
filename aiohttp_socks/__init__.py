# -*- coding: utf-8 -*-
from .proto import SocksVer
from .connector import SocksConnector
from .errors import (
    SocksError, NoAcceptableAuthMethods, UnknownAuthMethod,
    LoginAuthenticationFailed, InvalidServerVersion, InvalidServerReply,
    SocksConnectionError
)

__version__ = '0.1.0'

__all__ = ('SocksConnector', 'SocksVer',
           'SocksError', 'NoAcceptableAuthMethods', 'UnknownAuthMethod',
           'LoginAuthenticationFailed', 'InvalidServerVersion',
           'InvalidServerReply', 'SocksConnectionError')
