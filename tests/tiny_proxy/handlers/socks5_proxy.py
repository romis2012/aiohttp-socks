import enum
import ipaddress
import logging
import socket

from .base_proxy import BaseProxyHandler, ProxyError
from .resolver import Resolver
from ..helpers import is_ipv4_address, is_ipv6_address

RSV = NULL = 0x00
SOCKS_VER5 = 0x05

SOCKS5_GRANTED = 0x00


class AuthMethod(enum.IntEnum):
    ANONYMOUS = 0x00
    GSSAPI = 0x01
    USERNAME_PASSWORD = 0x02
    NO_ACCEPTABLE = 0xff


class AddressType(enum.IntEnum):
    IPV4 = 0x01
    DOMAIN = 0x03
    IPV6 = 0x04

    @classmethod
    def from_ip_ver(cls, ver: int):
        if ver == 4:
            return cls.IPV4
        if ver == 6:
            return cls.IPV6

        raise ValueError('Invalid IP version')


class Command(enum.IntEnum):
    CONNECT = 0x01
    BIND = 0x02
    UDP_ASSOCIATE = 0x03


class ReplyCode(enum.IntEnum):
    SUCCEEDED = 0x00
    GENERAL_FAILURE = 0x01
    CONNECTION_NOT_ALLOWED = 0x02
    NETWORK_UNREACHABLE = 0x03
    HOST_UNREACHABLE = 0x04
    CONNECTION_REFUSED = 0x05
    TTL_EXPIRED = 0x06
    COMMAND_NOT_SUPPORTED = 0x07
    ADDRESS_TYPE_NOT_SUPPORTED = 0x08


ReplyMessages = {
    ReplyCode.SUCCEEDED: 'Request granted',
    ReplyCode.GENERAL_FAILURE: 'General SOCKS server failure',
    ReplyCode.CONNECTION_NOT_ALLOWED: 'Connection not allowed by ruleset',
    ReplyCode.NETWORK_UNREACHABLE: 'Network unreachable',
    ReplyCode.HOST_UNREACHABLE: 'Host unreachable',
    ReplyCode.CONNECTION_REFUSED: 'Connection refused by destination host',
    ReplyCode.TTL_EXPIRED: 'TTL expired',
    ReplyCode.COMMAND_NOT_SUPPORTED: 'Command not supported or protocol error',
    ReplyCode.ADDRESS_TYPE_NOT_SUPPORTED: 'Address type not supported'
}


class Socks5ProxyHandler(BaseProxyHandler):
    def __init__(self, request, client_address, server, *,
                 username=None, password=None):
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
        self.resolver = Resolver()

        super().__init__(request, client_address, server)

    def connect_to_remote(self) -> socket.socket:
        client = self.request

        auth_required = self.username and self.password

        # ------------------------AUTH METHODS---------------------
        version, num_methods = client.recv(2)

        if version != SOCKS_VER5:
            client.sendall(bytes([NULL, NULL]))
            raise ProxyError('Unsupported socks version')

        methods = []
        for i in range(num_methods):
            methods.append(ord(client.recv(1)))

        if auth_required:
            auth_method = (AuthMethod.USERNAME_PASSWORD
                           if AuthMethod.USERNAME_PASSWORD in methods
                           else AuthMethod.NO_ACCEPTABLE)
        else:
            auth_method = (AuthMethod.ANONYMOUS
                           if AuthMethod.ANONYMOUS in methods
                           else AuthMethod.NO_ACCEPTABLE)

        client.sendall(bytes([SOCKS_VER5, auth_method]))
        if auth_method == AuthMethod.NO_ACCEPTABLE:
            raise ProxyError('Not acceptable auth method')

        # -----------------------AUTH REQUEST-----------------------
        if auth_method == AuthMethod.USERNAME_PASSWORD:
            version = ord(client.recv(1))
            if version != 1:
                client.sendall(bytes([version, 0xFF]))
                raise ProxyError('Invalid auth request')

            username_len = ord(client.recv(1))
            username = client.recv(username_len).decode('utf-8')

            password_len = ord(client.recv(1))
            password = client.recv(password_len).decode('utf-8')

            if username == self.username and password == self.password:
                client.sendall(bytes([version, SOCKS5_GRANTED]))
            else:
                client.sendall(bytes([version, 0xFF]))
                raise ProxyError('Authentication failed')

        # --------------------------CONNECT-----------------------------
        version, cmd, _, address_type = client.recv(4)

        if version != SOCKS_VER5:
            client.sendall(bytes([
                SOCKS_VER5,
                ReplyCode.GENERAL_FAILURE,
                RSV
            ]))
            raise ProxyError(ReplyMessages[ReplyCode.GENERAL_FAILURE])

        if cmd != Command.CONNECT:
            client.sendall(bytes([
                SOCKS_VER5,
                ReplyCode.COMMAND_NOT_SUPPORTED,
                RSV
            ]))
            raise ProxyError(ReplyMessages[ReplyCode.COMMAND_NOT_SUPPORTED])

        if address_type == AddressType.IPV4:
            remote_host = str(ipaddress.IPv4Address(client.recv(4)))
        elif address_type == AddressType.IPV6:
            remote_host = str(ipaddress.IPv6Address(client.recv(16)))
        elif address_type == AddressType.DOMAIN:
            domain_length = ord(client.recv(1))
            remote_host = client.recv(domain_length).decode('ascii')
        else:
            client.sendall(bytes([
                SOCKS_VER5,
                ReplyCode.ADDRESS_TYPE_NOT_SUPPORTED,
                NULL, NULL, NULL, NULL
            ]))
            raise ProxyError(
                ReplyMessages[ReplyCode.ADDRESS_TYPE_NOT_SUPPORTED])

        remote_port = int.from_bytes(client.recv(2), 'big')

        self.logger.info('CONNECT {}:{}'.format(remote_host, remote_port))

        try:
            # remote = socket.create_connection((remote_host, remote_port))
            family, host = self.resolve_target_host(remote_host)

            remote = socket.socket(
                family=family,
                type=socket.SOCK_STREAM
            )

            remote.connect((host, remote_port))
        except Exception as e:
            self.logger.error(e)
            reply = bytes([
                SOCKS_VER5,
                ReplyCode.CONNECTION_REFUSED,
                NULL, NULL, NULL, NULL
            ])
            client.sendall(reply)
            raise ProxyError(
                ReplyMessages[ReplyCode.CONNECTION_REFUSED]) from e
        else:
            bind_address = remote.getsockname()
            bind_ip = ipaddress.ip_address(bind_address[0])
            bind_port = bind_address[1]

            reply = bytearray([
                SOCKS_VER5,
                ReplyCode.SUCCEEDED,
                RSV,
                AddressType.from_ip_ver(bind_ip.version)
            ])
            reply += bind_ip.packed
            reply += bind_port.to_bytes(2, 'big')

            client.sendall(reply)

            return remote

    def resolve_target_host(self, host):
        if is_ipv4_address(host):
            return socket.AF_INET, host
        if is_ipv6_address(host):
            return socket.AF_INET6, host
        return self.resolver.resolve(host=host)
