# -*- coding: utf-8 -*-
import asyncio
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


async def open_connection(socks_url=None, host=None, port=None, *,
                          socks_ver=SocksVer.SOCKS5,
                          socks_host='127.0.0.1', socks_port=1080,
                          username=None, password=None, rdns=True,
                          family=socket.AF_INET,
                          loop=None, **kwargs):
    if host is None or port is None:
        raise ValueError('host and port must be specified')

    if loop is None:
        loop = asyncio.get_event_loop()

    if socks_url is not None:
        socks_ver, socks_host, socks_port, username, password \
            = parse_socks_url(socks_url)

    sock = create_socket_wrapper(
        loop=loop,
        socks_ver=socks_ver, host=socks_host, port=socks_port,
        username=username, password=password, rdns=rdns, family=family)

    await sock.connect((host, port))

    return await asyncio.open_connection(
        loop=loop, host=None, port=None, sock=sock.socket, **kwargs)


async def create_connection(socks_url=None, protocol_factory=None,
                            host=None, port=None, *,
                            socks_ver=SocksVer.SOCKS5,
                            socks_host='127.0.0.1', socks_port=1080,
                            username=None, password=None, rdns=True,
                            family=socket.AF_INET,
                            loop=None, **kwargs):
    if protocol_factory is None:
        raise ValueError('protocol_factory must be specified')

    if host is None or port is None:
        raise ValueError('host and port must be specified')

    if loop is None:
        loop = asyncio.get_event_loop()

    if socks_url is not None:
        socks_ver, socks_host, socks_port, username, password \
            = parse_socks_url(socks_url)

    sock = create_socket_wrapper(
        loop=loop,
        socks_ver=socks_ver, host=socks_host, port=socks_port,
        username=username, password=password, rdns=rdns, family=family)

    await sock.connect((host, port))

    return await loop.create_connection(
        protocol_factory=protocol_factory,
        host=None, port=None, sock=sock.socket, **kwargs)
