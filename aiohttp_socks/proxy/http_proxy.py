import socket

from aiohttp import BasicAuth
from aiohttp.http import SERVER_SOFTWARE
from ..errors import InvalidServerReply

from .base_proxy import BaseProxy

CRLF = '\r\n'
CRLF_B = CRLF.encode('ascii')


class HttpProxy(BaseProxy):
    def __init__(self, loop, proxy_host, proxy_port,
                 username=None, password=None, family=socket.AF_INET):
        super().__init__(
            loop=loop,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            family=family
        )
        self._username = username
        self._password = password

    async def _negotiate(self):
        host = self._dest_host
        port = self._dest_port
        login = self._username
        password = self._password

        # noinspection PyListCreation
        req = []
        req.append('CONNECT {}:{} HTTP/1.1'.format(host, port))
        req.append('Host: {}:{}'.format(host, port))
        req.append('User-Agent: {}'.format(SERVER_SOFTWARE))

        if login and password:
            auth = BasicAuth(login, password)
            req.append('Proxy-Authorization: {}'.format(auth.encode()))

        req.append(CRLF)

        data = CRLF.join(req).encode('ascii')

        await self.write_all(data)

        res = await self.read_all()

        if not res:
            raise InvalidServerReply(  # pragma: no cover
                'Invalid proxy response')

        line = res.split(CRLF_B, 1)[0]
        line = line.decode('utf-8', 'surrogateescape')

        try:
            version, code, *reason = line.split()
        except ValueError:  # pragma: no cover
            raise InvalidServerReply('Invalid status line: {}'.format(line))

        try:
            status_code = int(code)
        except ValueError:  # pragma: no cover
            raise InvalidServerReply('Invalid status code: {}'.format(code))

        if status_code != 200:
            raise InvalidServerReply(  # pragma: no cover
                'Proxy error. Status: {}'.format(status_code))
