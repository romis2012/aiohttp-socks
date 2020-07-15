import platform
import os

# noinspection PyPackageRequirements
import pytest

from tests.utils import resolve_path, ProxyServer

LOGIN = 'admin'
PASSWORD = 'admin'

SOCKS5_IPV6_HOST = '::1'
SOCKS5_IPV6_PORT = 7780

SOCKS5_IPV4_HOST = '127.0.0.1'
SOCKS5_IPV4_PORT = 7780
SOCKS5_IPV4_PORT_WO_AUTH = 7781

SOCKS4_HOST = '127.0.0.1'
SOCKS4_PORT = 7782

HTTP_PROXY_HOST = '127.0.0.1'
HTTP_PROXY_PORT = 7783

SKIP_IPV6_TESTS = 'SKIP_IPV6_TESTS' in os.environ

SOCKS5_IPV4_URL = 'socks5://{login}:{password}@{host}:{port}'.format(
    host=SOCKS5_IPV4_HOST,
    port=SOCKS5_IPV4_PORT,
    login=LOGIN,
    password=PASSWORD,
)

SOCKS5_IPV6_URL = 'socks5://{login}:{password}@{host}:{port}'.format(
    host='[%s]' % SOCKS5_IPV6_HOST,
    port=SOCKS5_IPV6_PORT,
    login=LOGIN,
    password=PASSWORD,
)

SOCKS5_IPV4_URL_WO_AUTH = 'socks5://{host}:{port}'.format(
    host=SOCKS5_IPV4_HOST,
    port=SOCKS5_IPV4_PORT_WO_AUTH
)

SOCKS4_URL = 'socks4://{host}:{port}'.format(
    host=SOCKS4_HOST,
    port=SOCKS4_PORT,
)

HTTP_PROXY_URL = 'http://{login}:{password}@{host}:{port}'.format(
    host=HTTP_PROXY_HOST,
    port=HTTP_PROXY_PORT,
    login=LOGIN,
    password=PASSWORD,
)


@pytest.fixture(scope='session', autouse=True)
def proxy_server():
    system = platform.system().lower()
    config_path = resolve_path('./3proxy/cfg/3proxy.cfg')
    binary_path = resolve_path('./3proxy/bin/%s/3proxy' % system)

    with open(config_path, mode='w') as cfg:
        cfg.write('users %s:CL:%s\n' % (LOGIN, PASSWORD))

        if not SKIP_IPV6_TESTS:
            cfg.write('auth strong\n')
            cfg.write('socks -p%d -i%s\n' % (SOCKS5_IPV6_PORT,
                                             SOCKS5_IPV6_HOST))

        cfg.write('auth strong\n')
        cfg.write('socks -p%d -i%s\n' % (SOCKS5_IPV4_PORT,
                                         SOCKS5_IPV4_HOST))

        cfg.write('auth none\n')
        cfg.write('socks -p%d -i%s\n' % (SOCKS5_IPV4_PORT_WO_AUTH,
                                         SOCKS5_IPV4_HOST))

        cfg.write('auth none\n')
        cfg.write('socks -p%d -i%s\n' % (SOCKS4_PORT, SOCKS4_HOST))

        cfg.write('auth strong\n')
        cfg.write('proxy -p%d -i%s -n\n' % (HTTP_PROXY_PORT, HTTP_PROXY_HOST))

    server = ProxyServer(binary_path=binary_path, config_path=config_path)

    if not SKIP_IPV6_TESTS:
        server.wait_until_connectable(host=SOCKS5_IPV6_HOST,
                                      port=SOCKS5_IPV6_PORT)

    server.wait_until_connectable(host=SOCKS5_IPV4_HOST, port=SOCKS5_IPV4_PORT)
    server.wait_until_connectable(host=SOCKS4_HOST, port=SOCKS4_PORT)

    yield None

    server.kill()
