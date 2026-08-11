import socket
import time


def is_connectable(host: str, port: int) -> bool:
    try:
        sock = socket.create_connection((host, port), 1)
    except OSError:
        return False
    else:
        sock.close()
        return True


def wait_until_connectable(host: str, port: int, timeout: int = 10) -> bool:
    count = 0
    while not is_connectable(host=host, port=port):
        if count >= timeout:
            raise ConnectionError(
                f"The server has not available "
                f"by ({host}, {port}) in {timeout:d} seconds"
            )
        count += 1
        time.sleep(1)
    return True
