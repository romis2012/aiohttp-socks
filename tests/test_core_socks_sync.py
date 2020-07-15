import socket
import ssl

import pytest  # noqa
from yarl import URL   # noqa

from aiohttp_socks.core_socks import (
    ProxyType,
    ProxyError,
    ProxyTimeoutError,
    ProxyConnectionError
)

from aiohttp_socks.core_socks._proxy_sync import SyncProxy  # noqa
from aiohttp_socks.core_socks.sync import Proxy
from aiohttp_socks.core_socks.sync import ProxyChain

from tests.conftest import (
    SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT, LOGIN, PASSWORD, SKIP_IPV6_TESTS,
    SOCKS5_IPV4_URL, SOCKS5_IPV4_URL_WO_AUTH, SOCKS5_IPV6_URL, SOCKS4_URL,
    HTTP_PROXY_URL
)

# TEST_URL = 'https://httpbin.org/ip'
TEST_URL = 'https://check-host.net/ip'


def read_status_code(sock: socket.socket) -> int:
    data = sock.recv(1024)
    status_line = data.split(b'\r\n', 1)[0]
    status_line = status_line.decode('utf-8', 'surrogateescape')
    version, status_code, *reason = status_line.split()
    return int(status_code)


def make_request(proxy: SyncProxy, url: str,
                 resolve_host=False, timeout=None):
    url = URL(url)

    dest_host = url.host
    if resolve_host:
        dest_host = socket.gethostbyname(url.host)

    sock: socket.socket = proxy.connect(
        dest_host=dest_host,
        dest_port=url.port,
        timeout=timeout
    )

    if url.scheme == 'https':
        sock = ssl.create_default_context().wrap_socket(
            sock=sock,
            server_hostname=url.host
        )

    request = (
        'GET {rel_url} HTTP/1.1\r\n'
        'Host: {host}\r\n'
        'Connection: close\r\n\r\n'
    )
    request = request.format(rel_url=url.path_qs, host=url.host)
    request = request.encode('ascii')
    sock.sendall(request)

    status_code = read_status_code(sock)
    sock.close()
    return status_code


@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.parametrize('resolve_host', (True, False))
def test_socks5_proxy_ipv4(rdns, resolve_host):
    proxy = Proxy.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    status_code = make_request(
        proxy=proxy,
        url=TEST_URL,
        resolve_host=resolve_host
    )
    assert status_code == 200


@pytest.mark.parametrize('rdns', (None, True, False))
def test_socks5_proxy_ipv4_with_auth_none(rdns):
    proxy = Proxy.from_url(SOCKS5_IPV4_URL_WO_AUTH, rdns=rdns)
    status_code = make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200


def test_socks5_proxy_with_invalid_credentials():
    proxy = Proxy.create(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(ProxyError):
        make_request(proxy=proxy, url=TEST_URL)


def test_socks5_proxy_with_connect_timeout():
    proxy = Proxy.create(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyTimeoutError):
        make_request(proxy=proxy, url=TEST_URL, timeout=0.0001)


def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port):
    proxy = Proxy.create(
        proxy_type=ProxyType.SOCKS5,
        host=SOCKS5_IPV4_HOST,
        port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyConnectionError):
        make_request(proxy=proxy, url=TEST_URL)


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
def test_socks5_proxy_ipv6():
    proxy = Proxy.from_url(SOCKS5_IPV6_URL)
    status_code = make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200


@pytest.mark.parametrize('rdns', (None, True, False))
@pytest.mark.parametrize('resolve_host', (True, False))
def test_socks4_proxy(rdns, resolve_host):
    proxy = Proxy.from_url(SOCKS4_URL, rdns=rdns)
    status_code = make_request(
        proxy=proxy,
        url=TEST_URL,
        resolve_host=resolve_host
    )
    assert status_code == 200


def test_http_proxy():
    proxy = Proxy.from_url(HTTP_PROXY_URL)
    status_code = make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200


def test_proxy_chain():
    proxy = ProxyChain([
        Proxy.from_url(SOCKS5_IPV4_URL),
        Proxy.from_url(SOCKS4_URL),
        Proxy.from_url(HTTP_PROXY_URL),
    ])
    # noinspection PyTypeChecker
    status_code = make_request(proxy=proxy, url=TEST_URL)
    assert status_code == 200
