# -*- coding: utf-8 -*-
import asyncio
import socket
import struct

from .errors import (
    SocksConnectionError, InvalidServerReply, SocksError,
    InvalidServerVersion, NoAcceptableAuthMethods,
    LoginAuthenticationFailed, UnknownAuthMethod
)

RSV = NULL = 0x00
SOCKS_VER4 = 0x04
SOCKS_VER5 = 0x05

SOCKS_CMD_CONNECT = 0x01
SOCKS_CMD_BIND = 0x02
SOCKS_CMD_UDP_ASSOCIATE = 0x03

SOCKS4_GRANTED = 0x5A
SOCKS5_GRANTED = 0x00

SOCKS5_AUTH_ANONYMOUS = 0x00
SOCKS5_AUTH_UNAME_PWD = 0x02
SOCKS5_AUTH_NO_ACCEPTABLE_METHODS = 0xFF

SOCKS5_ATYP_IPv4 = 0x01
SOCKS5_ATYP_DOMAIN = 0x03
SOCKS5_ATYP_IPv6 = 0x04

SOCKS4_ERRORS = {
    0x5B: 'Request rejected or failed',
    0x5C: 'Request rejected because SOCKS server '
          'cannot connect to identd on the client',
    0x5D: 'Request rejected because the client program '
          'and identd report different user-ids'
}

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


def _is_proactor(loop):
    try:
        from asyncio import ProactorEventLoop
    except ImportError:
        return False
    return isinstance(loop, ProactorEventLoop)


def _is_uvloop(loop):
    try:
        # noinspection PyPackageRequirements
        from uvloop import Loop
    except ImportError:
        return False
    return isinstance(loop, Loop)


class SocksVer(object):
    SOCKS4 = 1
    SOCKS5 = 2


class BaseSocketWrapper(object):
    def __init__(self, loop, host=None, port=None,
                 family=socket.AF_INET):

        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 1080

        self._loop = loop
        self._socks_host = host
        self._socks_port = port
        self._dest_host = None
        self._dest_port = None
        self._family = family
        self._socket = None

    async def _send(self, request):
        data = bytearray()
        for item in request:
            if isinstance(item, int):
                data.append(item)
            elif isinstance(item, (bytearray, bytes)):
                data += item
            else:
                raise ValueError('Unsupported item')
        await self._loop.sock_sendall(self._socket, data)

    async def _receive(self, n):
        data = b''
        while len(data) < n:
            packet = await self._loop.sock_recv(self._socket, n - len(data))
            if not packet:
                raise InvalidServerReply('Not all data available')
            data += packet
        return bytearray(data)

    async def _resolve_addr(self, host, port):
        addresses = await self._loop.getaddrinfo(
            host=host, port=port, family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP,
            flags=socket.AI_ADDRCONFIG)
        if not addresses:
            raise OSError('Can`t resolve address %s:%s' % (host, port))
        family = addresses[0][0]
        addr = addresses[0][4][0]
        return family, addr

    async def negotiate(self):
        raise NotImplementedError

    async def connect(self, address):
        self._dest_host = address[0]
        self._dest_port = address[1]

        self._socket = socket.socket(
            family=self._family,
            type=socket.SOCK_STREAM
        )
        self._socket.setblocking(False)

        try:
            await self._loop.sock_connect(
                sock=self._socket,
                address=(self._socks_host, self._socks_port)
            )
        except OSError as e:
            self.close()
            raise SocksConnectionError(
                e.errno,
                'Can not connect to proxy %s:%d [%s]' %
                (self._socks_host, self._socks_port, e.strerror)) from e
        except asyncio.CancelledError:
            self.close()
            raise

        try:
            await self.negotiate()
        except SocksError:
            self.close()
            raise
        except asyncio.CancelledError:
            if _is_proactor(self._loop) or _is_uvloop(self._loop):
                self.close()
            raise

    def close(self):
        self._socket.close()

    async def sendall(self, data):
        await self._loop.sock_sendall(self._socket, data)

    async def recv(self, nbytes):
        return await self._loop.sock_recv(self._socket, nbytes)

    @property
    def socket(self):
        return self._socket


class Socks4SocketWrapper(BaseSocketWrapper):
    def __init__(self, loop, host=None, port=None,
                 user_id=None, rdns=False):
        super().__init__(
            loop=loop,
            host=host,
            port=port,
            family=socket.AF_INET
        )
        self._user_id = user_id
        self._rdns = rdns

    async def _socks_connect(self):
        host, port = self._dest_host, self._dest_port
        port_bytes = struct.pack(b'>H', port)

        include_hostname = False
        try:
            # destination address provided is an IP address
            host_bytes = socket.inet_aton(host)
        except socket.error:
            # not IP address, probably a DNS name
            if self._rdns:
                # remote resolve (SOCKS4a)
                host_bytes = bytes([NULL, NULL, NULL, 0x01])
                include_hostname = True
            else:
                # resolve locally
                family, host = await self._resolve_addr(host, port)
                host_bytes = socket.inet_aton(host)

        # build and send connect command
        req = [SOCKS_VER4, SOCKS_CMD_CONNECT, port_bytes, host_bytes]

        if self._user_id:
            req.append(self._user_id.encode())

        req.append(NULL)

        if include_hostname:
            req += [host.encode('idna'), NULL]

        await self._send(req)

        res = await self._receive(8)

        if res[0] != NULL:
            raise InvalidServerReply('SOCKS4 proxy server sent invalid data')
        if res[1] != SOCKS4_GRANTED:
            error = SOCKS4_ERRORS.get(res[1], 'Unknown error')
            raise SocksError('[Errno {0:#04x}]: {1}'.format(res[1], error))

        binded_addr = (
            socket.inet_ntoa(res[4:]),
            struct.unpack('>H', res[2:4])[0]
        )
        return (host, port), binded_addr

    async def negotiate(self):
        await self._socks_connect()


class Socks5SocketWrapper(BaseSocketWrapper):
    def __init__(self, loop, host=None, port=None, username=None,
                 password=None, rdns=True, family=socket.AF_INET):
        super().__init__(
            loop=loop,
            host=host,
            port=port,
            family=family
        )
        self._username = username
        self._password = password
        self._rdns = rdns

    async def _socks_auth(self):
        # send auth methods
        if self._username and self._password:
            auth_methods = [SOCKS5_AUTH_UNAME_PWD, SOCKS5_AUTH_ANONYMOUS]
        else:
            auth_methods = [SOCKS5_AUTH_ANONYMOUS]

        req = [SOCKS_VER5, len(auth_methods)] + auth_methods

        await self._send(req)
        res = await self._receive(2)
        ver, auth_method = res[0], res[1]

        if ver != SOCKS_VER5:
            raise InvalidServerVersion(
                'Unexpected SOCKS version number: %s' % ver
            )

        if auth_method == SOCKS5_AUTH_NO_ACCEPTABLE_METHODS:
            raise NoAcceptableAuthMethods(
                'No acceptable authentication methods were offered'
            )

        if auth_method not in auth_methods:
            raise UnknownAuthMethod(
                'Unexpected SOCKS authentication method: %s' % auth_method
            )

        # authenticate
        if auth_method == SOCKS5_AUTH_UNAME_PWD:
            req = [0x01,
                   chr(len(self._username)).encode(),
                   self._username.encode(),
                   chr(len(self._password)).encode(),
                   self._password.encode()]

            await self._send(req)
            res = await self._receive(2)
            ver, status = res[0], res[1]
            if ver != 0x01:
                raise InvalidServerReply('Invalid authentication response')
            if status != SOCKS5_GRANTED:
                raise LoginAuthenticationFailed(
                    'Username and password authentication failure'
                )

    async def _socks_connect(self):
        req_addr, resolved_addr = await self._build_dest_address()
        req = [SOCKS_VER5, SOCKS_CMD_CONNECT, RSV] + req_addr

        await self._send(req)
        res = await self._receive(3)
        ver, err_code, reserved = res[0], res[1], res[2]
        if ver != SOCKS_VER5:
            raise InvalidServerVersion(
                'Unexpected SOCKS version number: %s' % ver
            )
        if err_code != 0x00:
            raise SocksError(SOCKS5_ERRORS.get(err_code, 'Unknown error'))
        if reserved != 0x00:
            raise InvalidServerReply('The reserved byte must be 0x00')

        binded_addr = await self._read_binded_address()
        return resolved_addr, binded_addr

    async def _build_dest_address(self):
        host = self._dest_host
        port = self._dest_port

        family_to_byte = {socket.AF_INET: SOCKS5_ATYP_IPv4,
                          socket.AF_INET6: SOCKS5_ATYP_IPv6}
        port_bytes = struct.pack('>H', port)

        # destination address provided is an IPv4 or IPv6 address
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                host_bytes = socket.inet_pton(family, host)
                req = [family_to_byte[family], host_bytes, port_bytes]
                return req, (host, port)
            except socket.error:
                pass

        # not IP address, probably a DNS name
        if self._rdns:
            # resolve remotely
            host_bytes = host.encode('idna')
            req = [SOCKS5_ATYP_DOMAIN, chr(len(host_bytes)).encode(),
                   host_bytes, port_bytes]
        else:
            # resolve locally
            family, addr = await self._resolve_addr(host=host, port=port)
            host_bytes = socket.inet_pton(family, addr)
            req = [family_to_byte[family], host_bytes, port_bytes]
            host = socket.inet_ntop(family, host_bytes)

        return req, (host, port)

    async def _read_binded_address(self):
        atype = (await self._receive(1))[0]
        if atype == SOCKS5_ATYP_IPv4:
            addr = await self._receive(4)
            addr = socket.inet_ntoa(addr)
        elif atype == SOCKS5_ATYP_DOMAIN:
            length = await self._receive(1)
            addr = await self._receive(ord(length))
        elif atype == SOCKS5_ATYP_IPv6:
            addr = await self._receive(16)
            addr = socket.inet_ntop(socket.AF_INET6, addr)
        else:
            raise InvalidServerReply('SOCKS5 proxy server sent invalid data')

        port = await self._receive(2)
        port = struct.unpack('>H', port)[0]

        return addr, port

    async def negotiate(self):
        await self._socks_auth()
        await self._socks_connect()
