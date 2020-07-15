import socket
import ssl
import trio  # noqa

import pytest  # noqa
from yarl import URL  # noqa

from aiohttp_socks.core_socks import (
    ProxyType,
    ProxyError,
    ProxyTimeoutError,
    ProxyConnectionError
)

from aiohttp_socks.core_socks._proxy_async import AsyncProxy  # noqa
from aiohttp_socks.core_socks.async_.trio import Proxy
from aiohttp_socks.core_socks.async_ import ProxyChain
# noinspection PyUnresolvedReferences,PyProtectedMember
from aiohttp_socks.core_socks._resolver_async_trio import Resolver

from tests.conftest import (
    SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT, LOGIN, PASSWORD, SKIP_IPV6_TESTS,
    SOCKS5_IPV4_URL, SOCKS5_IPV4_URL_WO_AUTH, SOCKS5_IPV6_URL, SOCKS4_URL,
    HTTP_PROXY_URL
)

# TEST_URL = 'https://httpbin.org/ip'
TEST_URL = 'https://check-host.net/ip'


async def make_request(proxy: AsyncProxy,
                       url: str, resolve_host=False, timeout=None):
    url = URL(url)

    dest_host = url.host
    if resolve_host:
        resolver = Resolver()
        _, dest_host = await resolver.resolve(url.host)

    sock: socket.socket = await proxy.connect(
        dest_host=dest_host,
        dest_port=url.port,
        timeout=timeout
    )

    ssl_context = None
    if url.scheme == 'https':
        ssl_context = ssl.create_default_context()

    stream = trio.SocketStream(sock)

    if ssl_context is not None:
        stream = trio.SSLStream(
            stream, ssl_context,
            server_hostname=url.host
        )
        await stream.do_handshake()

    request = (
        'GET {rel_url} HTTP/1.1\r\n'
        'Host: {host}\r\n'
        'Connection: close\r\n\r\n'
    )
    request = request.format(rel_url=url.path_qs, host=url.host)
    request = request.encode('ascii')

    await stream.send_all(request)

    response = await stream.receive_some(1024)

    status_line = response.split(b'\r\n', 1)[0]
    status_line = status_line.decode('utf-8', 'surrogateescape')
    version, status_code, *reason = status_line.split()

    return int(status_code)


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.parametrize('resolve_host', (True, False))
@pytest.mark.trio
async def test_socks5_proxy_ipv4(rdns, resolve_host):
    proxy = Proxy.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    status_code = await make_request(
        proxy=proxy,
        url=TEST_URL,
        resolve_host=resolve_host
    )
    assert status_code == 200


@pytest.mark.parametrize('rdns', (None, True, False))
@pytest.mark.trio
async def test_socks5_proxy_ipv4_with_auth_none(rdns):
    proxy = Proxy.from_url(SOCKS5_IPV4_URL_WO_AUTH, rdns=rdns)
    status_code = await make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200


@pytest.mark.trio
async def test_socks5_proxy_with_invalid_credentials():
    proxy = Proxy.create(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(ProxyError):
        await make_request(proxy=proxy, url=TEST_URL)


@pytest.mark.trio
async def test_socks5_proxy_with_connect_timeout():
    proxy = Proxy.create(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyTimeoutError):
        await make_request(proxy=proxy, url=TEST_URL, timeout=0.0001)


@pytest.mark.trio
async def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port):
    proxy = Proxy.create(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyConnectionError):
        await make_request(proxy=proxy, url=TEST_URL)


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
@pytest.mark.trio
async def test_socks5_proxy_ipv6():
    proxy = Proxy.from_url(SOCKS5_IPV6_URL)
    status_code = await make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200


@pytest.mark.parametrize('rdns', (None, True, False))
@pytest.mark.parametrize('resolve_host', (True, False))
@pytest.mark.trio
async def test_socks4_proxy(rdns, resolve_host):
    proxy = Proxy.from_url(SOCKS4_URL, rdns=rdns)
    status_code = await make_request(
        proxy=proxy,
        url=TEST_URL,
        resolve_host=resolve_host
    )
    assert status_code == 200


@pytest.mark.trio
async def test_http_proxy():
    proxy = Proxy.from_url(HTTP_PROXY_URL)
    status_code = await make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200


@pytest.mark.trio
async def test_proxy_chain():
    proxy = ProxyChain([
        Proxy.from_url(SOCKS5_IPV4_URL),
        Proxy.from_url(SOCKS4_URL),
        Proxy.from_url(HTTP_PROXY_URL),
    ])
    # noinspection PyTypeChecker
    status_code = await make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200
