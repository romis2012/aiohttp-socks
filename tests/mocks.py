import socket

from tests.config import (
    TEST_HOST_NAME_IPV4,
    PROXY_HOST_NAME_IPV4,
    TEST_HOST_NAME_IPV6,
    PROXY_HOST_NAME_IPV6
)


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

        return original_resolver(
            self, host=host, port=port,
            family=family)

    return new_resolver


def async_resolve_factory(cls):
    original_resolver = cls.resolve

    async def new_resolver(self, host, port=0, family=socket.AF_UNSPEC):
        res = _resolve_local(host)

        if res is not None:
            return res

        return await original_resolver(self, host=host, port=port,
                                       family=family)

    return new_resolver
