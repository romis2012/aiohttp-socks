import os

LOGIN = 'admin'
PASSWORD = 'admin'

PROXY_HOST_IPV4 = '127.0.0.1'
PROXY_HOST_IPV6 = '::1'

PROXY_HOST_NAME_IPV4 = 'ip4.proxy.example.com'
PROXY_HOST_NAME_IPV6 = 'ip6.proxy.example.com'

SOCKS5_PROXY_PORT = 7780
SOCKS5_PROXY_PORT_NO_AUTH = 7781

SOCKS4_PROXY_PORT = 7782
SOCKS4_PORT_NO_AUTH = 7783

HTTP_PROXY_PORT = 7784

SKIP_IPV6_TESTS = 'SKIP_IPV6_TESTS' in os.environ

SOCKS5_IPV4_URL = 'socks5://{login}:{password}@{host}:{port}'.format(
    host=PROXY_HOST_IPV4,
    port=SOCKS5_PROXY_PORT,
    login=LOGIN,
    password=PASSWORD,
)

SOCKS5_IPV6_URL = 'socks5://{login}:{password}@{host}:{port}'.format(
    host='[%s]' % PROXY_HOST_IPV6,
    port=SOCKS5_PROXY_PORT,
    login=LOGIN,
    password=PASSWORD,
)

SOCKS5_IPV4_HOSTNAME_URL = 'socks5://{login}:{password}@{host}:{port}'.format(
    host=PROXY_HOST_NAME_IPV4,
    port=SOCKS5_PROXY_PORT,
    login=LOGIN,
    password=PASSWORD,
)

SOCKS5_IPV4_URL_WO_AUTH = 'socks5://{host}:{port}'.format(
    host=PROXY_HOST_IPV4,
    port=SOCKS5_PROXY_PORT_NO_AUTH
)

SOCKS4_URL = 'socks4://{login}:{password}@{host}:{port}'.format(
    host=PROXY_HOST_IPV4,
    port=SOCKS4_PROXY_PORT,
    login=LOGIN,
    password='',
)

HTTP_PROXY_URL = 'http://{login}:{password}@{host}:{port}'.format(
    host=PROXY_HOST_IPV4,
    port=HTTP_PROXY_PORT,
    login=LOGIN,
    password=PASSWORD,
)

TEST_HOST_IPV4 = '127.0.0.1'
TEST_HOST_IPV6 = '::1'

TEST_HOST_NAME_IPV4 = 'ip4.target.example.com'
TEST_HOST_NAME_IPV6 = 'ip6.target.example.com'

TEST_PORT_IPV4 = 8889
TEST_PORT_IPV6 = 8889

TEST_PORT_IPV4_HTTPS = 8890

TEST_URL_IPV4 = 'http://{host}:{port}/ip'.format(
    host=TEST_HOST_NAME_IPV4,
    port=TEST_PORT_IPV4
)

TEST_URL_IPv6 = 'http://{host}:{port}/ip'.format(
    host=TEST_HOST_NAME_IPV6,
    port=TEST_PORT_IPV6
)

TEST_URL_IPV4_DELAY = 'http://{host}:{port}/delay/2'.format(
    host=TEST_HOST_NAME_IPV4,
    port=TEST_PORT_IPV4
)

TEST_URL_IPV4_HTTPS = 'https://{host}:{port}/ip'.format(
    host=TEST_HOST_NAME_IPV4,
    port=TEST_PORT_IPV4_HTTPS
)


def resolve_path(path):
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), path))


TEST_HOST_CERT_FILE = resolve_path('./cert/test_host.crt')
TEST_HOST_KEY_FILE = resolve_path('./cert/test_host.key')
TEST_HOST_PEM_FILE = resolve_path('./cert/test_host.pem')
