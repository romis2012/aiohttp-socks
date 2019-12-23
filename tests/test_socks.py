import asyncio
import socket
import ssl

import aiohttp
# noinspection PyPackageRequirements
import pytest

from aiohttp_socks import (
    ProxyType, ProxyConnector, ChainProxyConnector, ProxyInfo,
    ProxyError, ProxyConnectionError,
    open_connection, create_connection)

from tests.conftest import (
    SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT,
    LOGIN, PASSWORD, SOCKS5_IPV6_HOST,
    SOCKS5_IPV6_PORT, SOCKS4_HOST, SOCKS4_PORT,
    HTTP_PROXY_HOST, HTTP_PROXY_PORT,
    SKIP_IPV6_TESTS)

HTTP_TEST_HOST = 'httpbin.org'
HTTP_TEST_PORT = 80

HTTPS_TEST_HOST = 'httpbin.org'
HTTPS_TEST_PORT = 443

HTTP_TEST_URL = 'http://%s/ip' % HTTP_TEST_HOST
HTTPS_TEST_URL = 'https://%s/ip' % HTTP_TEST_HOST

HTTP_URL_DELAY_3_SEC = 'http://httpbin.org/delay/3'
HTTP_URL_REDIRECT = 'http://httpbin.org/redirect/1'

SOCKS5_IPV4_URL = 'socks5://{LOGIN}:{PASSWORD}@{SOCKS5_IPV4_HOST}:{SOCKS5_IPV4_PORT}'.format(  # noqa
    SOCKS5_IPV4_HOST=SOCKS5_IPV4_HOST,
    SOCKS5_IPV4_PORT=SOCKS5_IPV4_PORT,
    LOGIN=LOGIN,
    PASSWORD=PASSWORD,
)

SOCKS5_IPV6_URL = 'socks5://{LOGIN}:{PASSWORD}@{SOCKS5_IPV6_HOST}:{SOCKS5_IPV6_PORT}'.format(  # noqa
    SOCKS5_IPV6_HOST='[%s]' % SOCKS5_IPV6_HOST,
    SOCKS5_IPV6_PORT=SOCKS5_IPV6_PORT,
    LOGIN=LOGIN,
    PASSWORD=PASSWORD,
)

SOCKS4_URL = 'socks4://{SOCKS4_HOST}:{SOCKS4_PORT}'.format(
    SOCKS4_HOST=SOCKS4_HOST,
    SOCKS4_PORT=SOCKS4_PORT,
)

HTTP_PROXY_URL = 'http://{LOGIN}:{PASSWORD}@{HTTP_PROXY_HOST}:{HTTP_PROXY_PORT}'.format(  # noqa
    HTTP_PROXY_HOST=HTTP_PROXY_HOST,
    HTTP_PROXY_PORT=HTTP_PROXY_PORT,
    LOGIN=LOGIN,
    PASSWORD=PASSWORD,
)


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
    connector = ProxyConnector.from_url(SOCKS5_IPV6_URL,
                                        family=socket.AF_INET6)
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
    reader, writer = await open_connection(
        proxy_url=SOCKS5_IPV4_URL,
        host=HTTP_TEST_HOST,
        port=HTTP_TEST_PORT,
        rdns=rdns,
    )
    request = ("GET /ip HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % HTTP_TEST_HOST)

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_https_open_connection(rdns):
    reader, writer = await open_connection(
        proxy_url=SOCKS5_IPV4_URL,
        host=HTTPS_TEST_HOST,
        port=HTTPS_TEST_PORT,
        ssl=ssl.create_default_context(),
        server_hostname=HTTPS_TEST_HOST,
        rdns=rdns,
    )
    request = ("GET /ip HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % HTTPS_TEST_HOST)

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_http_open_connection(rdns):
    reader, writer = await open_connection(
        proxy_url=SOCKS4_URL,
        host=HTTP_TEST_HOST,
        port=HTTP_TEST_PORT,
        rdns=rdns,
    )
    request = ("GET /ip HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % HTTP_TEST_HOST)

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response


@pytest.mark.asyncio
async def test_socks5_http_create_connection(event_loop):
    reader = asyncio.StreamReader(loop=event_loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=event_loop)

    transport, _ = await create_connection(
        proxy_url=SOCKS5_IPV4_URL,
        protocol_factory=lambda: protocol,
        host=HTTP_TEST_HOST,
        port=HTTP_TEST_PORT,
    )

    writer = asyncio.StreamWriter(transport, protocol, reader, event_loop)

    request = ("GET /ip HTTP/1.1\r\n"
               "Host: %s\r\n"
               "Connection: close\r\n\r\n" % HTTP_TEST_HOST)

    writer.write(request.encode())
    response = await reader.read(-1)
    assert b'200 OK' in response
