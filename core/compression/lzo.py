#!/usr/bin/env python
#
# This program uses code translated from Java code of Java-LZO compression 
# program by Markus Oberhumer, author of LZO algorithm and its implementation
#
# http://www.oberhumer.com/opensource/lzo/
#
# Copyright (C) 1999 Markus Franz Xaver Johannes Oberhumer
#  Copyright (C) 1998 Markus Franz Xaver Johannes Oberhumer
#  Copyright (C) 1997 Markus Franz Xaver Johannes Oberhumer
#  Copyright (C) 1996 Markus Franz Xaver Johannes Oberhumer
#
#  The LZO library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#
#  The LZO library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with the LZO library; see the file COPYING.
#  If not, write to the Free Software Foundation, Inc.,
#  59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#  Markus F.X.J. Oberhumer
#  <markus.oberhumer@jk.uni-linz.ac.at>
#  http://wildsau.idv.uni-linz.ac.at/mfx/lzo.html
#
#
#
# Translation into Python by AMMOnium <ammonium at mail dot ru>
#

from struct import unpack


class LZO_ERROR(Exception):
    ed = {0: 'LZO_E_OK',
          -1: 'LZO_E_ERROR',
          -2: 'LZO_E_OUT_OF_MEMORY',
          -3: 'LZO_E_NOT_COMPRESSIBLE',
          -4: 'LZO_E_INPUT_OVERRUN',
          -5: 'LZO_E_OUTPUT_OVERRUN',
          -6: 'LZO_E_LOOKBEHIND_OVERRUN',
          -7: 'LZO_E_EOF_NOT_FOUND',
          -8: 'LZO_E_INPUT_NOT_CONSUMED'}

    def __init__(self, value, pos=0):
        self.value = value
        self.pos = pos

    def __str__(self):
        return (repr(self.ed[self.value])
                + ' at offset %d [0x%x]' % (self.pos, self.pos))


class pydelzo:
    """Python translation of Java-LZO decompression code"""
    __version__ = "0.1"
    copyright = "LZO Copyright (C) 1996-1999 Markus F.X.J. Oberhumer " \
                "<markus.oberhumer@jk.uni-linz.ac.at>"

    LZO_E_OK = 0
    LZO_E_ERROR = -1
    LZO_E_OUT_OF_MEMORY = -2
    LZO_E_NOT_COMPRESSIBLE = -3
    LZO_E_INPUT_OVERRUN = -4
    LZO_E_OUTPUT_OVERRUN = -5
    LZO_E_LOOKBEHIND_OVERRUN = -6
    LZO_E_EOF_NOT_FOUND = -7
    LZO_E_INPUT_NOT_CONSUMED = -8

    @staticmethod
    def decompress(buf, strict=False):
        """Perform decompression of a data block"""
        # length of uncompressed data
        raw_len = unpack('>L', bytes(buf[1:5]))[0]

        dst = bytearray(raw_len)

        src_len = len(buf) - 5
        dst_len = [0]
        dst_off = 0
        src_off = 0
        src = bytearray(buf[5:]) + bytearray(256)
        r = pydelzo.int_decompress(src, src_off, raw_len,
                                   dst, dst_off, dst_len)
        # if strict mode is on, die if header had specified more data 
        # than actually received
        if r != pydelzo.LZO_E_OK:
            if strict or \
                    (not strict and r != pydelzo.LZO_E_INPUT_NOT_CONSUMED):
                raise LZO_ERROR(r, dst_len[0])
        return dst[:min(raw_len, dst_len[0])]

    #    @profile
    @staticmethod
    def int_decompress(src, src_off, src_len, dst, dst_off, dst_len):
        """Internal decompression subroutine"""
        ip = src_off
        op = dst_off
        t = src[ip]
        ip += 1

        if t > 17:
            t -= 17
            dst[op:op + t] = src[ip:ip + t]
            op += t
            ip += t

            t = src[ip]
            ip += 1

            if t < 16:
                return pydelzo.LZO_E_ERROR

        while True:
            lf = False
            if t < 16:
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 15 + src[ip]
                    ip += 1

                t += 3
                dst[op:op + t] = src[ip:ip + t]
                op += t
                ip += t

                t = src[ip]
                ip += 1

                if t < 16:
                    m_pos = op - 0x801 - (t >> 2) - (src[ip] << 2)
                    ip += 1

                    if m_pos < dst_off:
                        t = pydelzo.LZO_E_LOOKBEHIND_OVERRUN
                        break

                    t = 3
                    dst[op:op + t] = src[m_pos:m_pos + t]
                    op += t
                    m_pos += t

                    t = src[ip - 2] & 3
                    if t == 0:
                        continue

                    dst[op:op + t] = src[ip:ip + t]
                    op += t
                    ip += t

                    t = src[ip]
                    ip += 1

            while True:
                if t >= 64:
                    m_pos = op - 1 - ((t >> 2) & 7) - (src[ip] << 3)
                    ip += 1
                    t = (t >> 5) - 1
                elif t >= 32:
                    t &= 31
                    if t == 0:
                        while src[ip] == 0:
                            t += 255
                            ip += 1
                        t += 31 + src[ip]
                        ip += 1

                    m_pos = op - 1 - (src[ip] >> 2)
                    ip += 1

                    m_pos -= (src[ip] << 6)
                    ip += 1

                elif t >= 16:
                    m_pos = op - ((t & 8) << 11)
                    t &= 7
                    if t == 0:
                        while src[ip] == 0:
                            t += 255
                            ip += 1
                        t += 7 + src[ip]
                        ip += 1
                    m_pos -= (src[ip] >> 2)
                    ip += 1

                    m_pos -= (src[ip] << 6)
                    ip += 1

                    if m_pos == op:
                        lf = True
                        break

                    m_pos -= 0x4000
                else:
                    m_pos = op - 1 - (t >> 2) - (src[ip] << 2)
                    ip += 1
                    t = 0

                if m_pos < dst_off:
                    t = pydelzo.LZO_E_LOOKBEHIND_OVERRUN
                    lf = True
                    break

                t += 2

                for ii in range(t):
                    dst[op + ii] = dst[m_pos + ii]
                op += t
                m_pos += t

                t = src[ip - 2] & 3
                if t == 0:
                    break

                dst[op:op + t] = src[ip:ip + t]
                op += t
                ip += t

                t = src[ip]
                ip += 1

            if lf:
                lf = False
                break
            else:
                t = src[ip]
                ip += 1

        ip -= src_off
        op -= dst_off
        dst_len[0] = op
        if t < 0:
            return t

        if ip < src_len:
            return pydelzo.LZO_E_INPUT_NOT_CONSUMED

        if ip > src_len:
            return pydelzo.LZO_E_INPUT_OVERRUN

        if t != 1:
            return pydelzo.LZO_E_ERROR

        return pydelzo.LZO_E_OK
