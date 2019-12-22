class AbstractProxy:
    async def connect(self, dest_host, dest_port,
                      _socket=None):  # pragma: no cover
        raise NotImplementedError()

    @property
    def socket(self):  # pragma: no cover
        raise NotImplementedError()

    @property
    def host(self):  # pragma: no cover
        raise NotImplementedError()

    @property
    def port(self):  # pragma: no cover
        raise NotImplementedError()
