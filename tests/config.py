import os

LOGIN = "admin"
PASSWORD = "admin"  # noqa: S105

PROXY_HOST_IPV4 = "127.0.0.1"
PROXY_HOST_IPV6 = "::1"

PROXY_HOST_NAME_IPV4 = "ip4.proxy.example.com"
PROXY_HOST_NAME_IPV6 = "ip6.proxy.example.com"

SOCKS5_PROXY_PORT = 7780
SOCKS5_PROXY_PORT_NO_AUTH = 7781

SOCKS4_PROXY_PORT = 7782
SOCKS4_PORT_NO_AUTH = 7783

HTTP_PROXY_PORT = 7784

SKIP_IPV6_TESTS = "SKIP_IPV6_TESTS" in os.environ

SOCKS5_IPV4_URL = f"socks5://{LOGIN}:{PASSWORD}@{PROXY_HOST_IPV4}:{SOCKS5_PROXY_PORT}"

SOCKS5_IPV6_URL = f"socks5://{LOGIN}:{PASSWORD}@[{PROXY_HOST_IPV6}]:{SOCKS5_PROXY_PORT}"

SOCKS5_IPV4_HOSTNAME_URL = (
    f"socks5://{LOGIN}:{PASSWORD}@{PROXY_HOST_NAME_IPV4}:{SOCKS5_PROXY_PORT}"
)

SOCKS5_IPV4_URL_WO_AUTH = f"socks5://{PROXY_HOST_IPV4}:{SOCKS5_PROXY_PORT_NO_AUTH}"

SOCKS4_URL = "socks4://{login}:{password}@{host}:{port}".format(
    host=PROXY_HOST_IPV4,
    port=SOCKS4_PROXY_PORT,
    login=LOGIN,
    password="",
)

HTTP_PROXY_URL = f"http://{LOGIN}:{PASSWORD}@{PROXY_HOST_IPV4}:{HTTP_PROXY_PORT}"

TEST_HOST_IPV4 = "127.0.0.1"
TEST_HOST_IPV6 = "::1"

TEST_HOST_NAME_IPV4 = "ip4.target.example.com"
TEST_HOST_NAME_IPV6 = "ip6.target.example.com"

TEST_PORT_IPV4 = 8889
TEST_PORT_IPV6 = 8889

TEST_PORT_IPV4_HTTPS = 8890

TEST_URL_IPV4 = f"http://{TEST_HOST_NAME_IPV4}:{TEST_PORT_IPV4}/ip"

TEST_URL_IPv6 = f"http://{TEST_HOST_NAME_IPV6}:{TEST_PORT_IPV6}/ip"

TEST_URL_IPV4_DELAY = f"http://{TEST_HOST_NAME_IPV4}:{TEST_PORT_IPV4}/delay/2"

TEST_URL_IPV4_HTTPS = f"https://{TEST_HOST_NAME_IPV4}:{TEST_PORT_IPV4_HTTPS}/ip"


def resolve_path(path: str) -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), path)  # noqa: PTH118, PTH120
    )
