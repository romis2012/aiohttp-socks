import asyncio
import socket
import warnings

from .helpers import is_ipv4_address, is_ipv6_address
from .mixins import StreamSocketReadWriteMixin, ResolveMixin
from .errors import ProxyConnectionError, ProxyError
from .abc import AbstractProxy


class BaseProxy(AbstractProxy, StreamSocketReadWriteMixin, ResolveMixin):
    def __init__(self, loop, proxy_host, proxy_port, family=None):
        if family is not None:
            warnings.warn('Parameter family is deprecated '
                          'and will be ignored.', DeprecationWarning,
                          stacklevel=2)

        self._loop = loop
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._dest_host = None
        self._dest_port = None
        self._socket = None

    async def connect(self, dest_host, dest_port, _socket=None):
        self._dest_host = dest_host
        self._dest_port = dest_port

        if _socket is None:
            family, host = await self._resolve_proxy_host()
            self._create_socket(family=family)
            await self._connect_to_proxy(
                host=host,
                port=self._proxy_port
            )
        else:
            self._socket = _socket

        try:
            await self.negotiate()
        except ProxyError:
            self.close()
            raise
        except asyncio.CancelledError:  # pragma: no cover
            if self._can_be_closed_safely():
                self.close()
            raise

    async def negotiate(self):  # pragma: no cover
        raise NotImplementedError()

    def _create_socket(self, family):
        self._socket = socket.socket(
            family=family,
            type=socket.SOCK_STREAM
        )
        self._socket.setblocking(False)

    async def _connect_to_proxy(self, host, port):
        try:
            await self._loop.sock_connect(
                sock=self._socket,
                address=(host, port)
            )
        except OSError as e:
            self.close()
            msg = 'Can not connect to proxy {}:{} [{}]'.format(
                host, port, e.strerror)
            raise ProxyConnectionError(e.errno, msg) from e
        except asyncio.CancelledError:  # pragma: no cover
            self.close()
            raise

    async def _resolve_proxy_host(self):
        host = self._proxy_host
        if is_ipv4_address(host):
            return socket.AF_INET, host
        if is_ipv6_address(host):
            return socket.AF_INET6, host
        return await self.resolve(host=host)

    def _can_be_closed_safely(self):  # pragma: no cover
        def is_proactor_event_loop():
            try:
                from asyncio import ProactorEventLoop
            except ImportError:
                return False
            return isinstance(self._loop, ProactorEventLoop)

        def is_uvloop_event_loop():
            try:
                # noinspection PyPackageRequirements
                from uvloop import Loop
            except ImportError:
                return False
            return isinstance(self._loop, Loop)

        return is_proactor_event_loop() or is_uvloop_event_loop()

    def close(self):
        self._socket.close()

    @property
    def socket(self):
        return self._socket

    @property
    def host(self):
        return self._proxy_host

    @property
    def port(self):
        return self._proxy_port
