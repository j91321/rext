# Name:Draytek Vigor 2XXX/3XXX series FW decompression and FS extraction
# File:vigor_fw_decompress.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 25.2.2014
# Last modified: 25.2.2014
# Shodan Dork:
# Description: Decompress FW file extract FS
# Based on draytools work of Nikita Abdullin (AMMOnium) https://github.com/ammonium/draytools

import core.Decryptor
import core.io
import core.compression.lzo

from interface.messages import print_error, print_success, print_warning, print_info
from struct import unpack, pack
import os


class Decryptor(core.Decryptor.RextDecryptor):
    """
Name:Draytek Vigor 2XXX/3XXX series FW decompression and FS extraction
File:vigor_fw_decompress.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 25.2.2014
Description: Decompress firmware file extract filesystem

Options:
    Name        Description

    file        Input firmware file path
    """

    def __init__(self):
        core.Decryptor.RextDecryptor.__init__(self)

    def do_run(self, e):
        f = open(self.input_file, 'rb')
        data = f.read()
        f.close()
        result = self.decompress_firmware(data)
        if result is not None:
            dirpath = core.io.writefile(result, "fw.decomp")
            print_success("Decompressed firmware written to fw.decomp")
            self.decompress_fs_only(data, dirpath)
            print_success("FS decompressed")

    #Code from draytools, with minor modifications for REXT and python3
    @staticmethod
    def decompress_firmware(data):
        """Decompress firmware"""
        flen = len(data)
        sigstart = data.find(b'\xA5\xA5\xA5\x5A\xA5\x5A')
        # Try an alternative signature
        if sigstart <= 0:
            sigstart = data.find(b'\x5A\x5A\xA5\x5A\xA5\x5A')
        # Compressed FW block found, now decompress
        if sigstart > 0:
            print_info('Signature found at [0x%08X]' % sigstart)
            lzosizestart = sigstart + 6
            lzostart = lzosizestart + 4
            lzosize = unpack('>L', bytes(data[lzosizestart:lzostart]))[0]
            return data[0x100:sigstart + 2] + core.compression.lzo.pydelzo.decompress(
                b'\xF0' + pack(">L", 0x1000000) + data[lzostart:lzostart + lzosize])
        else:
            print_error('Compressed FW signature not found!')
            return None

    def decompress_fs_only(self, data, path):
        """Decompress filesystem"""
        fsstart = unpack('>L', data[:4])[0]
        print_info('FS block start at: %d [0x%08X]' % (fsstart, fsstart))
        return self.decompress_fs(data[fsstart:], path)

    def decompress_fs(self, data, path):
        """Decompress filesystem"""
        lzofsdatalen = unpack('>L', data[4:8])[0]
        print_info('Compressed FS length: %d [0x%08X]' % (lzofsdatalen, lzofsdatalen))
        # stupid assumption of raw FS length. Seems OK for now
        fsdatalen = 0x800000
        fs_raw = core.compression.lzo.pydelzo.decompress(b'\xF0' + pack(">L", fsdatalen)
                                                         + data[0x08:0x08 + lzofsdatalen])
        cfs = fs(fs_raw)
        return lzofsdatalen, cfs.save_all(path)


class fs:
    """Draytek filesystem utilities"""

    def __init__(self, data):
        self.cdata = data

    def get_fname(self, i):
        """Return full filename of the file #i from FS header"""
        addr = 0x10 + i * 44
        return bytes(self.cdata[addr: addr + 0x20].strip(b'\x00')).decode()

    def get_hash(self, i):
        """Return currently unknown hash for the file #i from FS header"""
        addr = 0x10 + i * 44 + 0x20
        return unpack("<L", bytes(self.cdata[addr: addr + 4]))[0]

    def get_offset(self, i):
        """Return offset of the file #i in FS block"""
        addr = 0x10 + i * 44 + 0x24
        return unpack("<L", bytes(self.cdata[addr: addr + 4]))[0] + self.datastart

    def get_fsize(self, i):
        """Return compressed size of the file #i"""
        addr = 0x10 + i * 44 + 0x28
        return unpack("<L", bytes(self.cdata[addr: addr + 4]))[0]

    def save_file(self, i):
        """Extract file #i from current FS"""
        fname = self.get_fname(i)
        # compressed file data offset in FS block
        ds = self.get_offset(i)
        # size of compressed file
        fs = self.get_fsize(i)
        # compressed file data
        fdata = self.cdata[ds: ds + fs]
        # create all subdirs along the path if they don't exist
        pp = fname.split('\\')
        pp = [self.path] + pp
        ppp = os.sep.join(pp[:-1])
        if len(pp) > 1:
            if not os.path.exists(ppp):
                os.makedirs(ppp)
        nfname = os.sep.join(pp)
        # size of uncompressed file
        rawfs = -1
        ff = open(nfname, 'wb')
        # perform extraction, some file types are not compressed
        if fs > 0:
            if pp[-1].split('.')[-1].lower() in ['gif', 'jpg', 'cgi', 'cab', 'txt', 'jar']:
                rawfdata = fdata
            else:
                try:
                    rawfdata = core.compression.lzo.pydelzo.decompress(b'\xF0' + pack(">L", fs * 64) + fdata)
                except core.compression.lzo.LZO_ERROR as lze:
                    print_warning('File "' + fname + '" is damaged or uncompressed ['
                                  + str(lze)
                                  + '], RAW DATA WRITTEN')
                    rawfdata = fdata
        else:
            rawfdata = ''
        rawfs = len(rawfdata)
        ff.write(rawfdata)
        ff.close()
        # print some debug info for each file
        print_info('%08X "' % ds + fname + '" %08X' % fs + ' %08X' % rawfs)
        return fs, rawfs

    def save_all(self, path):
        """Extract all files from current FS"""
        self.path = path
        numfiles = unpack("<H", bytes(self.cdata[0x0E:0x10]))[0]
        # All files data block offset in FS
        self.datastart = 0x10 + 44 * numfiles
        for i in range(numfiles):
            fs, rawfs = self.save_file(i)
        return numfiles


Decryptor()


