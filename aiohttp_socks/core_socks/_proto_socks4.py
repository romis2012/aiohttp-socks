RSV = NULL = 0x00
SOCKS_VER4 = 0x04
SOCKS_CMD_CONNECT = 0x01
SOCKS4_GRANTED = 0x5A

SOCKS4_ERRORS = {
    0x5B: 'Request rejected or failed',
    0x5C: 'Request rejected because SOCKS server '
          'cannot connect to identd on the client',
    0x5D: 'Request rejected because the client program '
          'and identd report different user-ids'
}
