import asyncio

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
from tests.config import (
    TEST_URL_IPV4,
    SOCKS5_IPV4_URL, PROXY_HOST_IPV4, SOCKS5_PROXY_PORT, LOGIN,
    PASSWORD, TEST_URL_IPV4_DELAY, SKIP_IPV6_TESTS, SOCKS5_IPV6_URL,
    SOCKS4_URL, HTTP_PROXY_URL, SOCKS4_PROXY_PORT, HTTP_PROXY_PORT,
)


@pytest.mark.parametrize('url', (TEST_URL_IPV4,))
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
        host=PROXY_HOST_IPV4,
        port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(ProxyError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(TEST_URL_IPV4) as resp:
                await resp.text()


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
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(TEST_URL_IPV4_DELAY, timeout=1) as resp:
                await resp.text()


@pytest.mark.asyncio
async def test_socks5_proxy_with_proxy_connect_timeout():
    connector = ProxyConnector.from_url(SOCKS5_IPV4_URL)
    timeout = aiohttp.ClientTimeout(total=32, sock_connect=0.001)
    with pytest.raises(ProxyTimeoutError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(TEST_URL_IPV4, timeout=timeout) as resp:
                await resp.text()


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
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(TEST_URL_IPV4) as resp:
                await resp.text()


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
@pytest.mark.asyncio
async def test_socks5_proxy_ipv6():
    connector = ProxyConnector.from_url(SOCKS5_IPV6_URL)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(TEST_URL_IPV4) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4,))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_proxy(url, rdns):
    connector = ProxyConnector.from_url(SOCKS4_URL, rdns=rdns, )
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4,))
@pytest.mark.asyncio
async def test_http_proxy(url):
    connector = ProxyConnector.from_url(HTTP_PROXY_URL)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4,))
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


@pytest.mark.parametrize('url', (TEST_URL_IPV4,))
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
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_http_open_connection(rdns):
    url = URL(TEST_URL_IPV4)

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


# @pytest.mark.parametrize('rdns', (True, False))
# @pytest.mark.asyncio
# async def test_socks5_https_open_connection(rdns):
#     url = URL(TEST_URL_IPV4)
#
#     reader, writer = await open_connection(
#         proxy_url=SOCKS5_IPV4_URL,
#         host=url.host,
#         port=url.port,
#         ssl=ssl.create_default_context(),
#         server_hostname=url.host,
#         rdns=rdns,
#     )
#     request = ("GET %s HTTP/1.1\r\n"
#                "Host: %s\r\n"
#                "Connection: close\r\n\r\n" % (url.path_qs, url.host))
#
#     writer.write(request.encode())
#     response = await reader.read(-1)
#     assert b'200 OK' in response


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_http_open_connection(rdns):
    url = URL(TEST_URL_IPV4)

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
    url = URL(TEST_URL_IPV4)

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
