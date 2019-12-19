import asyncio
import socket

from .mixins import StreamSocketReadWriteMixin, ResolveMixin
from ..errors import ProxyConnectionError, ProxyError


class BaseProxy(StreamSocketReadWriteMixin, ResolveMixin):
    def __init__(self, loop, proxy_host, proxy_port, family=socket.AF_INET):
        self._loop = loop
        self._socks_host = proxy_host
        self._socks_port = proxy_port
        self._dest_host = None
        self._dest_port = None
        self._family = family
        self._socket = None

    async def connect(self, dest_host, dest_port):
        self._dest_host = dest_host
        self._dest_port = dest_port

        self._socket = socket.socket(
            family=self._family,
            type=socket.SOCK_STREAM
        )
        self._socket.setblocking(False)

        try:
            await self._loop.sock_connect(
                sock=self._socket,
                address=(self._socks_host, self._socks_port)
            )
        except OSError as e:
            self.close()
            raise ProxyConnectionError(
                e.errno,
                'Can not connect to proxy {}:{} [{}]'.format(
                    self._socks_host, self._socks_port, e.strerror)) from e
        except asyncio.CancelledError:  # pragma: no cover
            self.close()
            raise

        try:
            await self._negotiate()
        except ProxyError:
            self.close()
            raise
        except asyncio.CancelledError:  # pragma: no cover
            if self._can_be_closed_safely():
                self.close()
            raise

    async def _negotiate(self):  # pragma: no cover
        raise NotImplementedError()

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
