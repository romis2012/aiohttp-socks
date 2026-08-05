from __future__ import annotations

import time
from collections.abc import Iterable
from multiprocessing import Process
from typing import Any, NamedTuple

from tests.http_app import run_app
from tests.utils import is_connectable


class HttpServerConfig(NamedTuple):
    host: str
    port: int
    certfile: str | None = None
    keyfile: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val  # noqa: PERF403
        return d


class HttpServer:
    def __init__(self, config: Iterable[HttpServerConfig]) -> None:
        self.config = config
        self.workers: list[Process] = []

    def start(self) -> None:
        for cfg in self.config:
            p = Process(target=run_app, kwargs=cfg.to_dict())
            self.workers.append(p)

        for p in self.workers:
            p.start()

    def terminate(self) -> None:
        for p in self.workers:
            p.terminate()

    def wait_until_connectable(self, host: str, port: int, timeout: int = 10) -> bool:
        count = 0
        while not is_connectable(host=host, port=port):
            if count >= timeout:
                self.terminate()
                raise ConnectionError(
                    f"The http server has not available "
                    f"by ({host}, {port}) in {timeout:d} seconds"
                )
            count += 1
            time.sleep(1)
        return True
