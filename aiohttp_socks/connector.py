import socket
from typing import Iterable

import attr
from aiohttp import TCPConnector
from aiohttp.abc import AbstractResolver

from python_socks import ProxyType, parse_proxy_url
from python_socks.async_ import ProxyChain
from python_socks.async_.asyncio import Proxy


class NoResolver(AbstractResolver):
    async def resolve(self, host, port=0, family=socket.AF_INET):
          """
          Resolve host

          Args:
              self: (todo): write your description
              host: (str): write your description
              port: (int): write your description
              family: (str): write your description
              socket: (todo): write your description
              AF_INET: (int): write your description
          """
        return [{'hostname': host,
                 'host': host, 'port': port,
                 'family': family, 'proto': 0,
                 'flags': 0}]

    async def close(self):
          """
          Closes the connection.

          Args:
              self: (todo): write your description
          """
        pass  # pragma: no cover


class ProxyConnector(TCPConnector):
    def __init__(self, proxy_type=ProxyType.SOCKS5,
                 host=None, port=None,
                 username=None, password=None,
                 rdns=None, **kwargs):
        """
        Initialize the proxy

        Args:
            self: (todo): write your description
            proxy_type: (str): write your description
            ProxyType: (str): write your description
            SOCKS5: (todo): write your description
            host: (str): write your description
            port: (int): write your description
            username: (str): write your description
            password: (str): write your description
            rdns: (int): write your description
        """
        kwargs['resolver'] = NoResolver()
        super().__init__(**kwargs)

        self._proxy_type = proxy_type
        self._proxy_host = host
        self._proxy_port = port
        self._proxy_username = username
        self._proxy_password = password
        self._rdns = rdns

    # noinspection PyMethodOverriding
    async def _wrap_create_connection(self, protocol_factory,
                                      host, port, **kwargs):
          """
          Establish a connection to a redis server.

          Args:
              self: (todo): write your description
              protocol_factory: (todo): write your description
              host: (str): write your description
              port: (int): write your description
          """
        proxy = Proxy.create(
            proxy_type=self._proxy_type,
            host=self._proxy_host,
            port=self._proxy_port,
            username=self._proxy_username,
            password=self._proxy_password,
            rdns=self._rdns,
            loop=self._loop,
        )

        connect_timeout = None

        timeout = kwargs.get('timeout')
        if timeout is not None:
            connect_timeout = getattr(timeout, 'sock_connect', None)

        sock = await proxy.connect(host, port, timeout=connect_timeout)

        return await super()._wrap_create_connection(
            protocol_factory,
            None,
            None,
            sock=sock,
            **kwargs
        )

    @classmethod
    def from_url(cls, url, **kwargs):
        """
        Create a new http : class from a url.

        Args:
            cls: (todo): write your description
            url: (str): write your description
        """
        proxy_type, host, port, username, password = parse_proxy_url(url)
        return cls(
            proxy_type=proxy_type,
            host=host,
            port=port,
            username=username,
            password=password,
            **kwargs
        )


@attr.s(frozen=True, slots=True)
class ProxyInfo:
    proxy_type = attr.ib(type=ProxyType)
    host = attr.ib(type=str)
    port = attr.ib(type=int)
    username = attr.ib(type=str, default=None)
    password = attr.ib(type=str, default=None)
    rdns = attr.ib(type=bool, default=None)


class ChainProxyConnector(TCPConnector):
    def __init__(self, proxy_infos: Iterable[ProxyInfo], **kwargs):
        """
        Initialize the proxy

        Args:
            self: (todo): write your description
            proxy_infos: (todo): write your description
        """
        kwargs['resolver'] = NoResolver()
        super().__init__(**kwargs)

        self._proxy_infos = proxy_infos

    # noinspection PyMethodOverriding
    async def _wrap_create_connection(self, protocol_factory,
                                      host, port, **kwargs):
          """
          Establish a connection to the http connection.

          Args:
              self: (todo): write your description
              protocol_factory: (todo): write your description
              host: (str): write your description
              port: (int): write your description
          """
        proxies = []
        for info in self._proxy_infos:
            proxy = Proxy.create(
                proxy_type=info.proxy_type,
                host=info.host,
                port=info.port,
                username=info.username,
                password=info.password,
                rdns=info.rdns,
                loop=self._loop
            )
            proxies.append(proxy)

        proxy = ProxyChain(proxies)

        connect_timeout = None

        timeout = kwargs.get('timeout')
        if timeout is not None:
            connect_timeout = getattr(timeout, 'sock_connect', None)

        sock = await proxy.connect(host, port, timeout=connect_timeout)

        return await super()._wrap_create_connection(
            protocol_factory,
            None,
            None,
            sock=sock,
            **kwargs
        )

    @classmethod
    def from_urls(cls, urls: Iterable[str], **kwargs):
        """
        Create a new proxy from a urllib.

        Args:
            cls: (todo): write your description
            urls: (str): write your description
        """
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
