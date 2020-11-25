import enum
import ipaddress
import logging
import socket

from .base_proxy import BaseProxyHandler, ProxyError
from .resolver import Resolver
from ..helpers import is_ipv4_address, is_ipv6_address

RSV = NULL = 0x00
SOCKS_VER4 = 0x04


class Command(enum.IntEnum):
    CONNECT = 0x01
    BIND = 0x02


class ReplyCode(enum.IntEnum):
    REQUEST_GRANTED = 0x5A
    REQUEST_REJECTED_OR_FAILED = 0x5B
    CONNECTION_FAILED = 0x5C
    AUTHENTICATION_FAILED = 0x5D


ReplyMessages = {
    ReplyCode.REQUEST_GRANTED: 'Request granted',
    ReplyCode.REQUEST_REJECTED_OR_FAILED: 'Request rejected or failed',
    ReplyCode.CONNECTION_FAILED: 'Request rejected because SOCKS server '
                                 'cannot connect to identd on the client',
    ReplyCode.AUTHENTICATION_FAILED: 'Request rejected because '
                                     'the client program '
                                     'and identd report different user-ids'
}


class Socks4ProxyHandler(BaseProxyHandler):
    def __init__(self, request, client_address, server, *, username=None):
        self.username = username
        self.logger = logging.getLogger(__name__)
        self.resolver = Resolver()

        super().__init__(request, client_address, server)

    def connect_to_remote(self) -> socket.socket:
        client = self.request

        version, command = client.recv(2)

        if version != SOCKS_VER4:
            self.respond(ReplyCode.REQUEST_REJECTED_OR_FAILED)
            raise ProxyError('Invalid socks version')

        if command != Command.CONNECT:
            self.respond(ReplyCode.REQUEST_REJECTED_OR_FAILED)
            raise ProxyError('Unsupported command')

        port = int.from_bytes(client.recv(2), 'big')
        host_bytes = client.recv(4)

        include_hostname = host_bytes[:3] == bytes([NULL, NULL, NULL])

        user = self.read_until_null().decode('ascii')
        if self.username and self.username != user:
            self.respond(ReplyCode.AUTHENTICATION_FAILED)
            raise ProxyError('Authentication failed')

        if include_hostname:
            host = self.read_until_null().decode('ascii')
        else:
            host = str(ipaddress.IPv4Address(host_bytes))

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
            self.respond(ReplyCode.CONNECTION_FAILED)
            raise ProxyError('Connection refused by destination host') from e
        else:
            self.respond(ReplyCode.REQUEST_GRANTED)
            return remote

    def read_until_null(self) -> bytes:
        data = bytearray()
        while True:
            byte = ord(self.request.recv(1))
            if byte == NULL:
                break
            data.append(byte)
        return data

    def respond(self, code: ReplyCode):
        self.request.sendall(bytes([
            RSV,
            code,
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
        ]))

    def resolve_target_host(self, host):
        if is_ipv4_address(host):
            return socket.AF_INET, host
        if is_ipv6_address(host):
            return socket.AF_INET6, host
        return self.resolver.resolve(host=host)
