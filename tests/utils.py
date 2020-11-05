import socket
import subprocess
import time
import os


def is_connectable(host, port):
    """
    Return true if host is closed.

    Args:
        host: (str): write your description
        port: (int): write your description
    """
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


def resolve_path(path):
    """
    Resolve a path.

    Args:
        path: (str): write your description
    """
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), path))


class ProxyServer(object):
    def __init__(self, binary_path, config_path):
        """
        Initialize a binary.

        Args:
            self: (todo): write your description
            binary_path: (str): write your description
            config_path: (str): write your description
        """
        self.process = subprocess.Popen([binary_path, config_path],
                                        shell=False)

    def wait_until_connectable(self, host, port, timeout=10):
        """
        Wait until a host to be established.

        Args:
            self: (todo): write your description
            host: (str): write your description
            port: (int): write your description
            timeout: (float): write your description
        """
        count = 0
        while not is_connectable(host=host, port=port):
            if self.process.poll() is not None:
                # process has exited
                raise Exception(
                    'The process appears to have exited '
                    'before we could connect.')
            if count >= timeout:
                self.kill()
                raise Exception(
                    'The proxy server has not binded '
                    'to (%s, %s) in %d seconds'
                    % (host, port, timeout))
            count += 1
            time.sleep(1)
        return True

    def kill(self):
        """
        Kill the child process.

        Args:
            self: (todo): write your description
        """
        if self.process:
            self.process.terminate()
            self.process.kill()
            self.process.wait()
