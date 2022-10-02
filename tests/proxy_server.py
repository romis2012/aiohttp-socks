import ssl
import typing
from multiprocessing import Process
from unittest import mock

import anyio
from anyio import create_tcp_listener
from anyio.streams.tls import TLSListener
from tiny_proxy import (
    HttpProxyHandler,
    Socks5ProxyHandler,
    Socks4ProxyHandler,
    HttpProxy,
    Socks4Proxy,
    Socks5Proxy,
    AbstractProxy,
)

from tests.mocks import getaddrinfo_async_mock


class ProxyConfig(typing.NamedTuple):
    proxy_type: str
    host: str
    port: int
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None
    ssl_certfile: typing.Optional[str] = None
    ssl_keyfile: typing.Optional[str] = None

    def to_dict(self):
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val
        return d


cls_map = {
    'http': HttpProxyHandler,
    'socks4': Socks4ProxyHandler,
    'socks5': Socks5ProxyHandler,
}


def connect_to_remote_factory(cls: typing.Type[AbstractProxy]):
    """
    simulate target host connection timeout
    """
    origin_connect_to_remote = cls.connect_to_remote

    async def new_connect_to_remote(self):
        await anyio.sleep(0.01)
        return await origin_connect_to_remote(self)

    return new_connect_to_remote


@mock.patch.object(
    HttpProxy,
    attribute='connect_to_remote',
    new=connect_to_remote_factory(HttpProxy),
)
@mock.patch.object(
    Socks4Proxy,
    attribute='connect_to_remote',
    new=connect_to_remote_factory(Socks4Proxy),
)
@mock.patch.object(
    Socks5Proxy,
    attribute='connect_to_remote',
    new=connect_to_remote_factory(Socks5Proxy),
)
@mock.patch('anyio._core._sockets.getaddrinfo', new=getaddrinfo_async_mock(anyio.getaddrinfo))
def start(
    proxy_type,
    host,
    port,
    ssl_certfile=None,
    ssl_keyfile=None,
    **kwargs,
):
    handler_cls = cls_map.get(proxy_type)
    if not handler_cls:
        raise RuntimeError(f'Unsupported type: {proxy_type}')

    if ssl_certfile and ssl_keyfile:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_certfile, ssl_keyfile)
    else:
        ssl_context = None

    print(f'Starting {proxy_type} proxy on {host}:{port}...')

    handler = handler_cls(**kwargs)

    async def serve():
        listener = await create_tcp_listener(local_host=host, local_port=port)
        if ssl_context is not None:
            listener = TLSListener(listener=listener, ssl_context=ssl_context)

        async with listener:
            await listener.serve(handler.handle)

    anyio.run(serve)


class ProxyServer:
    workers: typing.List[Process]

    def __init__(self, config: typing.Iterable[ProxyConfig]):
        self.config = config
        self.workers = []

    def start(self):
        for cfg in self.config:
            print(
                'Starting {} proxy on {}:{}; certfile={}, keyfile={}...'.format(
                    cfg.proxy_type,
                    cfg.host,
                    cfg.port,
                    cfg.ssl_certfile,
                    cfg.ssl_keyfile,
                )
            )

            p = Process(target=start, kwargs=cfg.to_dict(), daemon=True)
            self.workers.append(p)

        for p in self.workers:
            p.start()

    def terminate(self):
        for p in self.workers:
            p.terminate()
