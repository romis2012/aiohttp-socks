import signal
import subprocess
import os
import platform
import time

import socket
import threading

import psutil
import pytest

LOGIN = 'admin'
PASSWORD = 'admin'

# SOCKS5_IPV6_HOST = '[::1]'
SOCKS5_IPV6_HOST = '::1'
SOCKS5_IPV6_PORT = 7780

SOCKS5_IPV4_HOST = '127.0.0.1'
SOCKS5_IPV4_PORT = 7780

SOCKS4_HOST = '127.0.0.1'
SOCKS4_PORT = 7781


def wait_for_socket(server_name, host, port, family=socket.AF_INET, timeout=2):
    ok = False
    for x in range(10):
        try:
            print('Testing [%s] proxy server on %s:%d'
                  % (server_name, host, port))
            s = socket.socket(family, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
        except socket.error as ex:
            print('ERROR', ex)
            time.sleep(timeout / 10.0)
        else:
            print('Connection established')
            ok = True
            break
    if not ok:
        raise Exception('The %s proxy server has not started in %d seconds'
                        % (server_name, timeout))


def start_proxy_server():
    this_path = os.path.dirname(os.path.realpath(__file__))

    template_path = os.path.join(this_path, '3proxy/cfg/3proxy.cfg.tmpl')
    config_path = os.path.join(this_path, '3proxy/cfg/3proxy.cfg')

    system = platform.system()
    if system == 'Windows':
        binary_path = os.path.join(this_path, '3proxy/bin/windows/3proxy.exe')
    elif system == 'Linux':
        binary_path = os.path.join(this_path, '3proxy/bin/linux/3proxy')
    else:
        raise RuntimeError('Unsupportable system: %s' % system)

    with open(template_path, mode='r') as tmpl:
        content = tmpl.read()
        content = content.format(
            LOGIN=LOGIN,
            PASSWORD=PASSWORD,
            SOCKS5_IPV6_PORT=SOCKS5_IPV6_PORT,
            SOCKS5_IPV6_HOST=SOCKS5_IPV6_HOST,
            SOCKS5_IPV4_PORT=SOCKS5_IPV4_PORT,
            SOCKS5_IPV4_HOST=SOCKS5_IPV4_HOST,
            SOCKS4_PORT=SOCKS4_PORT,
            SOCKS4_HOST=SOCKS4_HOST,
        )
        with open(config_path, mode='w') as cfg:
            cfg.write(content)

    cmd = '%s %s' % (binary_path, config_path)
    server = subprocess.Popen(cmd, shell=True)
    server.wait()


@pytest.fixture(scope='session', autouse=True)
def proxy_server():
    th = threading.Thread(target=start_proxy_server)
    th.daemon = True
    th.start()

    wait_for_socket('3proxy:socks4', SOCKS4_HOST, SOCKS4_PORT)
    wait_for_socket('3proxy:socks5:ipv4', SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT)
    wait_for_socket('3proxy:socks5:ipv6', SOCKS5_IPV6_HOST, SOCKS5_IPV6_PORT,
                    socket.AF_INET6)

    yield None

    print('Active threads:')
    for th in threading.enumerate():
        print(' * %s' % th)

    parent = psutil.Process(os.getpid())
    print('Active child processes:')
    for child in parent.children(recursive=True):
        print(' * %s' % child)
        # child.send_signal(signal.SIGINT)
        child.send_signal(signal.SIGTERM)
