RSV = NULL = 0x00
SOCKS_VER5 = 0x05
SOCKS5_GRANTED = 0x00

SOCKS_CMD_CONNECT = 0x01

SOCKS5_AUTH_ANONYMOUS = 0x00
SOCKS5_AUTH_UNAME_PWD = 0x02
SOCKS5_AUTH_NO_ACCEPTABLE_METHODS = 0xFF

SOCKS5_ATYP_IPv4 = 0x01
SOCKS5_ATYP_DOMAIN = 0x03
SOCKS5_ATYP_IPv6 = 0x04

SOCKS5_ERRORS = {
    0x01: 'General SOCKS server failure',
    0x02: 'Connection not allowed by ruleset',
    0x03: 'Network unreachable',
    0x04: 'Host unreachable',
    0x05: 'Connection refused',
    0x06: 'TTL expired',
    0x07: 'Command not supported, or protocol error',
    0x08: 'Address type not supported'
}
