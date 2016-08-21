# Name:Draytek Vigor 2XXX/3XXX series config file decryption and decompression with password extraction
# File:vigor_config.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 7.3.2014
# Last modified: 7.3.2014
# Shodan Dork:
# Description: Guess the state of config file and decrypt and decompress it, extract passwords
# Based on draytools work of Nikita Abdullin (AMMOnium) https://github.com/ammonium/draytools
# TODO: No sample of older cfg file, so not able to test properly.
# TODO: All cfgs use new encryption. Works with decrypted cfg
import core.Decryptor
import core.io
import core.compression.lzo

from interface.messages import print_success, print_green, print_yellow, print_warning, print_info
from collections import defaultdict
from struct import unpack, pack
import math


class Decryptor(core.Decryptor.RextDecryptor):
    """
Name:Draytek Vigor 2XXX/3XXX series config file decryption and decompression with password extraction
File:vigor_config.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 7.3.2014
Description: Guess the state of config file and decrypt and decompress it, extract passwords
Based on: draytools work of Nikita Abdullin (AMMOnium) https://github.com/ammonium/draytools

Options:
    Name        Description

    file        Input config file path
    """

    CFG_RAW = 0
    CFG_LZO = 1
    CFG_ENC = 2

    def __init__(self):
        core.Decryptor.RextDecryptor.__init__(self)

    def do_run(self, e):
        f = open(self.input_file, 'rb')
        data = f.read()
        f.close()
        g, outdata = self.de_cfg(data)
        if g != self.CFG_RAW:
            core.io.writefile(outdata, "config.out")
            print_success("config file written to config.out, extracting credentials...")
        creds = self.get_credentials(outdata)
        print_green("Login    :\t" + (creds[0] == b"" and b"admin" or creds[0]).decode())
        print_green("Password :\t" + (creds[1] == b"" and b"admin" or creds[1]).decode())

    def de_cfg(self, data):
        """Get raw config data from raw /compressed/encrypted & comressed"""
        g = self.smart_guess(data)
        if g == self.CFG_RAW:
            print_warning('File is  :\tnot compressed, not encrypted')
            return g, data
        elif g == self.CFG_LZO:
            print_warning('File is  :\tcompressed, not encrypted')
            return g, self.decompress_cfg(data)
        elif g == self.CFG_ENC:
            print_warning('File is  :\tcompressed, encrypted')
            return g, self.decompress_cfg(self.decrypt_cfg(data))

    def smart_guess(self, data):
        """Guess is the cfg block compressed or not"""
        # Uncompressed block is large and has low entropy
        if self.entropy(data) < 1.0 or len(data) > 0x10000:
            return self.CFG_RAW
        # Compressed block still has pieces of cleartext at the beginning
        if b"Vigor" in data and (b"Series" in data or b"draytek" in data):
            return self.CFG_LZO
        return self.CFG_ENC

    def entropy(self, data):
        """Calculate Shannon entropy (in bits per byte)"""
        flist = defaultdict(int)
        dlen = len(data)
        data = map(int, data)
        # count occurencies
        for byte in data:
            flist[byte] += 1
        ent = 0.0
        # convert count of occurencies into frequency
        for freq in flist.values():
            if freq > 0:
                ffreq = float(freq) / dlen
                # actual entropy calcualtion
                ent -= ffreq * math.log(ffreq, 2)
        return ent

    def get_modelid(self, data):
        """Extract a model ID from config file header"""
        modelid = data[0x0C:0x0E]
        return modelid

    def decompress_cfg(self, data):
        """Decompress a config file"""
        modelstr = "V" + format(unpack(">H", self.get_modelid(data))[0], "04X")
        print_info('Model is :\t' + modelstr)
        rawcfgsize = 0x00100000
        lzocfgsize = unpack(">L", data[0x24:0x28])[0]
        raw = data[:0x2D] + b'\x00' + data[0x2E:0x100] + \
              core.compression.lzo.pydelzo.decompress(b'\xF0' + pack(">L", rawcfgsize) + data[0x100:0x100 + lzocfgsize])
        return raw

    def decrypt_cfg(self, data):
        """Decrypt config, bruteforce if default key fails"""
        modelstr = "V" + format(unpack(">H", self.get_modelid(data))[0], "04X")
        print_info('Model is :\t' + modelstr)
        ckey = self.make_key(modelstr)
        rdata = self.decrypt(data[0x100:], ckey)
        # if the decrypted data does not look good, bruteforce
        if self.smart_guess(rdata) != self.CFG_LZO:
            rdata = self.brute_cfg(data[0x100:])
            print_success('Used key :\t[0x%02X]' % ckey)
        return data[:0x2D] + b'\x01' + data[0x2E:0x100] + rdata

    def make_key(self, modelstr):
        """Construct a key out of a model string (like 'V2710')"""
        key_sum = 0
        for c in modelstr:
            key_sum += ord(c)
        return 0xFF & key_sum

    def enc(self, c, key):
        c ^= key
        c -= key
        c = 0xFF & (c >> 5 | c << 3)
        return c

    def dec(self, c, key):
        c = (c << 5 | c >> 3)
        c += key
        c ^= key
        c &= 0xFF
        return c

    def decrypt(self, data, key):
        """Decrypt a block of data using given key"""
        rdata = b''
        for i in range(len(data)):
            rdata += bytes(self.dec(data[i], key))
        return rdata

    #		return ''.join(map(lambda od:chr(draytools.dec(ord(od),key)),data))

    def brute_cfg(self, data):
        """Check all possible keys until data looks like decrypted"""
        rdata = None
        key = 0
        for i in range(256):
            rdata = self.decrypt(data, i)
            if self.smart_guess(rdata) == self.CFG_LZO:
                key = i
                break
        print_success('Found key:\t[0x%02X]' % key)
        return rdata

    def get_credentials(self, data):
        """Extract admin credentials from config"""
        login = data[0x100 + 0x28:0x100 + 0x40].split(b'\x00')[0]
        password = data[0x100 + 0x40:0x100 + 0x58].split(b'\x00')[0]
        return [login, password]


Decryptor()