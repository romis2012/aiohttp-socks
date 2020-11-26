from unittest import mock

import pytest  # noqa

# noinspection PyProtectedMember
from python_socks._resolver_async_aio import Resolver as AsyncioResolver
from tests.config import (
    PROXY_HOST_IPV4, PROXY_HOST_IPV6,
    SOCKS5_PROXY_PORT, LOGIN, PASSWORD, SKIP_IPV6_TESTS,
    HTTP_PROXY_PORT,
    SOCKS4_PORT_NO_AUTH, SOCKS4_PROXY_PORT,
    SOCKS5_PROXY_PORT_NO_AUTH, TEST_PORT_IPV4, TEST_PORT_IPV6, TEST_HOST_IPV4,
    TEST_HOST_IPV6, TEST_PORT_IPV4_HTTPS, TEST_HOST_CERT_FILE,
    TEST_HOST_KEY_FILE,
)
from tests.http_server import HttpServer, HttpServerConfig
from tests.mocks import async_resolve_factory
from tests.proxy_server import ProxyConfig, ProxyServer


@pytest.fixture(scope='session', autouse=True)
def patch_resolvers():
    with mock.patch.object(
            AsyncioResolver,
            attribute='resolve',
            new=async_resolve_factory(AsyncioResolver)
    ):
        yield None


@pytest.fixture(scope='session', autouse=True)
def proxy_server():
    config = [
        ProxyConfig(
            proxy_type='http',
            host=PROXY_HOST_IPV4,
            port=HTTP_PROXY_PORT,
            username=LOGIN,
            password=PASSWORD
        ),
        ProxyConfig(
            proxy_type='socks4',
            host=PROXY_HOST_IPV4,
            port=SOCKS4_PROXY_PORT,
            username=LOGIN,
            password=None
        ),
        ProxyConfig(
            proxy_type='socks4',
            host=PROXY_HOST_IPV4,
            port=SOCKS4_PORT_NO_AUTH,
            username=None,
            password=None
        ),
        ProxyConfig(
            proxy_type='socks5',
            host=PROXY_HOST_IPV4,
            port=SOCKS5_PROXY_PORT,
            username=LOGIN,
            password=PASSWORD
        ),
        ProxyConfig(
            proxy_type='socks5',
            host=PROXY_HOST_IPV4,
            port=SOCKS5_PROXY_PORT_NO_AUTH,
            username=None,
            password=None
        ),
    ]

    if not SKIP_IPV6_TESTS:
        config.append(
            ProxyConfig(
                proxy_type='socks5',
                host=PROXY_HOST_IPV6,
                port=SOCKS5_PROXY_PORT,
                username=LOGIN,
                password=PASSWORD
            ),
        )

    server = ProxyServer(config=config)
    server.start()
    for cfg in config:
        server.wait_until_connectable(host=cfg.host, port=cfg.port)

    yield None

    server.terminate()


@pytest.fixture(scope='session', autouse=True)
def web_server():
    config = [
        HttpServerConfig(
            host=TEST_HOST_IPV4,
            port=TEST_PORT_IPV4
        ),
        HttpServerConfig(
            host=TEST_HOST_IPV4,
            port=TEST_PORT_IPV4_HTTPS,
            certfile=TEST_HOST_CERT_FILE,
            keyfile=TEST_HOST_KEY_FILE,
        )
    ]

    if not SKIP_IPV6_TESTS:
        config.append(
            HttpServerConfig(
                host=TEST_HOST_IPV6,
                port=TEST_PORT_IPV6
            )
        )

    server = HttpServer(config=config)
    server.start()
    for cfg in config:
        server.wait_until_connectable(host=cfg.host, port=cfg.port)

    yield None

    server.terminate()
