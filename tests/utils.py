import socket
import time


def is_connectable(host, port):
    try:
        sock = socket.create_connection((host, port), 1)
    except socket.error:
        return False
    else:
        sock.close()
        return True


def wait_until_connectable(host, port, timeout=10):
    count = 0
    while not is_connectable(host=host, port=port):
        if count >= timeout:
            raise Exception(
                f'The proxy server has not available by ({host}, {port}) in {timeout:d} seconds'
            )
        count += 1
        time.sleep(1)
    return True
