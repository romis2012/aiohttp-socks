import asyncio

from python_socks import ProxyType, parse_proxy_url
from python_socks.async_.asyncio import Proxy


async def open_connection(proxy_url=None, host=None, port=None, *,
                          proxy_type=ProxyType.SOCKS5,
                          proxy_host='127.0.0.1', proxy_port=1080,
                          username=None, password=None, rdns=True,
                          loop=None, **kwargs):
      """
      Establish a connection to a given proxy.

      Args:
          proxy_url: (str): write your description
          host: (str): write your description
          port: (int): write your description
          proxy_type: (str): write your description
          ProxyType: (str): write your description
          SOCKS5: (str): write your description
          proxy_host: (str): write your description
          proxy_port: (int): write your description
          username: (str): write your description
          password: (str): write your description
          rdns: (str): write your description
          loop: (todo): write your description
      """
    if host is None or port is None:
        raise ValueError('host and port must be specified')  # pragma: no cover

    if loop is None:
        loop = asyncio.get_event_loop()

    if proxy_url is not None:
        proxy_type, proxy_host, proxy_port, username, password \
            = parse_proxy_url(proxy_url)

    proxy = Proxy.create(
        proxy_type=proxy_type,
        host=proxy_host,
        port=proxy_port,
        username=username,
        password=password,
        rdns=rdns,
        loop=loop
    )

    sock = await proxy.connect(host, port)

    # noinspection PyTypeChecker
    return await asyncio.open_connection(
        host=None,
        port=None,
        sock=sock,
        **kwargs
    )


async def create_connection(proxy_url=None, protocol_factory=None,
                            host=None, port=None, *,
                            proxy_type=ProxyType.SOCKS5,
                            proxy_host='127.0.0.1', proxy_port=1080,
                            username=None, password=None, rdns=True,
                            loop=None, **kwargs):
      """
      Create a new connection to a connection.

      Args:
          proxy_url: (str): write your description
          protocol_factory: (str): write your description
          host: (str): write your description
          port: (int): write your description
          proxy_type: (str): write your description
          ProxyType: (str): write your description
          SOCKS5: (str): write your description
          proxy_host: (str): write your description
          proxy_port: (int): write your description
          username: (str): write your description
          password: (str): write your description
          rdns: (str): write your description
          loop: (todo): write your description
      """
    if protocol_factory is None:
        raise ValueError('protocol_factory '
                         'must be specified')  # pragma: no cover

    if host is None or port is None:
        raise ValueError('host and port '
                         'must be specified')  # pragma: no cover

    if loop is None:
        loop = asyncio.get_event_loop()

    if proxy_url is not None:
        proxy_type, proxy_host, proxy_port, username, password \
            = parse_proxy_url(proxy_url)

    proxy = Proxy.create(
        proxy_type=proxy_type,
        host=proxy_host,
        port=proxy_port,
        username=username,
        password=password,
        rdns=rdns,
        loop=loop
    )

    sock = await proxy.connect(host, port)

    return await loop.create_connection(
        protocol_factory=protocol_factory,
        host=None,
        port=None,
        sock=sock,
        **kwargs
    )
