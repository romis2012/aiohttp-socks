# -*- coding: utf-8 -*-
import socket
from aiohttp import TCPConnector

from .proto import SocksVer
from .helpers import create_socket_wrapper, parse_socks_url


class SocksConnector(TCPConnector):
    def __init__(self, socks_ver=SocksVer.SOCKS5,
                 host=None, port=None,
                 username=None, password=None,
                 rdns=True, family=socket.AF_INET, **kwargs):
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
