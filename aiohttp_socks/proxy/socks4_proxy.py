import ipaddress
import socket

from .helpers import is_ipv4_address
from .base_proxy import BaseProxy
from .errors import ProxyError

RSV = NULL = 0x00
SOCKS_VER4 = 0x04
SOCKS_CMD_CONNECT = 0x01
SOCKS4_GRANTED = 0x5A

SOCKS4_ERRORS = {
    0x5B: 'Request rejected or failed',
    0x5C: 'Request rejected because SOCKS server '
          'cannot connect to identd on the client',
    0x5D: 'Request rejected because the client program '
          'and identd report different user-ids'
}


class Socks4Proxy(BaseProxy):
    def __init__(self, loop, proxy_host, proxy_port,
                 user_id=None, rdns=None):
        super().__init__(
            loop=loop,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            family=None
        )

        if rdns is None:
            rdns = False

        self._user_id = user_id
        self._rdns = rdns

    async def negotiate(self):
        await self._socks_connect()

    async def _socks_connect(self):
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
                _, addr = await self.resolve(host, family=socket.AF_INET)
                host_bytes = ipaddress.ip_address(addr).packed

        # build and send connect command
        req = [SOCKS_VER4, SOCKS_CMD_CONNECT, port_bytes, host_bytes]

        if self._user_id:
            req.append(self._user_id.encode('ascii'))

        req.append(NULL)

        if include_hostname:
            req += [host.encode('idna'), NULL]

        await self.write(req)

        rsv, code, *_ = await self.read(8)

        if rsv != NULL:  # pragma: no cover
            raise ProxyError('SOCKS4 proxy server sent invalid data')

        if code != SOCKS4_GRANTED:  # pragma: no cover
            error = SOCKS4_ERRORS.get(code, 'Unknown error')
            raise ProxyError('[Errno {0:#04x}]: {1}'.format(code, error),
                             code)
