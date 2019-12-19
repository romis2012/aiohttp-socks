import asyncio
import socket

from .proxy import (
    ProxyType,
    SocksVer,
    create_proxy,
    parse_socks_url
)


async def open_connection(socks_url=None, host=None, port=None, *,
                          socks_ver=SocksVer.SOCKS5,
                          socks_host='127.0.0.1', socks_port=1080,
                          username=None, password=None, rdns=True,
                          family=socket.AF_INET,
                          loop=None, **kwargs):
    if host is None or port is None:
        raise ValueError('host and port must be specified')  # pragma: no cover

    if loop is None:
        loop = asyncio.get_event_loop()

    if socks_url is not None:
        socks_ver, socks_host, socks_port, username, password \
            = parse_socks_url(socks_url)

    proxy = create_proxy(
        loop=loop,
        proxy_type=ProxyType(socks_ver), host=socks_host, port=socks_port,
        username=username, password=password, rdns=rdns, family=family)

    await proxy.connect(host, port)

    # noinspection PyTypeChecker
    return await asyncio.open_connection(
        loop=loop, host=None, port=None, sock=proxy.socket, **kwargs)


async def create_connection(socks_url=None, protocol_factory=None,
                            host=None, port=None, *,
                            socks_ver=SocksVer.SOCKS5,
                            socks_host='127.0.0.1', socks_port=1080,
                            username=None, password=None, rdns=True,
                            family=socket.AF_INET,
                            loop=None, **kwargs):
    if protocol_factory is None:
        raise ValueError('protocol_factory '
                         'must be specified')  # pragma: no cover

    if host is None or port is None:
        raise ValueError('host and port '
                         'must be specified')  # pragma: no cover

    if loop is None:
        loop = asyncio.get_event_loop()

    if socks_url is not None:
        socks_ver, socks_host, socks_port, username, password \
            = parse_socks_url(socks_url)

    proxy = create_proxy(
        loop=loop,
        proxy_type=ProxyType(socks_ver), host=socks_host, port=socks_port,
        username=username, password=password, rdns=rdns, family=family)

    await proxy.connect(host, port)

    return await loop.create_connection(
        protocol_factory=protocol_factory,
        host=None, port=None, sock=proxy.socket, **kwargs)
