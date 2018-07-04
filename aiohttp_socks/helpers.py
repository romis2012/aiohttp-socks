# -*- coding: utf-8 -*-
import socket
from urllib.parse import urlparse, unquote

from .proto import SocksVer, Socks4SocketWrapper, Socks5SocketWrapper


def create_socket_wrapper(loop, socks_ver, host=None, port=None,
                          username=None, password=None,
                          rdns=True, family=socket.AF_INET):
    if socks_ver == SocksVer.SOCKS4:
        return Socks4SocketWrapper(
            loop=loop, host=host, port=port,
            user_id=username, rdns=rdns)

    if socks_ver == SocksVer.SOCKS5:
        return Socks5SocketWrapper(
            loop=loop, host=host, port=port,
            username=username, password=password, rdns=rdns, family=family)

    raise ValueError('Invalid socks ver: %s' % socks_ver)


def parse_socks_url(url):
    parsed = urlparse(url)

    scheme = parsed.scheme
    if scheme == 'socks5':
        socks_ver = SocksVer.SOCKS5
    elif scheme == 'socks4':
        socks_ver = SocksVer.SOCKS4
    else:
        raise ValueError('Invalid scheme component: %s' % scheme)

    host = parsed.hostname
    if not host:
        raise ValueError('Empty host component')

    try:
        port = parsed.port
    except (ValueError, TypeError):
        raise ValueError('Invalid port component')

    try:
        username, password = (unquote(parsed.username),
                              unquote(parsed.password))
    except (AttributeError, TypeError):
        username, password = '', ''

    return socks_ver, host, port, username, password
