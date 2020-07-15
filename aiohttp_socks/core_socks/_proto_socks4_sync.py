import ipaddress
import socket

from ._errors import ProxyError
from ._helpers import is_ipv4_address
from ._stream_sync import SyncSocketStream

from ._proto_socks4 import (
    NULL,
    SOCKS_VER4,
    SOCKS_CMD_CONNECT,
    SOCKS4_GRANTED,
    SOCKS4_ERRORS
)


class Socks4Proto:
    def __init__(self, stream: SyncSocketStream, dest_host, dest_port,
                 user_id=None, rdns=None):

        if rdns is None:
            rdns = False

        self._dest_host = dest_host
        self._dest_port = dest_port

        self._user_id = user_id
        self._rdns = rdns

        self._stream = stream

    def negotiate(self):
        self._socks_connect()

    def _socks_connect(self):
        host, port = self._dest_host, self._dest_port
        port_bytes = port.to_bytes(2, 'big')

        include_hostname = False

        if is_ipv4_address(host):
            host_bytes = ipaddress.ip_address(host).packed
        else:
            # not IP address, probably a DNS name
            if self._rdns:
                # remote resolve (SOCKS4a)
                include_hostname = True
                host_bytes = bytes([NULL, NULL, NULL, 0x01])
            else:
                # resolve locally
                _, addr = self._stream.resolver.resolve(
                    host,
                    family=socket.AF_INET
                )
                host_bytes = ipaddress.ip_address(addr).packed

        # build and send connect command
        req = [SOCKS_VER4, SOCKS_CMD_CONNECT, port_bytes, host_bytes]

        if self._user_id:
            req.append(self._user_id.encode('ascii'))

        req.append(NULL)

        if include_hostname:
            req += [host.encode('idna'), NULL]

        self._stream.write(req)

        rsv, code, *_ = self._stream.read_exact(8)

        if rsv != NULL:  # pragma: no cover
            raise ProxyError('SOCKS4 proxy server sent invalid data')

        if code != SOCKS4_GRANTED:  # pragma: no cover
            error = SOCKS4_ERRORS.get(code, 'Unknown error')
            raise ProxyError('[Errno 0x{0:02x}]: {1}'.format(code, error),
                             code)
