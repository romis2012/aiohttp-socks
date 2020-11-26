import typing
import time
from multiprocessing import Process

from tests.utils import is_connectable
from tests.http_app import run_app


class HttpServerConfig(typing.NamedTuple):
    host: str
    port: int
    certfile: str = None
    keyfile: str = None

    def to_dict(self):
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val
        return d


class HttpServer:
    def __init__(self, config: typing.Iterable[HttpServerConfig]):
        self.config = config
        self.workers = []

    def start(self):
        for cfg in self.config:
            p = Process(target=run_app, kwargs=cfg.to_dict())
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
                    'The http server has not available '
                    'by (%s, %s) in %d seconds'
                    % (host, port, timeout))
            count += 1
            time.sleep(1)
        return True
