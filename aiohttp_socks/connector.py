import socket
import warnings
from typing import Iterable

import attr
from aiohttp import TCPConnector
from aiohttp.abc import AbstractResolver
from aiohttp.helpers import CeilTimeout  # noqa

from .proxy import (ProxyType, SocksVer, ChainProxy,
                    parse_proxy_url, create_proxy)


class NoResolver(AbstractResolver):
    async def resolve(self, host, port=0, family=socket.AF_INET):
        return [{'hostname': host,
                 'host': host, 'port': port,
                 'family': family, 'proto': 0,
                 'flags': 0}]

    async def close(self):
        pass  # pragma: no cover


class SocksConnector(TCPConnector):  # pragma: no cover
    def __init__(self, socks_ver=SocksVer.SOCKS5,
                 host=None, port=None,
                 username=None, password=None,
                 rdns=False, family=socket.AF_INET, **kwargs):

        warnings.warn('SocksConnector is deprecated. '
                      'Use ProxyConnector instead.', DeprecationWarning,
                      stacklevel=2)
        if rdns:
            kwargs['resolver'] = NoResolver()

        super().__init__(**kwargs)

        self._socks_ver = socks_ver
        self._socks_host = host
        self._socks_port = port
        self._socks_username = username
        self._socks_password = password
        self._rdns = rdns
        self._socks_family = family

    # noinspection PyMethodOverriding
    async def _wrap_create_connection(self, protocol_factory,
                                      host, port, **kwargs):

        proxy = create_proxy(
            loop=self._loop,
            proxy_type=ProxyType(self._socks_ver),
            host=self._socks_host, port=self._socks_port,
            username=self._socks_username, password=self._socks_password,
            rdns=self._rdns, family=self._socks_family)

        timeout = kwargs.get('timeout')
        if timeout is not None and hasattr(timeout, 'sock_connect'):
            with CeilTimeout(timeout.sock_connect):
                await proxy.connect(host, port)
        else:
            await proxy.connect(host, port)

        return await super()._wrap_create_connection(
            protocol_factory, None, None, sock=proxy.socket, **kwargs)

    @classmethod
    def from_url(cls, url, **kwargs):
        proxy_type, host, port, username, password = parse_proxy_url(url)

        if proxy_type not in (ProxyType.SOCKS4, ProxyType.SOCKS5):
            raise ValueError('Invalid proxy_type: {}'.format(proxy_type))

        return cls(socks_ver=proxy_type.value, host=host, port=port,
                   username=username, password=password, **kwargs)


class ProxyConnector(TCPConnector):
    def __init__(self, proxy_type=ProxyType.SOCKS5,
                 host=None, port=None,
                 username=None, password=None,
                 rdns=None, family=None, **kwargs):

        kwargs['resolver'] = NoResolver()
        super().__init__(**kwargs)

        self._proxy_type = proxy_type
        self._proxy_host = host
        self._proxy_port = port
        self._proxy_username = username
        self._proxy_password = password
        self._rdns = rdns
        self._proxy_family = family

    # noinspection PyMethodOverriding
    async def _wrap_create_connection(self, protocol_factory,
                                      host, port, **kwargs):
        # aiohttp calls this method for each http request
        proxy = create_proxy(
            loop=self._loop,
            proxy_type=self._proxy_type,
            host=self._proxy_host, port=self._proxy_port,
            username=self._proxy_username, password=self._proxy_password,
            rdns=self._rdns, family=self._proxy_family)

        timeout = kwargs.get('timeout')
        if timeout is not None and hasattr(timeout, 'sock_connect'):
            with CeilTimeout(timeout.sock_connect):
                await proxy.connect(host, port)
        else:
            await proxy.connect(host, port)

        return await super()._wrap_create_connection(
            protocol_factory, None, None, sock=proxy.socket, **kwargs)

    @classmethod
    def from_url(cls, url, **kwargs):
        proxy_type, host, port, username, password = parse_proxy_url(url)
        return cls(proxy_type=proxy_type, host=host, port=port,
                   username=username, password=password, **kwargs)


@attr.s(frozen=True, slots=True)
class ProxyInfo:
    proxy_type = attr.ib(type=ProxyType)
    host = attr.ib(type=str)
    port = attr.ib(type=int)
    username = attr.ib(type=str, default=None)
    password = attr.ib(type=str, default=None)
    rdns = attr.ib(type=bool, default=None)
    family = attr.ib(type=int, default=None)


class ChainProxyConnector(TCPConnector):
    def __init__(self, proxy_infos: Iterable[ProxyInfo], **kwargs):
        kwargs['resolver'] = NoResolver()
        super().__init__(**kwargs)

        self._proxy_infos = proxy_infos

    # noinspection PyMethodOverriding
    async def _wrap_create_connection(self, protocol_factory,
                                      host, port, **kwargs):
        proxies = []
        for info in self._proxy_infos:
            proxy = create_proxy(
                proxy_type=info.proxy_type,
                host=info.host,
                port=info.port,
                username=info.username,
                password=info.password,
                rdns=info.rdns,
                family=info.family,
                loop=self._loop
            )
            proxies.append(proxy)

        proxy = ChainProxy(proxies)

        await proxy.connect(host, port)

        return await super()._wrap_create_connection(
            protocol_factory, None, None, sock=proxy.socket, **kwargs)

    @classmethod
    def from_urls(cls, urls: Iterable[str], **kwargs):
        infos = []
        for url in urls:
            proxy_type, host, port, username, password = parse_proxy_url(url)
            proxy_info = ProxyInfo(
                proxy_type=proxy_type,
                host=host,
                port=port,
                username=username,
                password=password
            )
            infos.append(proxy_info)

        return cls(infos, **kwargs)
