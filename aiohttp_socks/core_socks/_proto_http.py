import sys

from ._version import __title__, __version__

DEFAULT_USER_AGENT = 'Python/{0[0]}.{0[1]} {1}/{2}'.format(
    sys.version_info, __title__, __version__)

CRLF = '\r\n'
