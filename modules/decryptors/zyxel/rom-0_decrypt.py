#Name:ZyNOS rom-0 config file decryption
#File:rom-0_decrypt.py
#Author:Ján Trenčanský
#License: ADD LATER
#Created: 18.2.2014
#Last modified: 18.2.2014
#Shodan Dork:
#Description: Decrypts rom-0 file from ZyNOS, older files (round 16kB are compressed by LZS algorithm)
#             newer files (around 60kB) seems to be using something else???
#http://reverseengineering.stackexchange.com/questions/3662/backup-from-zynos-but-can-not-be-decompressed-with-lzs

import core.Decryptor
import core.io
import core.compression.lzs


#TODO Not completed please do not use
class Decryptor(core.Decryptor.RextDecryptor):
    def __init__(self):
        core.Decryptor.RextDecryptor.__init__(self)

    def do_run(self, e):
        f = open(self.input_file, 'rb')
        result, window = core.compression.lzs.LZSDecompress(f.read())
        print(result)

Decryptor()

