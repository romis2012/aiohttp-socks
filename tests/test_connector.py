import asyncio
import ssl

import aiohttp
import pytest  # noqa
from aiohttp import ClientResponse, TCPConnector
from yarl import URL  # noqa

from aiohttp_socks import (
    ProxyType,
    ProxyConnector,
    ChainProxyConnector,
    ProxyInfo,
    ProxyError,
    ProxyConnectionError,
    ProxyTimeoutError,
    open_connection,
    create_connection
)
from tests.config import (
    TEST_URL_IPV4,
    SOCKS5_IPV4_URL, PROXY_HOST_IPV4, SOCKS5_PROXY_PORT, LOGIN,
    PASSWORD, TEST_URL_IPV4_DELAY, SKIP_IPV6_TESTS, SOCKS5_IPV6_URL,
    SOCKS4_URL, HTTP_PROXY_URL, SOCKS4_PROXY_PORT, HTTP_PROXY_PORT,
    TEST_HOST_PEM_FILE, TEST_URL_IPV4_HTTPS,
)


def create_ssl_context():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(TEST_HOST_PEM_FILE)
    return ssl_context


async def fetch(connector: TCPConnector,
                url: str, timeout=None) -> ClientResponse:
    url = URL(url)

    ssl_context = None
    if url.scheme == 'https':
        ssl_context = create_ssl_context()

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, ssl=ssl_context, timeout=timeout) as resp:
            return resp


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_proxy_ipv4(url, rdns):
    connector = ProxyConnector.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    res = await fetch(connector=connector, url=url)
    assert res.status == 200


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_credentials():
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=PROXY_HOST_IPV4,
        port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(ProxyError):
        await fetch(connector=connector, url=TEST_URL_IPV4)


@pytest.mark.asyncio
async def test_socks5_proxy_with_timeout():
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=PROXY_HOST_IPV4,
        port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(asyncio.TimeoutError):
        await fetch(connector=connector, url=TEST_URL_IPV4_DELAY, timeout=1)


@pytest.mark.asyncio
async def test_socks5_proxy_with_proxy_connect_timeout():
    connector = ProxyConnector.from_url(SOCKS5_IPV4_URL)
    timeout = aiohttp.ClientTimeout(total=32, sock_connect=0.001)
    with pytest.raises(ProxyTimeoutError):
        await fetch(connector=connector, url=TEST_URL_IPV4, timeout=timeout)


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port):
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=PROXY_HOST_IPV4,
        port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyConnectionError):
        await fetch(connector=connector, url=TEST_URL_IPV4)


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.skipif(SKIP_IPV6_TESTS, reason="TravisCI doesn't support ipv6")
@pytest.mark.asyncio
async def test_socks5_proxy_ipv6(url):
    connector = ProxyConnector.from_url(SOCKS5_IPV6_URL)
    res = await fetch(connector=connector, url=url)
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_proxy(url, rdns):
    connector = ProxyConnector.from_url(SOCKS4_URL, rdns=rdns, )
    res = await fetch(connector=connector, url=url)
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.asyncio
async def test_http_proxy(url):
    connector = ProxyConnector.from_url(HTTP_PROXY_URL)
    res = await fetch(connector=connector, url=url)
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.asyncio
async def test_chain_proxy_from_url(url):
    connector = ChainProxyConnector.from_urls([
        SOCKS5_IPV4_URL,
        SOCKS4_URL,
        HTTP_PROXY_URL
    ])
    res = await fetch(connector=connector, url=url)
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_chain_proxy_ctor(url, rdns):
    connector = ChainProxyConnector([
        ProxyInfo(
            proxy_type=ProxyType.SOCKS5,
            host=PROXY_HOST_IPV4,
            port=SOCKS5_PROXY_PORT,
            username=LOGIN,
            password=PASSWORD,
            rdns=rdns
        ),
        ProxyInfo(
            proxy_type=ProxyType.SOCKS4,
            host=PROXY_HOST_IPV4,
            port=SOCKS4_PROXY_PORT,
            username=LOGIN,
            rdns=rdns
        ),
        ProxyInfo(
            proxy_type=ProxyType.HTTP,
            host=PROXY_HOST_IPV4,
            port=HTTP_PROXY_PORT,
            username=LOGIN,
            password=PASSWORD
        ),
    ])
    res = await fetch(connector=connector, url=url)
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_open_connection(url, rdns):
    url = URL(url)

    ssl_context = None
    if url.scheme == 'https':
        ssl_context = create_ssl_context()

    reader, writer = await open_connection(
        proxy_url=SOCKS5_IPV4_URL,
        host=url.host,
        port=url.port,
        ssl=ssl_context,
        server_hostname=url.host if ssl_context else None,
        rdns=rdns,
    )
    request = ("GET %s HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % (url.path_qs, url.host))

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_http_create_connection(url, rdns, event_loop):
    url = URL(url)

    ssl_context = None
    if url.scheme == 'https':
        ssl_context = create_ssl_context()

    reader = asyncio.StreamReader(loop=event_loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=event_loop)

    transport, _ = await create_connection(
        proxy_url=SOCKS5_IPV4_URL,
        protocol_factory=lambda: protocol,
        host=url.host,
        port=url.port,
        ssl=ssl_context,
        server_hostname=url.host if ssl_context else None,
        rdns=rdns,
    )

    writer = asyncio.StreamWriter(transport, protocol, reader, event_loop)

    request = ("GET %s HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % (url.path_qs, url.host))

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response
