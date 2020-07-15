import ipaddress
import socket

from ._errors import ProxyError
from ._helpers import is_ip_address
from ._stream_sync import SyncSocketStream
from ._proto_socks5 import (
    NULL,
    RSV,
    SOCKS_VER5,
    SOCKS5_AUTH_UNAME_PWD,
    SOCKS5_AUTH_ANONYMOUS,
    SOCKS5_AUTH_NO_ACCEPTABLE_METHODS,
    SOCKS5_GRANTED,
    SOCKS_CMD_CONNECT,
    SOCKS5_ATYP_IPv4,
    SOCKS5_ATYP_IPv6,
    SOCKS5_ATYP_DOMAIN,
    SOCKS5_ERRORS
)


class Socks5Proto:
    def __init__(self, stream: SyncSocketStream,
                 dest_host, dest_port, username=None, password=None,
                 rdns=None):

        if rdns is None:
            rdns = True

        self._dest_port = dest_port
        self._dest_host = dest_host
        self._username = username
        self._password = password
        self._rdns = rdns

        self._stream = stream

    def negotiate(self):
        self._socks_auth()
        self._socks_connect()

    def _socks_auth(self):
        # send auth methods
        if self._username and self._password:
            auth_methods = [SOCKS5_AUTH_UNAME_PWD, SOCKS5_AUTH_ANONYMOUS]
        else:
            auth_methods = [SOCKS5_AUTH_ANONYMOUS]

        req = [SOCKS_VER5, len(auth_methods)] + auth_methods

        self._stream.write(req)

        ver, auth_method = self._stream.read_exact(2)

        if ver != SOCKS_VER5:
            raise ProxyError('Unexpected '  # pragma: no cover
                             'SOCKS version number: {}'.format(ver))

        if auth_method == SOCKS5_AUTH_NO_ACCEPTABLE_METHODS:
            raise ProxyError('No acceptable '  # pragma: no cover
                             'authentication methods were offered')

        if auth_method not in auth_methods:
            raise ProxyError('Unexpected SOCKS '  # pragma: no cover
                             'authentication method: {}'.format(auth_method))

        # authenticate
        if auth_method == SOCKS5_AUTH_UNAME_PWD:
            req = [
                0x01,
                len(self._username),
                self._username.encode('ascii'),
                len(self._password),
                self._password.encode('ascii')
            ]

            self._stream.write(req)

            ver, status = self._stream.read_exact(2)

            if ver != 0x01:
                raise ProxyError('Invalid '  # pragma: no cover
                                 'authentication response')

            if status != SOCKS5_GRANTED:
                raise ProxyError('Username and password '  # pragma: no cover
                                 'authentication failure')

    def _socks_connect(self):
        req_addr = self._build_addr_request()
        req = [SOCKS_VER5, SOCKS_CMD_CONNECT, RSV] + req_addr

        self._stream.write(req)

        ver, err_code, reserved = self._stream.read_exact(3)

        if ver != SOCKS_VER5:
            raise ProxyError('Unexpected SOCKS '  # pragma: no cover
                             'version number: {}'.format(ver))

        if err_code != NULL:
            raise ProxyError(SOCKS5_ERRORS.get(err_code, 'Unknown error'),
                             err_code)

        if reserved != RSV:
            raise ProxyError('The reserved byte '  # pragma: no cover
                             'must be 0x00')

        # read all available data (bind address)
        self._stream.read()

    def _build_addr_request(self):
        host = self._dest_host
        port = self._dest_port
        port_bytes = port.to_bytes(2, 'big')

        ver_to_byte = {4: SOCKS5_ATYP_IPv4, 6: SOCKS5_ATYP_IPv6}

        # destination address provided is an IPv4 or IPv6 address
        if is_ip_address(host):
            ip = ipaddress.ip_address(host)
            return [ver_to_byte[ip.version], ip.packed, port_bytes]

        # not IP address, probably a DNS name
        if self._rdns:
            # resolve remotely
            host_bytes = host.encode('idna')
            host_len = len(host_bytes)
            return [SOCKS5_ATYP_DOMAIN, host_len, host_bytes, port_bytes]
        else:
            # resolve locally
            _, addr = self._stream.resolver.resolve(
                host,
                family=socket.AF_UNSPEC
            )
            ip = ipaddress.ip_address(addr)
            return [ver_to_byte[ip.version], ip.packed, port_bytes]
