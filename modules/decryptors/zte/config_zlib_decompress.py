# Name:ZTE config.bin XML extractor
# File:config_zlib_decompress.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 26.12.2015
# Last modified: 26.12.2015
# Shodan Dork:
# Description: Extract XML from config.bin for various ZTE devices.
# You may want to run binwalk on config.bin first, so far I've seen 3 types of config.bin
# 1. Header+plain XML 2. Header+zlib XML 3. Header+unknown encryption/obfuscation
# Based on :
# http://reverseengineering.stackexchange.com/questions/3593/re-compressed-backup-file-router-linux-based-so-is-it-compresed-with-zlib
# TODO reverse process
import core.Decryptor
import core.io


from interface.messages import print_success
import struct
import zlib
import re


class Decryptor(core.Decryptor.RextDecryptor):
    """
Name:ZTE config.bin XML extractor
File:config_zlib_decompress.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 26.12.2015
Description: Extract XML from config.bin for various ZTE devices.
    You may want to run binwalk on config.bin first, so far I've seen 3 types of config.bin
    1. Header+plain XML 2. Header+zlib XML 3. Header+unknown encryption/obfuscation
Based on :
http://reverseengineering.stackexchange.com/questions/3593/re-compressed-backup-file-router-linux-based-so-is-it-compresed-with-zlib
http://reverseengineering.stackexchange.com/questions/11626/zte-encrypted-backup-config-file
Options:
    Name        Description

    file        Input config file path
    """

    def __init__(self):
        core.Decryptor.RextDecryptor.__init__(self)

    def do_run(self, e):
        f = open(self.input_file, 'rb')
        data = f.read()
        f.close()
        core.io.writefile(self.extract_config_xml(data), "config.xml")
        print_success("Config.bin extracted to config.xml")

    def extract_config_xml(self, config_bin):
        config_xml = b''
        for zlib_chunk in re.finditer(b'\x78\xda', config_bin):
            zlib_chunk_start = zlib_chunk.start()
            zlib_chunk_header = config_bin[zlib_chunk_start - 12: zlib_chunk_start]
            xml_chunk_length, zlib_chunk_length, config_bin_length = \
                struct.unpack('>LLL', zlib_chunk_header)
            if xml_chunk_length == 0x10000 or config_bin_length == 0:
                zlib_chunk_end = zlib_chunk_start + zlib_chunk_length
                zlib_chunk = config_bin[zlib_chunk_start: zlib_chunk_end]
                xml_chunk = zlib.decompress(zlib_chunk)
                assert xml_chunk_length == len(xml_chunk)
                config_xml += xml_chunk
        return config_xml


Decryptor()
