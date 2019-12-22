from typing import Iterable

from .abc import AbstractProxy


class ChainProxy:
    def __init__(self, proxies: Iterable[AbstractProxy]):
        self._proxies = proxies
        self._socket = None

    async def connect(self, dest_host, dest_port):
        curr_socket = None
        proxies = list(self._proxies)

        length = len(proxies) - 1
        for i in range(length):
            await proxies[i].connect(
                dest_host=proxies[i + 1].host,
                dest_port=proxies[i + 1].port,
                _socket=curr_socket
            )
            curr_socket = proxies[i].socket

        await proxies[length].connect(
            dest_host=dest_host,
            dest_port=dest_port,
            _socket=curr_socket
        )
        curr_socket = proxies[length].socket

        self._socket = curr_socket

    @property
    def socket(self):
        return self._socket
