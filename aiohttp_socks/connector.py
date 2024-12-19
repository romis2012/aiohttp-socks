import asyncio
import socket
import ssl
from asyncio import StreamWriter
from typing import Any, Iterable, List, NamedTuple, Optional, Tuple, Union, cast

import aiohappyeyeballs
from aiohttp import ClientRequest, ClientTimeout, Fingerprint, TCPConnector
from aiohttp.abc import AbstractResolver, ResolveResult
from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError
from aiohttp.client_proto import ResponseHandler
from aiohttp.connector import SSLContext
from aiohttp.helpers import sentinel
from python_socks import ProxyType, parse_proxy_url  # type: ignore
from python_socks.async_.asyncio.v2 import Proxy  # type: ignore


class NoResolver(AbstractResolver):
    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,  # pylint: disable=no-member
    ) -> list[ResolveResult]:
        return [
            {
                'hostname': host,
                'host': host,
                'port': port,
                'family': family,
                'proto': 0,
                'flags': 0,
            }
        ]

    async def close(self):
        pass  # pragma: no cover


class _ResponseHandler(ResponseHandler):
    """
    To fix issue https://github.com/romis2012/aiohttp-socks/issues/27
    In Python>=3.11.5 we need to keep a reference to the StreamWriter
    so that the underlying transport is not closed during garbage collection.
    See StreamWriter.__del__ method (was added in Python 3.11.5)
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, writer: StreamWriter) -> None:
        super().__init__(loop)
        self._writer = writer


class ProxyConnector(TCPConnector):
    def __init__(
        self,
        host: str,
        port: int,
        proxy_type: ProxyType = ProxyType.SOCKS5,
        username: str = "",
        password: str = "",
        rdns: bool = True,
        proxy_ssl: Optional[ssl.SSLContext] = None,
        *,
        verify_ssl: bool = True,
        fingerprint: Optional[bytes] = None,
        use_dns_cache: bool = True,
        ttl_dns_cache: Optional[int] = 10,
        family: socket.AddressFamily = socket.AddressFamily.AF_UNSPEC,  # pylint: disable=no-member
        ssl_context: Optional[SSLContext] = None,
        ssl: Union[bool, Fingerprint, SSLContext] = True,  # pylint: disable=redefined-outer-name
        local_addr: Optional[Tuple[str, int]] = None,
        resolver: Optional[AbstractResolver] = None,
        keepalive_timeout: Union[None, float, object] = sentinel,
        force_close: bool = False,
        limit: int = 100,
        limit_per_host: int = 0,
        enable_cleanup_closed: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        timeout_ceil_threshold: float = 5,
        happy_eyeballs_delay: Optional[float] = 0.25,
        interleave: Optional[int] = None,
    ):
        resolver = NoResolver()
        super().__init__(
            verify_ssl=verify_ssl,
            fingerprint=fingerprint,
            use_dns_cache=use_dns_cache,
            ttl_dns_cache=ttl_dns_cache,
            family=family,
            ssl_context=ssl_context,
            ssl=ssl,
            local_addr=local_addr,
            resolver=resolver,
            keepalive_timeout=keepalive_timeout,
            force_close=force_close,
            limit=limit,
            limit_per_host=limit_per_host,
            enable_cleanup_closed=enable_cleanup_closed,
            loop=loop,
            timeout_ceil_threshold=timeout_ceil_threshold,
            happy_eyeballs_delay=happy_eyeballs_delay,
            interleave=interleave,
        )

        self._proxy_type = proxy_type
        self._proxy_host = host
        self._proxy_port = port
        self._proxy_username = username
        self._proxy_password = password
        self._rdns = rdns
        self._proxy_ssl = proxy_ssl

    async def _connect_via_proxy(
        self,
        host: str,
        port: int,
        ssl: Optional[SSLContext] = None,  # pylint: disable=redefined-outer-name
        timeout: Optional[float] = None,
    ) -> tuple[asyncio.Transport, ResponseHandler]:
        proxy = Proxy(
            proxy_type=self._proxy_type,
            host=self._proxy_host,
            port=self._proxy_port,
            username=self._proxy_username,
            password=self._proxy_password,
            rdns=self._rdns,
            proxy_ssl=self._proxy_ssl,  # type: ignore
        )

        stream = await proxy.connect(
            dest_host=host,
            dest_port=port,
            dest_ssl=ssl,  # type: ignore
            timeout=timeout,  # type: ignore
        )

        transport: asyncio.Transport = stream.writer.transport  # type: ignore
        protocol = _ResponseHandler(loop=self._loop, writer=stream.writer)

        transport.set_protocol(protocol)
        protocol.connection_made(transport)

        return transport, protocol

    async def _wrap_create_connection(
        self,
        *args: Any,
        addr_infos: List[aiohappyeyeballs.AddrInfoType],  # type: ignore
        req: ClientRequest,
        timeout: ClientTimeout,
        client_error: type[Exception] = ClientConnectionError,
        **kwargs: Any,
    ) -> Tuple[asyncio.Transport, ResponseHandler]:
        try:
            host = cast(str, addr_infos[0][4][0])
            port = cast(int, addr_infos[0][4][1])
        except IndexError as e:
            raise ValueError("Invalid arg: `addr_infos`") from e

        ssl: Optional[SSLContext] = kwargs.get("ssl")  # pylint: disable=redefined-outer-name
        return await self._connect_via_proxy(
            host=host,
            port=port,
            ssl=ssl,
            timeout=timeout.sock_connect,
        )

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> 'ProxyConnector':
        proxy_type, host, port, username, password = cast(
            Tuple[ProxyType, str, int, str, str],
            parse_proxy_url(url),
        )

        return cls(
            proxy_type=proxy_type,
            host=host,
            port=port,
            username=username,
            password=password,
            **kwargs,
        )


class ProxyInfo(NamedTuple):
    proxy_type: ProxyType
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    rdns: Optional[bool] = None


class ChainProxyConnector(TCPConnector):
    def __init__(
        self,
        proxy_infos: Iterable[ProxyInfo],
        *,
        verify_ssl: bool = True,
        fingerprint: Optional[bytes] = None,
        use_dns_cache: bool = True,
        ttl_dns_cache: Optional[int] = 10,
        family: socket.AddressFamily = socket.AddressFamily.AF_UNSPEC,  # pylint: disable=no-member
        ssl_context: Optional[SSLContext] = None,
        ssl: Union[bool, Fingerprint, SSLContext] = True,  # pylint: disable=redefined-outer-name
        local_addr: Optional[Tuple[str, int]] = None,
        resolver: Optional[AbstractResolver] = None,
        keepalive_timeout: Union[None, float, object] = sentinel,
        force_close: bool = False,
        limit: int = 100,
        limit_per_host: int = 0,
        enable_cleanup_closed: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        timeout_ceil_threshold: float = 5,
        happy_eyeballs_delay: Optional[float] = 0.25,
        interleave: Optional[int] = None,
    ):
        resolver = NoResolver()
        super().__init__(
            verify_ssl=verify_ssl,
            fingerprint=fingerprint,
            use_dns_cache=use_dns_cache,
            ttl_dns_cache=ttl_dns_cache,
            family=family,
            ssl_context=ssl_context,
            ssl=ssl,
            local_addr=local_addr,
            resolver=resolver,
            keepalive_timeout=keepalive_timeout,
            force_close=force_close,
            limit=limit,
            limit_per_host=limit_per_host,
            enable_cleanup_closed=enable_cleanup_closed,
            loop=loop,
            timeout_ceil_threshold=timeout_ceil_threshold,
            happy_eyeballs_delay=happy_eyeballs_delay,
            interleave=interleave,
        )
        self._proxy_infos = proxy_infos

    async def _connect_via_proxy(
        self,
        host: str,
        port: int,
        ssl: Optional[SSLContext] = None,  # pylint: disable=redefined-outer-name
        timeout: Optional[float] = None,
    ) -> tuple[asyncio.Transport, ResponseHandler]:
        forward: Proxy = None  # type: ignore
        for info in self._proxy_infos:
            forward = Proxy(
                proxy_type=info.proxy_type,
                host=info.host,
                port=info.port,
                username=info.username,  # type: ignore
                password=info.password,  # type: ignore
                rdns=info.rdns,  # type: ignore
                forward=forward,  # type: ignore
            )

        stream = await forward.connect(
            dest_host=host,
            dest_port=port,
            dest_ssl=ssl,  # type: ignore
            timeout=timeout,  # type: ignore
        )

        transport: asyncio.Transport = stream.writer.transport  # type: ignore
        protocol: ResponseHandler = _ResponseHandler(
            loop=self._loop,
            writer=stream.writer,
        )

        transport.set_protocol(protocol)
        protocol.connection_made(transport)

        return transport, protocol

    async def _wrap_create_connection(
        self,
        *args: Any,
        addr_infos: List[aiohappyeyeballs.AddrInfoType],  # type: ignore
        req: ClientRequest,
        timeout: ClientTimeout,
        client_error: type[Exception] = ClientConnectorError,
        **kwargs: Any,
    ) -> Tuple[asyncio.Transport, ResponseHandler]:
        try:
            host = cast(str, addr_infos[0][4][0])
            port = cast(int, addr_infos[0][4][1])
        except IndexError as e:
            raise ValueError("Invalid arg: `addr_infos`") from e

        ssl: Optional[SSLContext] = kwargs.get("ssl")  # pylint: disable=redefined-outer-name
        return await self._connect_via_proxy(
            host=host,
            port=port,
            ssl=ssl,
            timeout=timeout.sock_connect,
        )

    @classmethod
    def from_urls(cls, urls: Iterable[str], **kwargs: Any) -> 'ChainProxyConnector':
        infos: List[ProxyInfo] = []

        for url in urls:
            proxy_type, host, port, username, password = cast(
                Tuple[ProxyType, str, int, str, str],
                parse_proxy_url(url),
            )
            proxy_info = ProxyInfo(
                proxy_type=proxy_type,
                host=host,
                port=port,
                username=username,
                password=password,
            )
            infos.append(proxy_info)

        return cls(infos, **kwargs)
