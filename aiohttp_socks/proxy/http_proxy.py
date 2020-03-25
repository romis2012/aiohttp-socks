from aiohttp import BasicAuth
from aiohttp.http import SERVER_SOFTWARE
from .errors import ProxyError

from .base_proxy import BaseProxy

CRLF = '\r\n'
CRLF_B = CRLF.encode('ascii')


class HttpProxy(BaseProxy):
    def __init__(self, loop, proxy_host, proxy_port,
                 username=None, password=None, family=None):
        super().__init__(
            loop=loop,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            family=family
        )
        self._username = username
        self._password = password

    async def negotiate(self):
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
            raise ProxyError('Invalid proxy response')  # pragma: no cover'

        line = res.split(CRLF_B, 1)[0]
        line = line.decode('utf-8', 'surrogateescape')

        try:
            version, code, *reason = line.split()
        except ValueError:  # pragma: no cover
            raise ProxyError('Invalid status line: {}'.format(line))

        try:
            status_code = int(code)
        except ValueError:  # pragma: no cover
            raise ProxyError('Invalid status code: {}'.format(code))

        if status_code != 200:
            raise ProxyError(  # pragma: no cover
                'Proxy server error. Status: {}'.format(status_code),
                status_code)
