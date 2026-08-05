from __future__ import annotations

import ssl
from collections.abc import Awaitable, Callable, Iterable
from multiprocessing import Process
from typing import Any, NamedTuple
from unittest import mock

import anyio
from anyio import create_tcp_listener
from anyio.streams.tls import TLSListener
from tiny_proxy import (
    AbstractProxy,
    HttpProxy,
    HttpProxyHandler,
    SocketStream,
    Socks4Proxy,
    Socks4ProxyHandler,
    Socks5Proxy,
    Socks5ProxyHandler,
)

from tests.mocks import getaddrinfo_async_mock


class ProxyConfig(NamedTuple):
    proxy_type: str
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val  # noqa: PERF403
        return d


cls_map = {
    "http": HttpProxyHandler,
    "socks4": Socks4ProxyHandler,
    "socks5": Socks5ProxyHandler,
}


def connect_to_remote_factory(
    cls: type[AbstractProxy],
) -> Callable[[AbstractProxy], Awaitable[SocketStream]]:
    """
    simulate target host connection timeout
    """
    origin_connect_to_remote = cls.connect_to_remote

    async def new_connect_to_remote(self: AbstractProxy) -> SocketStream:
        await anyio.sleep(0.01)
        return await origin_connect_to_remote(self)

    return new_connect_to_remote


@mock.patch.object(
    HttpProxy,
    attribute="connect_to_remote",
    new=connect_to_remote_factory(HttpProxy),
)
@mock.patch.object(
    Socks4Proxy,
    attribute="connect_to_remote",
    new=connect_to_remote_factory(Socks4Proxy),
)
@mock.patch.object(
    Socks5Proxy,
    attribute="connect_to_remote",
    new=connect_to_remote_factory(Socks5Proxy),
)
@mock.patch(
    "anyio._core._sockets.getaddrinfo",
    new=getaddrinfo_async_mock(anyio.getaddrinfo),
)
def start(
    proxy_type: str,
    host: str,
    port: int,
    ssl_certfile: str | None = None,
    ssl_keyfile: str | None = None,
    **kwargs: Any,
) -> None:
    handler_cls = cls_map.get(proxy_type)
    if not handler_cls:
        raise RuntimeError(f"Unsupported type: {proxy_type}")

    if ssl_certfile and ssl_keyfile:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_certfile, ssl_keyfile)
    else:
        ssl_context = None

    print(f"Starting {proxy_type} proxy on {host}:{port}...")

    handler = handler_cls(**kwargs)

    async def serve():  # noqa: ANN202
        listener = await create_tcp_listener(local_host=host, local_port=port)
        if ssl_context is not None:
            listener = TLSListener(listener=listener, ssl_context=ssl_context)

        async with listener:
            await listener.serve(handler.handle)

    anyio.run(serve)


class ProxyServer:
    def __init__(self, config: Iterable[ProxyConfig]) -> None:
        self.config = config
        self.workers: list[Process] = []

    def start(self) -> None:
        for cfg in self.config:
            print(
                "Starting {} proxy on {}:{}; certfile={}, keyfile={}...".format(  # noqa: UP032
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

    def terminate(self) -> None:
        for p in self.workers:
            p.terminate()
