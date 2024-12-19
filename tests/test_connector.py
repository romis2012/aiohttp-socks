import asyncio

import aiohttp
import pytest  # noqa
from aiohttp import ClientResponse, TCPConnector
from yarl import URL  # noqa

from aiohttp_socks import (
    ChainProxyConnector,
    ProxyConnectionError,
    ProxyConnector,
    ProxyError,
    ProxyInfo,
    ProxyTimeoutError,
    ProxyType,
)
from tests.config import (
    HTTP_PROXY_PORT,
    HTTP_PROXY_URL,
    LOGIN,
    PASSWORD,
    PROXY_HOST_IPV4,
    SKIP_IPV6_TESTS,
    SOCKS4_PROXY_PORT,
    SOCKS4_URL,
    SOCKS5_IPV4_URL,
    SOCKS5_IPV6_URL,
    SOCKS5_PROXY_PORT,
    TEST_URL_IPV4,
    TEST_URL_IPV4_DELAY,
    TEST_URL_IPV4_HTTPS,
)


async def fetch(
    connector: TCPConnector,
    url: str,
    timeout=None,
    ssl_context=None,
) -> ClientResponse:
    url = URL(url)

    if url.scheme == 'https':
        dest_ssl = ssl_context
    else:
        dest_ssl = None

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, ssl=dest_ssl, timeout=timeout) as resp:
            return resp


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_proxy_ipv4(url, rdns, target_ssl_context):
    connector = ProxyConnector.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    res = await fetch(
        connector=connector,
        url=url,
        ssl_context=target_ssl_context,
    )
    assert res.status == 200


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_credentials(target_ssl_context):
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=PROXY_HOST_IPV4,
        port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(ProxyError):
        await fetch(
            connector=connector,
            url=TEST_URL_IPV4,
            ssl_context=target_ssl_context,
        )


@pytest.mark.asyncio
async def test_socks5_proxy_with_timeout(target_ssl_context):
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=PROXY_HOST_IPV4,
        port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(asyncio.TimeoutError):
        await fetch(
            connector=connector,
            url=TEST_URL_IPV4_DELAY,
            timeout=1,
            ssl_context=target_ssl_context,
        )


@pytest.mark.asyncio
async def test_socks5_proxy_with_proxy_connect_timeout(target_ssl_context):
    connector = ProxyConnector.from_url(SOCKS5_IPV4_URL)
    timeout = aiohttp.ClientTimeout(total=32, sock_connect=0.001)
    with pytest.raises(ProxyTimeoutError):
        await fetch(
            connector=connector,
            url=TEST_URL_IPV4,
            timeout=timeout,
            ssl_context=target_ssl_context,
        )


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port, target_ssl_context):
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host=PROXY_HOST_IPV4,
        port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyConnectionError):
        await fetch(
            connector=connector,
            url=TEST_URL_IPV4,
            ssl_context=target_ssl_context,
        )


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.skipif(SKIP_IPV6_TESTS, reason="TravisCI doesn't support ipv6")
@pytest.mark.asyncio
async def test_socks5_proxy_ipv6(url, target_ssl_context):
    connector = ProxyConnector.from_url(SOCKS5_IPV6_URL)
    res = await fetch(
        connector=connector,
        url=url,
        ssl_context=target_ssl_context,
    )
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_proxy(url, rdns, target_ssl_context):
    connector = ProxyConnector.from_url(
        SOCKS4_URL,
        rdns=rdns,
    )
    res = await fetch(
        connector=connector,
        url=url,
        ssl_context=target_ssl_context,
    )
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.asyncio
async def test_http_proxy(url, target_ssl_context):
    connector = ProxyConnector.from_url(HTTP_PROXY_URL)
    res = await fetch(
        connector=connector,
        url=url,
        ssl_context=target_ssl_context,
    )
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.asyncio
async def test_chain_proxy_from_url(url, target_ssl_context):
    connector = ChainProxyConnector.from_urls([SOCKS5_IPV4_URL, SOCKS4_URL, HTTP_PROXY_URL])
    res = await fetch(
        connector=connector,
        url=url,
        ssl_context=target_ssl_context,
    )
    assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_chain_proxy_ctor(url, rdns, target_ssl_context):
    connector = ChainProxyConnector(
        [
            ProxyInfo(
                proxy_type=ProxyType.SOCKS5,
                host=PROXY_HOST_IPV4,
                port=SOCKS5_PROXY_PORT,
                username=LOGIN,
                password=PASSWORD,
                rdns=rdns,
            ),
            ProxyInfo(
                proxy_type=ProxyType.SOCKS4,
                host=PROXY_HOST_IPV4,
                port=SOCKS4_PROXY_PORT,
                username=LOGIN,
                rdns=rdns,
            ),
            ProxyInfo(
                proxy_type=ProxyType.HTTP,
                host=PROXY_HOST_IPV4,
                port=HTTP_PROXY_PORT,
                username=LOGIN,
                password=PASSWORD,
            ),
        ]
    )
    res = await fetch(
        connector=connector,
        url=url,
        ssl_context=target_ssl_context,
    )
    assert res.status == 200
