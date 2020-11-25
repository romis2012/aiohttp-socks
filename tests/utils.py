import socket


def is_connectable(host, port):
    sock = None
    try:
        sock = socket.create_connection((host, port), 1)
        result = True
    except socket.error:
        result = False
    finally:
        if sock:
            sock.close()
    return result
