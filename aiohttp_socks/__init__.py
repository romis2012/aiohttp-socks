# -*- coding: utf-8 -*-
from .proto import SocksVer
from .connector import SocksConnector
from .helpers import open_connection, create_connection
from .errors import (
    SocksError, NoAcceptableAuthMethods, UnknownAuthMethod,
    LoginAuthenticationFailed, InvalidServerVersion, InvalidServerReply,
    SocksConnectionError
)

__version__ = '0.2'

__all__ = ('SocksConnector', 'SocksVer',
           'SocksError', 'NoAcceptableAuthMethods', 'UnknownAuthMethod',
           'LoginAuthenticationFailed', 'InvalidServerVersion',
           'InvalidServerReply', 'SocksConnectionError', 'open_connection',
           'create_connection')
