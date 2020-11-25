import functools
import ssl
import socket
from socketserver import ThreadingMixIn, TCPServer

from .handlers import HttpProxyHandler, Socks5ProxyHandler, Socks4ProxyHandler
from .helpers import is_ipv6_address


class ProxyServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True

    def __init__(self, addr, handler_cls, ssl_context: ssl.SSLContext = None):
        if is_ipv6_address(addr[0]):
            self.address_family = socket.AF_INET6

        super().__init__(server_address=addr, RequestHandlerClass=handler_cls)

        self.ssl_context = ssl_context

    def get_request(self):
        sock, addr = self.socket.accept()

        if self.ssl_context is not None:
            sock = self.ssl_context.wrap_socket(sock, server_side=True)

        return sock, addr


class HttpProxyServer(ProxyServer):
    def __init__(self, host: str, port: int,
                 username=None, password=None,
                 ssl_context: ssl.SSLContext = None):
        handler_cls = functools.partial(
            HttpProxyHandler,
            username=username,
            password=password
        )
        super().__init__(
            addr=(host, port),
            handler_cls=handler_cls,
            ssl_context=ssl_context
        )


class Socks5ProxyServer(ProxyServer):
    def __init__(self, host: str, port: int,
                 username=None, password=None,
                 ssl_context: ssl.SSLContext = None):
        handler_cls = functools.partial(
            Socks5ProxyHandler,
            username=username,
            password=password
        )
        super().__init__(
            addr=(host, port),
            handler_cls=handler_cls,
            ssl_context=ssl_context
        )


class Socks4ProxyServer(ProxyServer):
    def __init__(self, host: str, port: int,
                 username=None, ssl_context: ssl.SSLContext = None):
        handler_cls = functools.partial(
            Socks4ProxyHandler,
            username=username
        )
        super().__init__(
            addr=(host, port),
            handler_cls=handler_cls,
            ssl_context=ssl_context
        )
