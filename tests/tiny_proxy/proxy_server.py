import logging
import sys
import time
import typing
from multiprocessing import Process
from unittest import mock

from tests.mocks import sync_resolve_factory
from tests.tiny_proxy import (
    HttpProxyServer,
    Socks4ProxyServer,
    Socks5ProxyServer
)
from tests.tiny_proxy.handlers import (
    Socks4ProxyHandler,
    Socks5ProxyHandler,
    HttpProxyHandler,
)
from tests.tiny_proxy.handlers.base_proxy import BaseProxyHandler
from tests.tiny_proxy.handlers.resolver import Resolver
from tests.utils import is_connectable


class ProxyConfig(typing.NamedTuple):
    proxy_type: str
    host: str
    port: int
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None

    def to_dict(self):
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val
        return d


cls_map = {
    'http': HttpProxyServer,
    'socks4': Socks4ProxyServer,
    'socks5': Socks5ProxyServer,
}


def configure_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel('DEBUG')

    fmt = '%(asctime)s [%(name)s] %(levelname)s : %(message)s'
    formatter = logging.Formatter(fmt)
    formatter.converter = time.gmtime

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)


def connect_to_remote_factory(cls: typing.Type[BaseProxyHandler]):
    """
    simulate target host connection timeout
    """
    origin_connect_to_remote = cls.connect_to_remote

    def new_connect_to_remote(self):
        time.sleep(0.01)
        return origin_connect_to_remote(self)

    return new_connect_to_remote


@mock.patch.object(HttpProxyHandler, attribute='connect_to_remote',
                   new=connect_to_remote_factory(HttpProxyHandler))
@mock.patch.object(Socks4ProxyHandler, attribute='connect_to_remote',
                   new=connect_to_remote_factory(Socks4ProxyHandler))
@mock.patch.object(Socks5ProxyHandler, attribute='connect_to_remote',
                   new=connect_to_remote_factory(Socks5ProxyHandler))
@mock.patch.object(Resolver, attribute='resolve',
                   new=sync_resolve_factory(Resolver))
def start(proxy_type, host, port, **kwargs):
    # configure_logging()

    cls = cls_map.get(proxy_type)
    if not cls:
        raise RuntimeError('Unsupported type: {}'.format(proxy_type))

    with cls(host, port, **kwargs) as server:
        server.serve_forever()


class ProxyServer:
    workers: typing.List[Process]

    def __init__(self, config: typing.Iterable[ProxyConfig]):
        self.config = config
        self.workers = []

    def start(self):
        for proxy in self.config:
            print('Starting {} proxy on {}:{}...'.format(
                proxy.proxy_type, proxy.host, proxy.port))

            p = Process(target=start, kwargs=proxy.to_dict())
            self.workers.append(p)

        for p in self.workers:
            p.start()

    def terminate(self):
        for p in self.workers:
            p.terminate()

    def wait_until_connectable(self, host, port, timeout=10):
        count = 0
        while not is_connectable(host=host, port=port):
            if count >= timeout:
                self.terminate()
                raise Exception(
                    'The proxy server has not available '
                    'by (%s, %s) in %d seconds'
                    % (host, port, timeout))
            count += 1
            time.sleep(1)
        return True
