# noinspection PyPackageRequirements
import pytest

from aiohttp_socks.core_socks._helpers import is_ip_address  # noqa
from aiohttp_socks.core_socks._basic_auth import BasicAuth  # noqa


@pytest.mark.parametrize('address', ('::1', b'::1', '127.0.0.1', b'127.0.0.1'))
def test_is_ip_address(address):
    assert is_ip_address(address)


def test_basic_auth():
    login = 'login'
    password = 'password'

    auth1 = BasicAuth(login=login, password=password)
    auth2 = BasicAuth.decode(auth1.encode())

    assert auth2.login == login
    assert auth2.password == password
