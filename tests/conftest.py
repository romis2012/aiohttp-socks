import ssl
from unittest import mock

import pytest  # noqa
import trustme  # noqa
from python_socks.async_.asyncio._resolver import Resolver as AsyncioResolver

from tests.config import (
    HTTP_PROXY_PORT,
    LOGIN,
    PASSWORD,
    PROXY_HOST_IPV4,
    PROXY_HOST_IPV6,
    SKIP_IPV6_TESTS,
    SOCKS4_PORT_NO_AUTH,
    SOCKS4_PROXY_PORT,
    SOCKS5_PROXY_PORT,
    SOCKS5_PROXY_PORT_NO_AUTH,
    TEST_HOST_IPV4,
    TEST_HOST_IPV6,
    TEST_HOST_NAME_IPV4,
    TEST_HOST_NAME_IPV6,
    TEST_PORT_IPV4,
    TEST_PORT_IPV4_HTTPS,
    TEST_PORT_IPV6,
)
from tests.http_server import HttpServer, HttpServerConfig
from tests.mocks import async_resolve_factory
from tests.proxy_server import ProxyConfig, ProxyServer
from tests.utils import wait_until_connectable


@pytest.fixture(scope='session')
def target_ssl_ca() -> trustme.CA:
    return trustme.CA()


@pytest.fixture(scope='session')
def target_ssl_cert(target_ssl_ca) -> trustme.LeafCert:
    return target_ssl_ca.issue_cert(
        'localhost',
        TEST_HOST_IPV4,
        TEST_HOST_IPV6,
        TEST_HOST_NAME_IPV4,
        TEST_HOST_NAME_IPV6,
    )


@pytest.fixture(scope='session')
def target_ssl_certfile(target_ssl_cert):
    with target_ssl_cert.cert_chain_pems[0].tempfile() as cert_path:
        yield cert_path


@pytest.fixture(scope='session')
def target_ssl_keyfile(target_ssl_cert):
    with target_ssl_cert.private_key_pem.tempfile() as private_key_path:
        yield private_key_path


@pytest.fixture(scope='session')
def target_ssl_context(target_ssl_ca) -> ssl.SSLContext:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.check_hostname = True
    target_ssl_ca.configure_trust(ssl_ctx)
    return ssl_ctx


@pytest.fixture(scope='session', autouse=True)
def patch_resolvers():
    with mock.patch.object(
        AsyncioResolver, attribute='resolve', new=async_resolve_factory(AsyncioResolver)
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
            password=PASSWORD,
        ),
        ProxyConfig(
            proxy_type='socks4',
            host=PROXY_HOST_IPV4,
            port=SOCKS4_PROXY_PORT,
            username=LOGIN,
            password=None,
        ),
        ProxyConfig(
            proxy_type='socks4',
            host=PROXY_HOST_IPV4,
            port=SOCKS4_PORT_NO_AUTH,
            username=None,
            password=None,
        ),
        ProxyConfig(
            proxy_type='socks5',
            host=PROXY_HOST_IPV4,
            port=SOCKS5_PROXY_PORT,
            username=LOGIN,
            password=PASSWORD,
        ),
        ProxyConfig(
            proxy_type='socks5',
            host=PROXY_HOST_IPV4,
            port=SOCKS5_PROXY_PORT_NO_AUTH,
            username=None,
            password=None,
        ),
    ]

    if not SKIP_IPV6_TESTS:
        config.append(
            ProxyConfig(
                proxy_type='socks5',
                host=PROXY_HOST_IPV6,
                port=SOCKS5_PROXY_PORT,
                username=LOGIN,
                password=PASSWORD,
            ),
        )

    server = ProxyServer(config=config)
    server.start()
    for cfg in config:
        wait_until_connectable(host=cfg.host, port=cfg.port, timeout=10)

    yield None

    server.terminate()


@pytest.fixture(scope='session', autouse=True)
def web_server(target_ssl_certfile, target_ssl_keyfile):
    config = [
        HttpServerConfig(host=TEST_HOST_IPV4, port=TEST_PORT_IPV4),
        HttpServerConfig(
            host=TEST_HOST_IPV4,
            port=TEST_PORT_IPV4_HTTPS,
            certfile=target_ssl_certfile,
            keyfile=target_ssl_keyfile,
        ),
    ]

    if not SKIP_IPV6_TESTS:
        config.append(HttpServerConfig(host=TEST_HOST_IPV6, port=TEST_PORT_IPV6))

    server = HttpServer(config=config)
    server.start()
    for cfg in config:
        server.wait_until_connectable(host=cfg.host, port=cfg.port)

    yield None

    server.terminate()
