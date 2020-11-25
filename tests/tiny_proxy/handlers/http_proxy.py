import logging
import socket
from http.server import BaseHTTPRequestHandler
from io import BytesIO

from .auth import BasicAuth
from .base_proxy import BaseProxyHandler, ProxyError, DEFAULT_RECEIVE_SIZE
from .resolver import Resolver
from ..helpers import is_ipv4_address, is_ipv6_address


class HTTPRequest(BaseHTTPRequestHandler):
    """
    https://stackoverflow.com/questions/4685217/parse-raw-http-headers
    """

    # noinspection PyMissingConstructor
    def __init__(self, data: bytes):
        self.rfile = BytesIO(data)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message=None, explain=None):
        self.error_code = code


class HTTPResponse:
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class HttpProxyHandler(BaseProxyHandler):
    def __init__(self, request, client_address, server, *,
                 username=None, password=None):
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
        self.resolver = Resolver()

        super().__init__(request, client_address, server)

    def connect_to_remote(self) -> socket.socket:
        client = self.request

        req = HTTPRequest(client.recv(DEFAULT_RECEIVE_SIZE))

        if req.error_code:
            self.respond(int(req.error_code), req.error_message)

        if req.command.lower() != 'connect':
            self.respond(400, 'Bad Request')

        if self.username and self.password:
            auth_header = req.headers['proxy-authorization']

            if not auth_header:
                self.respond(401, 'Unauthorized')

            try:
                auth = BasicAuth.decode(auth_header)
            except ValueError:
                self.respond(401, 'Unauthorized')
            else:
                if (auth.login != self.username
                        or auth.password != self.password):
                    self.respond(401, 'Unauthorized')

        try:
            host, port = req.path.split(':')
            port = int(port)
        except ValueError:
            self.respond(400, 'Bad Request')
            raise

        self.logger.info('CONNECT {}:{}'.format(host, port))
        try:
            # remote = socket.create_connection((host, port))
            family, host = self.resolve_target_host(host)

            remote = socket.socket(
                family=family,
                type=socket.SOCK_STREAM
            )

            remote.connect((host, port))
        except Exception as e:
            self.logger.error(e)
            self.respond(502, 'Bad Gateway')
        else:
            self.respond(200, 'Connection established')
            return remote

    def respond(self, code: int, message: str):
        res = 'HTTP/1.1 {} {}\r\n\r\n'.format(code, message)
        self.request.sendall(res.encode('ascii'))
        if code != 200:
            raise ProxyError('{} {}'.format(code, message))

    def resolve_target_host(self, host):
        if is_ipv4_address(host):
            return socket.AF_INET, host
        if is_ipv6_address(host):
            return socket.AF_INET6, host
        return self.resolver.resolve(host=host)
