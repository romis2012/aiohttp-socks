import socket
import subprocess
import time
import os


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


def resolve_path(path):
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), path))


class ProxyServer(object):
    def __init__(self, binary_path, config_path):
        self.process = subprocess.Popen([binary_path, config_path],
                                        shell=False)

    def wait_until_connectable(self, host, port, timeout=10):
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
        if self.process:
            self.process.terminate()
            self.process.kill()
            self.process.wait()
