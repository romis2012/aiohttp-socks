import sys
import asyncio
import async_timeout

from ._types import ProxyType
from ._errors import ProxyConnectionError, ProxyTimeoutError
from ._helpers import parse_proxy_url

from ._proxy_async import AsyncProxy
from ._stream_async_aio import SocketStream
from ._proto_socks5_async import Socks5Proto
from ._proto_http_async import HttpProto
from ._proto_socks4_async import Socks4Proto

DEFAULT_TIMEOUT = 60


class Proxy:
    @classmethod
    def create(cls, proxy_type: ProxyType, host: str, port: int,
               username: str = None, password: str = None,
               rdns: bool = None,
               loop: asyncio.AbstractEventLoop = None) -> AsyncProxy:

        if loop is None:
            loop = asyncio.get_event_loop()

        if proxy_type == ProxyType.SOCKS4:
            return Socks4Proxy(
                loop=loop,
                proxy_host=host,
                proxy_port=port,
                user_id=username,
                rdns=rdns
            )

        if proxy_type == ProxyType.SOCKS5:
            return Socks5Proxy(
                loop=loop,
                proxy_host=host,
                proxy_port=port,
                username=username,
                password=password,
                rdns=rdns
            )

        if proxy_type == ProxyType.HTTP:
            return HttpProxy(
                loop=loop,
                proxy_host=host,
                proxy_port=port,
                username=username,
                password=password
            )

        raise ValueError('Invalid proxy type: %s'  # pragma: no cover
                         % proxy_type)

    @classmethod
    def from_url(cls, url: str, **kwargs) -> AsyncProxy:
        proxy_type, host, port, username, password = parse_proxy_url(url)
        return cls.create(
            proxy_type=proxy_type,
            host=host,
            port=port,
            username=username,
            password=password,
            **kwargs
        )


class BaseProxy(AsyncProxy):
    def __init__(self, loop: asyncio.AbstractEventLoop,
                 proxy_host, proxy_port):

        self._loop = loop

        self._proxy_host = proxy_host
        self._proxy_port = proxy_port

        self._dest_host = None
        self._dest_port = None
        self._timeout = None

        self._stream = SocketStream(loop=loop)

    async def connect(self, dest_host, dest_port, timeout=None, _socket=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT

        self._dest_host = dest_host
        self._dest_port = dest_port
        self._timeout = timeout

        try:
            await self._connect(_socket=_socket)
        except asyncio.TimeoutError as e:
            raise ProxyTimeoutError(
                'Proxy connection timed out: %s'
                % self._timeout) from e

        return self._stream.socket

    async def _connect(self, _socket=None):
        async with async_timeout.timeout(self._timeout):
            try:
                await self._stream.open_connection(
                    host=self._proxy_host,
                    port=self._proxy_port,
                    timeout=self._timeout,
                    _socket=_socket
                )
            except OSError as e:
                await self._stream.close()
                msg = ('Can not connect to proxy %s:%s [%s]' %
                       (self._proxy_host, self._proxy_port, e.strerror))
                raise ProxyConnectionError(e.errno, msg) from e
            except Exception:  # pragma: no cover
                await self._stream.close()
                raise

            try:
                await self._negotiate()
            except asyncio.CancelledError:  # pragma: no cover
                # https://bugs.python.org/issue30064
                # https://bugs.python.org/issue34795
                if self._can_be_closed_safely():
                    await self._stream.close()
                raise
            except Exception:
                await self._stream.close()
                raise

    def _can_be_closed_safely(self):  # pragma: no cover
        def is_proactor_event_loop():
            try:
                from asyncio import ProactorEventLoop  # noqa
            except ImportError:
                return False
            return isinstance(self._loop, ProactorEventLoop)

        def is_uvloop_event_loop():
            try:
                from uvloop import Loop  # noqa
            except ImportError:
                return False
            return isinstance(self._loop, Loop)

        return (sys.version_info[:2] >= (3, 8)
                or is_proactor_event_loop()
                or is_uvloop_event_loop())

    async def _negotiate(self):
        proto = self._create_proto()
        await proto.negotiate()

    def _create_proto(self):
        raise NotImplementedError()  # pragma: no cover

    @property
    def proxy_host(self):
        return self._proxy_host

    @property
    def proxy_port(self):
        return self._proxy_port


class Socks5Proxy(BaseProxy):
    def __init__(self, loop: asyncio.AbstractEventLoop,
                 proxy_host, proxy_port,
                 username=None, password=None, rdns=None):
        super().__init__(
            loop=loop,
            proxy_host=proxy_host,
            proxy_port=proxy_port
        )
        self._username = username
        self._password = password
        self._rdns = rdns

    def _create_proto(self):
        return Socks5Proto(
            stream=self._stream,
            dest_host=self._dest_host,
            dest_port=self._dest_port,
            username=self._username,
            password=self._password,
            rdns=self._rdns
        )


class Socks4Proxy(BaseProxy):
    def __init__(self, loop: asyncio.AbstractEventLoop,
                 proxy_host, proxy_port,
                 user_id=None, rdns=None):
        super().__init__(
            loop=loop,
            proxy_host=proxy_host,
            proxy_port=proxy_port
        )
        self._user_id = user_id
        self._rdns = rdns

    def _create_proto(self):
        return Socks4Proto(
            stream=self._stream,
            dest_host=self._dest_host,
            dest_port=self._dest_port,
            user_id=self._user_id,
            rdns=self._rdns
        )


class HttpProxy(BaseProxy):
    def __init__(self, loop: asyncio.AbstractEventLoop,
                 proxy_host, proxy_port,
                 username=None, password=None):
        super().__init__(
            loop=loop,
            proxy_host=proxy_host,
            proxy_port=proxy_port
        )
        self._username = username
        self._password = password

    def _create_proto(self):
        return HttpProto(
            stream=self._stream,
            dest_host=self._dest_host,
            dest_port=self._dest_port,
            username=self._username,
            password=self._password
        )
