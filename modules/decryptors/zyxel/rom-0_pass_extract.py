# Name:ZyNOS rom-0 config file decompress and admin password extract
# File:rom-0_pass_extract.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 18.2.2014
# Last modified: 12.11.2016
# Description: Decompress rom-0 file from ZyNOS, older files (round 16kB are compressed by LZS algorithm)
#             newer files (around 60kB) seems to be using something else???
# http://reverseengineering.stackexchange.com/questions/3662/backup-from-zynos-but-can-not-be-decompressed-with-lzs
# based on https://packetstormsecurity.com/files/127049/ZTE-TP-Link-ZynOS-Huawei-rom-0-Configuration-Decompressor.html
import core.Decryptor
import core.io
import core.compression.lzs
import interface.utils
from interface.messages import print_success, print_info


class Decryptor(core.Decryptor.RextDecryptor):
    """
Name:ZyNOS rom-0 config file decompress and admin password extract
File:rom-0_pass_extract.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 18.2.2014
Description: Decompress rom-0 file (spt.dat) from ZyNOS and try to extract strings.

Options:
    Name        Description

    file        Input firmware file path
    """
    def __init__(self):
        core.Decryptor.RextDecryptor.__init__(self)

    def do_run(self, e):
        f = open(self.input_file, 'rb')
        # These should be offsets of spt.dat but it somehow works with these values usually,
        # the core.compression.lzs is not a very good implementation, it won't decompress the whole file correctly
        # but it's enough to to extract admin password
        fpos = 8568
        fend = 8788
        f.seek(fpos)
        amount = 221
        while fpos < fend:
            if fend - fpos < amount:
                amount = amount
                data = f.read(amount)
                fpos += len(data)
        result, window = core.compression.lzs.LZSDecompress(data)
        print_info("Printing strings found in decompressed data (admin password is usually the first found):")
        for s in interface.utils.strings(result):
            print_success(s)

Decryptor()

