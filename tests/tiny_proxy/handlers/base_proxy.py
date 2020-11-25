import logging
import select
import socket
from socketserver import StreamRequestHandler

DEFAULT_RECEIVE_SIZE = 65536


class ProxyError(Exception):
    pass


class BaseProxyHandler(StreamRequestHandler):
    request: socket.socket
    logger: logging.Logger

    def __init__(self, request, client_address, server, ):
        self.logger = logging.getLogger(__name__)
        super().__init__(request, client_address, server)

    def handle(self):
        client = self.request
        try:
            remote = self.connect_to_remote()
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)
            client.close()
        else:
            try:
                self.exchange_loop(client=client, remote=remote)
            except Exception as e:
                self.logger.exception(e)
            finally:
                remote.close()
                client.close()

    def connect_to_remote(self) -> socket.socket:
        raise NotImplementedError

    # noinspection PyMethodMayBeStatic
    def exchange_loop(self, client: socket.socket, remote: socket.socket):
        while True:

            # wait until client or remote is available for read
            r, w, e = select.select([client, remote], [], [])

            if client in r:
                data = client.recv(DEFAULT_RECEIVE_SIZE)
                if remote.send(data) <= 0:
                    break

            if remote in r:
                data = remote.recv(DEFAULT_RECEIVE_SIZE)
                if client.send(data) <= 0:
                    break
