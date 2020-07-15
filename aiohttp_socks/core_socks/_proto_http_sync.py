from ._basic_auth import BasicAuth
from ._errors import ProxyError
from ._proto_http import DEFAULT_USER_AGENT, CRLF
from ._stream_sync import SyncSocketStream


class HttpProto:
    def __init__(self, stream: SyncSocketStream, dest_host, dest_port,
                 username=None, password=None):

        self._dest_host = dest_host
        self._dest_port = dest_port
        self._username = username
        self._password = password

        self._stream = stream

    def negotiate(self):
        host = self._dest_host
        port = self._dest_port
        login = self._username
        password = self._password

        # noinspection PyListCreation
        req = []
        req.append('CONNECT {}:{} HTTP/1.1'.format(host, port))
        req.append('Host: {}:{}'.format(host, port))
        req.append('User-Agent: {}'.format(DEFAULT_USER_AGENT))

        if login and password:
            auth = BasicAuth(login, password)
            req.append('Proxy-Authorization: {}'.format(auth.encode()))

        req.append(CRLF)

        data = CRLF.join(req).encode('ascii')

        self._stream.write_all(data)

        res = self._stream.read()

        if not res:
            raise ProxyError('Invalid proxy response')  # pragma: no cover'

        line = res.split(CRLF.encode('ascii'), 1)[0]
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
