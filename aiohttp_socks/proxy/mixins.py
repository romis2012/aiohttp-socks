import socket
from .errors import ProxyError


class StreamSocketReadWriteMixin:
    _loop = None
    _socket = None

    async def write(self, request):
        data = bytearray()
        for item in request:
            if isinstance(item, int):
                data.append(item)
            elif isinstance(item, (bytearray, bytes)):
                data += item
            else:
                raise ValueError('Unsupported request type')
        await self._loop.sock_sendall(self._socket, data)

    async def write_all(self, data):
        await self._loop.sock_sendall(self._socket, data)

    async def read(self, n):
        data = bytearray()
        while len(data) < n:
            packet = await self._loop.sock_recv(self._socket, n - len(data))
            if not packet:
                raise ProxyError('Connection closed unexpectedly')
            data += packet
        return data

    async def read_all(self, buff_size=4096):
        data = bytearray()
        while True:
            packet = await self._loop.sock_recv(self._socket, buff_size)
            if not packet:
                break
            data += packet
            if len(packet) < buff_size:
                break
        return data


class ResolveMixin:
    _loop = None

    async def resolve(self, host, port=0, family=socket.AF_UNSPEC):
        infos = await self._loop.getaddrinfo(
            host=host, port=port,
            family=family, type=socket.SOCK_STREAM)

        if not infos:
            raise OSError('Can`t resolve address {}:{} [{}]'.format(
                host, port, family))

        family, _, _, _, address = infos[0]
        return family, address[0]
