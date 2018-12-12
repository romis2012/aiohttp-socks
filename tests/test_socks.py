import asyncio
import socket
import ssl

import aiohttp
# noinspection PyPackageRequirements
import pytest

from aiohttp_socks import (
    SocksConnector, SocksVer, SocksError, open_connection,
    SocksConnectionError, create_connection)
from tests.conftest import (
    SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT,
    LOGIN, PASSWORD, SOCKS5_IPV6_HOST,
    SOCKS5_IPV6_PORT, SOCKS4_HOST, SOCKS4_PORT,
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


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_connector_ipv4(url, rdns):
    connector = SocksConnector.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.asyncio
async def test_socks5_connector_with_invalid_credentials():
    connector = SocksConnector(
        socks_ver=SocksVer.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(SocksError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(HTTP_TEST_URL) as resp:
                await resp.text()


@pytest.mark.asyncio
async def test_socks5_connector_with_timeout():
    connector = SocksConnector(
        socks_ver=SocksVer.SOCKS5,
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
async def test_socks5_connector_with_invalid_proxy_port(unused_tcp_port):
    connector = SocksConnector(
        socks_ver=SocksVer.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(SocksConnectionError):
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(HTTP_TEST_URL) as resp:
                await resp.text()


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
@pytest.mark.asyncio
async def test_socks5_connector_ipv6():
    connector = SocksConnector.from_url(SOCKS5_IPV6_URL,
                                        family=socket.AF_INET6)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(HTTP_TEST_URL) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_connector(url, rdns):
    connector = SocksConnector.from_url(SOCKS4_URL, rdns=rdns,)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as resp:
            assert resp.status == 200


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_http_open_connection(rdns):
    reader, writer = await open_connection(
        socks_url=SOCKS5_IPV4_URL,
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
        socks_url=SOCKS5_IPV4_URL,
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


@pytest.mark.asyncio
async def test_socks5_http_create_connection(event_loop):
    reader = asyncio.StreamReader(loop=event_loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=event_loop)

    transport, _ = await create_connection(
        socks_url=SOCKS5_IPV4_URL,
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
