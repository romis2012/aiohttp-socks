# -*- coding: utf-8 -*-
import socket
from aiohttp import TCPConnector
from aiohttp.abc import AbstractResolver

from .proto import SocksVer
from .helpers import create_socket_wrapper, parse_socks_url


class NoResolver(AbstractResolver):
    async def resolve(self, host, port=0, family=socket.AF_INET):
        return [{'hostname': host,
                 'host': host, 'port': port,
                 'family': family, 'proto': 0,
                 'flags': 0}]

    async def close(self):
        pass


class SocksConnector(TCPConnector):
    def __init__(self, socks_ver=SocksVer.SOCKS5,
                 host=None, port=None,
                 username=None, password=None,
                 rdns=False, family=socket.AF_INET, **kwargs):

        if rdns:
            kwargs['resolver'] = NoResolver()

        super().__init__(**kwargs)

        self._sock = create_socket_wrapper(
            loop=self._loop,
            socks_ver=socks_ver, host=host, port=port,
            username=username, password=password, rdns=rdns, family=family)

    # noinspection PyMethodOverriding
    async def _wrap_create_connection(self, protocol_factory,
                                      host, port, **kwargs):

        await self._sock.connect((host, port))

        return await super()._wrap_create_connection(
            protocol_factory, None, None, sock=self._sock.socket, **kwargs)

    @classmethod
    def from_url(cls, url):
        socks_ver, host, port, username, password = parse_socks_url(url)
        return cls(socks_ver=socks_ver, host=host, port=port,
                   username=username, password=password)
