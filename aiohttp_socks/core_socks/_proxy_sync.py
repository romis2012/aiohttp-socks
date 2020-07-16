import socket

from ._types import ProxyType
from ._errors import ProxyConnectionError, ProxyTimeoutError
from ._helpers import parse_proxy_url

from ._stream_sync import SyncSocketStream
from ._proto_socks5_sync import Socks5Proto
from ._proto_http_sync import HttpProto
from ._proto_socks4_sync import Socks4Proto

DEFAULT_TIMEOUT = 60


class SyncProxy:
    def connect(self, dest_host, dest_port, timeout=None, _socket=None):
        raise NotImplementedError()  # pragma: no cover

    @property
    def proxy_host(self):
        raise NotImplementedError()  # pragma: no cover

    @property
    def proxy_port(self):
        raise NotImplementedError()  # pragma: no cover


class Proxy:
    @classmethod
    def create(cls, proxy_type: ProxyType, host: str, port: int,
               username: str = None, password: str = None,
               rdns: bool = None) -> SyncProxy:

        if proxy_type == ProxyType.SOCKS4:
            return Socks4Proxy(
                proxy_host=host,
                proxy_port=port,
                user_id=username,
                rdns=rdns
            )

        if proxy_type == ProxyType.SOCKS5:
            return Socks5Proxy(
                proxy_host=host,
                proxy_port=port,
                username=username,
                password=password,
                rdns=rdns
            )

        if proxy_type == ProxyType.HTTP:
            return HttpProxy(
                proxy_host=host,
                proxy_port=port,
                username=username,
                password=password
            )

        raise ValueError('Invalid proxy type: '  # pragma: no cover
                         '{}'.format(proxy_type))

    @classmethod
    def from_url(cls, url: str, **kwargs) -> SyncProxy:
        proxy_type, host, port, username, password = parse_proxy_url(url)
        return cls.create(
            proxy_type=proxy_type,
            host=host,
            port=port,
            username=username,
            password=password,
            **kwargs
        )


class BaseProxy(SyncProxy):
    def __init__(self, proxy_host, proxy_port):
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port

        self._dest_host = None
        self._dest_port = None
        self._timeout = None

        self._stream = SyncSocketStream()

    def connect(self, dest_host, dest_port, timeout=None, _socket=None):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT

        self._dest_host = dest_host
        self._dest_port = dest_port
        self._timeout = timeout

        try:
            self._stream.open_connection(
                host=self._proxy_host,
                port=self._proxy_port,
                timeout=timeout,
                _socket=_socket
            )

            self._negotiate()

        except socket.timeout as e:
            self._stream.close()
            raise ProxyTimeoutError('Proxy connection timed out: %s'
                                    % self._timeout) from e
        except OSError as e:
            self._stream.close()
            msg = ('Can not connect to proxy %s:%s [%s]' %
                   (self._proxy_host, self._proxy_port, e.strerror))
            raise ProxyConnectionError(e.errno, msg) from e
        except Exception:
            self._stream.close()
            raise

        return self._stream.socket

    def _negotiate(self):
        proto = self._create_proto()
        proto.negotiate()

    def _create_proto(self):
        raise NotImplementedError()  # pragma: no cover

    @property
    def proxy_host(self):
        return self._proxy_host

    @property
    def proxy_port(self):
        return self._proxy_port


class Socks5Proxy(BaseProxy):
    def __init__(self, proxy_host, proxy_port,
                 username=None, password=None, rdns=None):
        super().__init__(
            proxy_host=proxy_host,
            proxy_port=proxy_port
        )
        self._username = username
        self._password = password
        self._rdns = rdns

    def _create_proto(self):
        return Socks5Proto(
            stream=self._stream,
            dest_host=self._dest_host,
            dest_port=self._dest_port,
            username=self._username,
            password=self._password,
            rdns=self._rdns
        )


class Socks4Proxy(BaseProxy):
    def __init__(self, proxy_host, proxy_port,
                 user_id=None, rdns=None):
        super().__init__(
            proxy_host=proxy_host,
            proxy_port=proxy_port
        )
        self._user_id = user_id
        self._rdns = rdns

    def _create_proto(self):
        return Socks4Proto(
            stream=self._stream,
            dest_host=self._dest_host,
            dest_port=self._dest_port,
            user_id=self._user_id,
            rdns=self._rdns
        )


class HttpProxy(BaseProxy):
    def __init__(self, proxy_host, proxy_port, username=None, password=None):
        super().__init__(
            proxy_host=proxy_host,
            proxy_port=proxy_port
        )
        self._username = username
        self._password = password

    def _create_proto(self):
        return HttpProto(
            stream=self._stream,
            dest_host=self._dest_host,
            dest_port=self._dest_port,
            username=self._username,
            password=self._password
        )
