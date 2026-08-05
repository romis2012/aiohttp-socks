from __future__ import annotations

import socket
from collections.abc import Awaitable, Callable
from typing import Any

from tests.config import (
    PROXY_HOST_NAME_IPV4,
    PROXY_HOST_NAME_IPV6,
    TEST_HOST_NAME_IPV4,
    TEST_HOST_NAME_IPV6,
)


def getaddrinfo_sync_mock() -> Callable[..., Any]:
    _orig_getaddrinfo = socket.getaddrinfo

    def getaddrinfo(
        host: str,
        port: int,
        family: int = 0,
        type: int = 0,  # noqa: A002
        proto: int = 0,
        flags: int = 0,
    ) -> Any:
        if host in (TEST_HOST_NAME_IPV4, PROXY_HOST_NAME_IPV4):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

        if host in (TEST_HOST_NAME_IPV6, PROXY_HOST_NAME_IPV6):
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", port, 0, 0))]

        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    return getaddrinfo


def getaddrinfo_async_mock(
    origin_getaddrinfo: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def getaddrinfo(
        host: str,
        port: int,
        family: int = 0,
        type: int = 0,  # noqa: A002
        proto: int = 0,
        flags: int = 0,
    ) -> Any:
        if host in (TEST_HOST_NAME_IPV4, PROXY_HOST_NAME_IPV4):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

        if host in (TEST_HOST_NAME_IPV6, PROXY_HOST_NAME_IPV6):
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", port, 0, 0))]

        return await origin_getaddrinfo(
            host,
            port,
            family=family,
            type=type,
            proto=proto,
            flags=flags,
        )

    return getaddrinfo


def _resolve_local(host: str) -> tuple[socket.AddressFamily, str] | None:
    if host in (TEST_HOST_NAME_IPV4, PROXY_HOST_NAME_IPV4):
        return socket.AF_INET, "127.0.0.1"

    if host in (TEST_HOST_NAME_IPV6, PROXY_HOST_NAME_IPV6):
        return socket.AF_INET6, "::1"

    return None


def sync_resolve_factory(cls: Any) -> Callable[..., tuple[socket.AddressFamily, str]]:
    original_resolver = cls.resolve

    def new_resolver(
        self: Any,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_UNSPEC,
    ) -> tuple[socket.AddressFamily, str]:
        res = _resolve_local(host)

        if res is not None:
            return res

        return original_resolver(self, host=host, port=port, family=family)

    return new_resolver


def async_resolve_factory(
    cls: Any,
) -> Callable[..., Awaitable[tuple[socket.AddressFamily, str]]]:
    original_resolver = cls.resolve

    async def new_resolver(
        self: Any,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_UNSPEC,
    ) -> tuple[socket.AddressFamily, str]:
        res = _resolve_local(host)

        if res is not None:
            return res

        return await original_resolver(self, host=host, port=port, family=family)

    return new_resolver
