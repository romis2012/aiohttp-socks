import socket
import asyncio

from ..errors import SocksConnectionError, InvalidServerReply, SocksError


class BaseProxy:
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
            raise SocksConnectionError(
                e.errno,
                'Can not connect to proxy {}:{} [{}]'.format(
                    self._socks_host, self._socks_port, e.strerror)) from e
        except asyncio.CancelledError:  # pragma: no cover
            self.close()
            raise

        try:
            await self._negotiate()
        except SocksError:
            self.close()
            raise
        except asyncio.CancelledError:  # pragma: no cover
            if self._can_be_closed_safely():
                self.close()
            raise

    async def _negotiate(self):
        raise NotImplementedError()

    async def _send(self, request):
        data = bytearray()
        for item in request:
            if isinstance(item, int):
                data.append(item)
            elif isinstance(item, (bytearray, bytes)):
                data += item
            else:
                raise ValueError('Unsupported request type')
        await self._loop.sock_sendall(self._socket, data)

    async def _send_all(self, data):
        await self._loop.sock_sendall(self._socket, data)

    async def _receive(self, n):
        data = bytearray()
        while len(data) < n:
            packet = await self._loop.sock_recv(self._socket, n - len(data))
            if not packet:
                raise InvalidServerReply('Connection closed unexpectedly')
            data += packet
        return data

    async def _receive_all(self, buff_size=4096):
        data = bytearray()
        while True:
            packet = await self._loop.sock_recv(self._socket, buff_size)
            if not packet:
                break
            data += packet
            if len(data) < buff_size:
                break
        return data

    async def resolve(self, host, port=0, family=socket.AF_INET):
        infos = await self._loop.getaddrinfo(
            host=host, port=port,
            family=family, type=socket.SOCK_STREAM)

        if not infos:
            raise OSError('Can`t resolve address {}:{} [{}]'.format(
                host, port, family))

        family, _, _, _, address = infos[0]
        return family, address[0]

    def _can_be_closed_safely(self):
        def is_proactor_event_loop():  # pragma: no cover
            try:
                from asyncio import ProactorEventLoop
            except ImportError:
                return False
            return isinstance(self._loop, ProactorEventLoop)

        def is_uvloop_event_loop():  # pragma: no cover
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
