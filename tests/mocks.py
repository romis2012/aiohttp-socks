import socket

from tests.config import (
    TEST_HOST_NAME_IPV4,
    PROXY_HOST_NAME_IPV4,
    TEST_HOST_NAME_IPV6,
    PROXY_HOST_NAME_IPV6,
)


def getaddrinfo_sync_mock():
    _orig_getaddrinfo = socket.getaddrinfo

    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host in (TEST_HOST_NAME_IPV4, PROXY_HOST_NAME_IPV4):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', port))]

        if host in (TEST_HOST_NAME_IPV6, PROXY_HOST_NAME_IPV6):
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', port, 0, 0))]

        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    return getaddrinfo


def getaddrinfo_async_mock(origin_getaddrinfo):
    async def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host in (TEST_HOST_NAME_IPV4, PROXY_HOST_NAME_IPV4):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', port))]

        if host in (TEST_HOST_NAME_IPV6, PROXY_HOST_NAME_IPV6):
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', port, 0, 0))]

        return await origin_getaddrinfo(
            host,
            port,
            family=family,
            type=type,
            proto=proto,
            flags=flags,
        )

    return getaddrinfo


def _resolve_local(host):
    if host in (TEST_HOST_NAME_IPV4, PROXY_HOST_NAME_IPV4):
        return socket.AF_INET, '127.0.0.1'

    if host in (TEST_HOST_NAME_IPV6, PROXY_HOST_NAME_IPV6):
        return socket.AF_INET6, '::1'

    return None


def sync_resolve_factory(cls):
    original_resolver = cls.resolve

    def new_resolver(self, host, port=0, family=socket.AF_UNSPEC):
        res = _resolve_local(host)

        if res is not None:
            return res

        return original_resolver(self, host=host, port=port, family=family)

    return new_resolver


def async_resolve_factory(cls):
    original_resolver = cls.resolve

    async def new_resolver(self, host, port=0, family=socket.AF_UNSPEC):
        res = _resolve_local(host)

        if res is not None:
            return res

        return await original_resolver(self, host=host, port=port, family=family)

    return new_resolver
