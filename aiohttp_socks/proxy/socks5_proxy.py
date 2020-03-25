import ipaddress
import socket

from .helpers import is_ip_address
from .base_proxy import BaseProxy
from .errors import ProxyError

RSV = NULL = 0x00
SOCKS_VER5 = 0x05
SOCKS5_GRANTED = 0x00

SOCKS_CMD_CONNECT = 0x01

SOCKS5_AUTH_ANONYMOUS = 0x00
SOCKS5_AUTH_UNAME_PWD = 0x02
SOCKS5_AUTH_NO_ACCEPTABLE_METHODS = 0xFF

SOCKS5_ATYP_IPv4 = 0x01
SOCKS5_ATYP_DOMAIN = 0x03
SOCKS5_ATYP_IPv6 = 0x04

SOCKS5_ERRORS = {
    0x01: 'General SOCKS server failure',
    0x02: 'Connection not allowed by ruleset',
    0x03: 'Network unreachable',
    0x04: 'Host unreachable',
    0x05: 'Connection refused',
    0x06: 'TTL expired',
    0x07: 'Command not supported, or protocol error',
    0x08: 'Address type not supported'
}


class Socks5Proxy(BaseProxy):
    def __init__(self, loop, proxy_host, proxy_port, username=None,
                 password=None, rdns=None, family=None):
        super().__init__(
            loop=loop,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            family=family
        )

        if rdns is None:
            rdns = True

        self._username = username
        self._password = password
        self._rdns = rdns

    async def negotiate(self):
        await self._socks_auth()
        await self._socks_connect()

    async def _socks_auth(self):
        # send auth methods
        if self._username and self._password:
            auth_methods = [SOCKS5_AUTH_UNAME_PWD, SOCKS5_AUTH_ANONYMOUS]
        else:
            auth_methods = [SOCKS5_AUTH_ANONYMOUS]

        req = [SOCKS_VER5, len(auth_methods)] + auth_methods

        await self.write(req)

        ver, auth_method = await self.read(2)

        if ver != SOCKS_VER5:  # pragma: no cover
            raise ProxyError(
                'Unexpected SOCKS version number: {}'.format(ver))

        if auth_method == SOCKS5_AUTH_NO_ACCEPTABLE_METHODS:
            raise ProxyError(
                'No acceptable authentication methods were offered')

        if auth_method not in auth_methods:
            raise ProxyError(
                'Unexpected SOCKS authentication method: {}'.format(
                    auth_method))

        # authenticate
        if auth_method == SOCKS5_AUTH_UNAME_PWD:
            req = [0x01,
                   len(self._username),
                   self._username.encode('ascii'),
                   len(self._password),
                   self._password.encode('ascii')]

            await self.write(req)

            ver, status = await self.read(2)

            if ver != 0x01:
                raise ProxyError('Invalid authentication response')
            if status != SOCKS5_GRANTED:
                raise ProxyError(
                    'Username and password authentication failure'
                )

    async def _socks_connect(self):
        req_addr = await self._build_addr_request()
        req = [SOCKS_VER5, SOCKS_CMD_CONNECT, RSV] + req_addr

        await self.write(req)

        ver, err_code, reserved = await self.read(3)

        if ver != SOCKS_VER5:
            raise ProxyError('Unexpected SOCKS version number: {}'.format(ver))

        if err_code != NULL:
            raise ProxyError(SOCKS5_ERRORS.get(err_code, 'Unknown error'),
                             err_code)

        if reserved != RSV:
            raise ProxyError('The reserved byte must be 0x00')

        # read all available data (binded address)
        await self.read_all()

    async def _build_addr_request(self):
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
            _, addr = await self.resolve(host, family=socket.AF_UNSPEC)
            ip = ipaddress.ip_address(addr)
            return [ver_to_byte[ip.version], ip.packed, port_bytes]
