from __future__ import annotations


class ProxyTimeoutError(Exception):
    pass


class ProxyConnectionError(Exception):
    pass


class ProxyError(Exception):
    def __init__(self, message: str, error_code: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
