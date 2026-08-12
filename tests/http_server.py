from __future__ import annotations

import threading
import typing
from collections.abc import Iterable
from dataclasses import dataclass

import uvicorn

from tests.http_app import app


@dataclass
class HttpServerConfig:
    host: str
    port: int
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None

    def to_dict(self) -> dict[str, typing.Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class HttpServer:
    def __init__(self, config: Iterable[HttpServerConfig]) -> None:
        self.config = config
        self.servers: list[uvicorn.Server] = []

    def start(self) -> None:
        for cfg in self.config:
            config = uvicorn.Config(
                app=app,
                host=cfg.host,
                port=cfg.port,
                ssl_certfile=cfg.ssl_certfile,
                ssl_keyfile=cfg.ssl_keyfile,
                log_level="warning",
            )
            server = uvicorn.Server(config)
            self.servers.append(server)

            t = threading.Thread(target=server.run, daemon=True)
            t.start()

    def shutdown(self) -> None:
        for server in self.servers:
            server.should_exit = True
