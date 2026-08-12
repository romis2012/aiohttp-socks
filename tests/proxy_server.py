from __future__ import annotations

import functools
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from ssl import SSLContext
from typing import Any
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

PROXY_HANDLERS = {
    "http": HttpProxyHandler,
    "socks4": Socks4ProxyHandler,
    "socks5": Socks5ProxyHandler,
}


@dataclass
class ProxyConfig:
    proxy_type: str
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    ssl_context: SSLContext | None = None

    def to_dict(self) -> dict[str, Any]:
        # TypeError: cannot pickle 'SSLContext' object
        # return {k: v for k, v in asdict(self).items() if v is not None}
        return {k: v for k, v in self.__dict__.items() if v is not None}


def connect_to_remote_factory(
    cls: type[AbstractProxy],
) -> Callable[[AbstractProxy], SocketStream]:
    """
    simulate target host connection timeout
    """
    origin_connect_to_remote = cls.connect_to_remote

    async def new_connect_to_remote(self: AbstractProxy) -> SocketStream:
        await anyio.sleep(0.01)
        return await origin_connect_to_remote(self)

    return new_connect_to_remote


async def serve(
    proxy_type: str,
    host: str,
    port: int,
    ssl_context: SSLContext | None = None,
    **kwargs: Any,
) -> None:
    handler_cls = PROXY_HANDLERS.get(proxy_type)
    if not handler_cls:
        raise RuntimeError(f"Unsupported type: {proxy_type}")

    print(f"Starting {proxy_type} proxy on {host}:{port}...")

    handler = handler_cls(**kwargs)

    listener = await create_tcp_listener(local_host=host, local_port=port)
    if ssl_context is not None:
        listener = TLSListener(listener=listener, ssl_context=ssl_context)  # type:ignore[assignment]

    async with listener:
        await listener.serve(handler.handle)


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
async def serve_multiple(
    config: Iterable[ProxyConfig],
    stop_event: threading.Event,
) -> None:
    async with anyio.create_task_group() as tg:
        for cfg in config:
            tg.start_soon(functools.partial(serve, **cfg.to_dict()))

        while not stop_event.is_set():  # noqa: ASYNC110
            await anyio.sleep(0.1)

        tg.cancel_scope.cancel()


class ProxyServer:
    def __init__(self, config: Iterable[ProxyConfig]) -> None:
        self.config = config
        self.stop_event = threading.Event()
        self.server_thread = threading.Thread(target=self.do_start, daemon=True)

    def do_start(self) -> None:
        anyio.run(serve_multiple, self.config, self.stop_event)

    def start(self) -> None:
        self.server_thread.start()

    def shutdown(self) -> None:
        self.stop_event.set()
        self.server_thread.join(timeout=2)
