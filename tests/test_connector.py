import asyncio
import ssl

import aiohttp
import pytest  # noqa
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

from tests.conftest import (
    SOCKS5_IPV4_HOST,
    SOCKS5_IPV4_PORT,
    LOGIN, PASSWORD,
    SOCKS4_HOST,
    SOCKS4_PORT,
    HTTP_PROXY_HOST,
    HTTP_PROXY_PORT,
    SKIP_IPV6_TESTS,
    SOCKS5_IPV4_URL,
    SOCKS5_IPV6_URL,
    SOCKS4_URL,
    HTTP_PROXY_URL)

# HTTP_TEST_URL = 'http://httpbin.org/ip'
# HTTPS_TEST_URL = 'https://httpbin.org/ip'
HTTP_TEST_URL = 'http://check-host.net/ip'
HTTPS_TEST_URL = 'https://check-host.net/ip'

HTTP_URL_DELAY_3_SEC = 'http://httpbin.org/delay/3'
HTTP_URL_REDIRECT = 'http://httpbin.org/redirect/1'


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_proxy_ipv4(url, rdns):
    connector = ProxyConnector.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_credentials():
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(ProxyError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(HTTP_TEST_URL) as resp:
                await resp.text()


@pytest.mark.asyncio
async def test_socks5_proxy_with_timeout():
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(asyncio.TimeoutError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(HTTP_URL_DELAY_3_SEC, timeout=1) as resp:
                await resp.text()


@pytest.mark.asyncio
async def test_socks5_proxy_with_proxy_connect_timeout():
    connector = ProxyConnector.from_url(SOCKS5_IPV4_URL)
    timeout = aiohttp.ClientTimeout(total=32, sock_connect=0.001)
    with pytest.raises(ProxyTimeoutError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(HTTP_TEST_URL, timeout=timeout) as resp:
                await resp.text()


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port):
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyConnectionError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(HTTP_TEST_URL) as resp:
                await resp.text()


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
@pytest.mark.asyncio
async def test_socks5_proxy_ipv6():
    connector = ProxyConnector.from_url(SOCKS5_IPV6_URL)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(HTTP_TEST_URL) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_proxy(url, rdns):
    connector = ProxyConnector.from_url(SOCKS4_URL, rdns=rdns, )
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.asyncio
async def test_http_proxy(url):
    connector = ProxyConnector.from_url(HTTP_PROXY_URL)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.asyncio
async def test_chain_proxy_from_url(url):
    connector = ChainProxyConnector.from_urls([
        SOCKS5_IPV4_URL,
        SOCKS4_URL,
        HTTP_PROXY_URL
    ])
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_chain_proxy_ctor(url, rdns):
    connector = ChainProxyConnector([
        ProxyInfo(
            proxy_type=ProxyType.SOCKS5,
            host=SOCKS5_IPV4_HOST,
            port=SOCKS5_IPV4_PORT,
            username=LOGIN,
            password=PASSWORD,
            rdns=rdns
        ),
        ProxyInfo(
            proxy_type=ProxyType.SOCKS4,
            host=SOCKS4_HOST,
            port=SOCKS4_PORT,
            rdns=rdns
        ),
        ProxyInfo(
            proxy_type=ProxyType.HTTP,
            host=HTTP_PROXY_HOST,
            port=HTTP_PROXY_PORT,
            username=LOGIN,
            password=PASSWORD
        ),
    ])
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_http_open_connection(rdns):
    url = URL(HTTP_TEST_URL)

    reader, writer = await open_connection(
        proxy_url=SOCKS5_IPV4_URL,
        host=url.host,
        port=url.port,
        rdns=rdns,
    )
    request = ("GET %s HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % (url.path_qs, url.host))

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_https_open_connection(rdns):
    url = URL(HTTPS_TEST_URL)

    reader, writer = await open_connection(
        proxy_url=SOCKS5_IPV4_URL,
        host=url.host,
        port=url.port,
        ssl=ssl.create_default_context(),
        server_hostname=url.host,
        rdns=rdns,
    )
    request = ("GET %s HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % (url.path_qs, url.host))

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_http_open_connection(rdns):
    url = URL(HTTP_TEST_URL)

    reader, writer = await open_connection(
        proxy_url=SOCKS4_URL,
        host=url.host,
        port=url.port,
        rdns=rdns,
    )
    request = ("GET %s HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % (url.path_qs, url.host))

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response


@pytest.mark.asyncio
async def test_socks5_http_create_connection(event_loop):
    url = URL(HTTP_TEST_URL)

    reader = asyncio.StreamReader(loop=event_loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=event_loop)

    transport, _ = await create_connection(
        proxy_url=SOCKS5_IPV4_URL,
        protocol_factory=lambda: protocol,
        host=url.host,
        port=url.port,
    )

    writer = asyncio.StreamWriter(transport, protocol, reader, event_loop)

    request = ("GET %s HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % (url.path_qs, url.host))

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response
