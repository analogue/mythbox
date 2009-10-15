"""
Connector/Python, native MySQL driver written in Python.
Copyright 2009 Sun Microsystems, Inc. All rights reserved. Use is subject to license terms.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import sys, struct

import tests
from mysql.connector import mysql, connection, cursor, conversion, protocol, utils, errors, constants

class UtilsTests(tests.MySQLConnectorTests):
    """Testing the helper functions in the utils module.
    
    These tests should not make a connection to the database.
    """

    def test_int1read(self):
        """Pass int1read a valid string of 1 byte long."""
        i = 65
        byte = chr(0x41)  # A
        self.failUnlessEqual( i, utils.int1read(byte))

    def test_int1read_fail(self):
        """Pass int1read an invalid string of 2 bytes long"""
        i = 65
        byte = chr(0x41) + chr(0x42) # A
        try:
            utils.int1read(byte)
        except:
            pass
        else:
            self.fail("int1read should have raise an exception")

    def test_int2read(self):
        """Pass int2read a valid string of 2 bytes long."""
        i = 65 + (66 << 8)
        bytes = chr(0x41) + chr(0x42) # AB
        self.failUnlessEqual( i, utils.int2read(bytes))
    
    def test_int2read_fail(self):
        """Pass int2read an invalid string of 3 bytes long"""
        byte = chr(0x41) * 3
        try:
            utils.int1read(byte)
        except:
            pass
        else:
            self.fail("int2read should have raise an exception")

    def test_int3read(self):
        """Pass int3read a valid string of 3 bytes long."""
        i = 65 + (66 << 8) + (67 << 16)
        bytes = chr(0x41) + chr(0x42) + chr(0x43) # ABC
        self.failUnlessEqual( i, utils.int3read(bytes))
    
    def test_int3read_fail(self):
        """Pass int3read an invalid string of 4 bytes long"""
        byte = chr(0x41) * 4
        try:
            utils.int1read(byte)
        except:
            pass
        else:
            self.fail("int3read should have raise an exception")

    def test_int4read(self):
        """Pass int4read a valid string of 4 bytes long."""
        i = 65 + (66 << 8) + (67 << 16) + (68 << 24)
        bytes = chr(0x41) + chr(0x42) + chr(0x43)+ chr(0x44) # ABC
        self.failUnlessEqual( i, utils.int4read(bytes))
    
    def test_int4read_fail(self):
        """Pass int4read an invalid string of 5 bytes long"""
        byte = chr(0x41) * 5
        try:
            utils.int1read(byte)
        except:
            pass
        else:
            self.fail("int4read should have raise an exception")

    def test_intread(self):
        """Use intread to read from valid strings."""
        try:
            for r in range(4):
                utils.intread('a'*(r+1))
        except ValueError, e:
            self.fail("intread failed calling 'int%dread: %s" % \
                (int(r)+1), e)
    
    def test_int1store(self):
        """Use int1store to pack an integer (2^8) as a string."""
        data = 2**(8-1)
        exp = struct.pack('<B',data)
        
        try:
            result = utils.int1store(data)
        except ValueError, e:
            self.fail("int1store failed: %s" % e)
        else:
            if not isinstance(result, str):
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (type(exp), type(result)))
            elif exp != result:
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (data, result))
                
    def test_int2store(self):
        """Use int2store to pack an integer (2^16) as a string."""
        data = 2**(16-1)
        exp = struct.pack('<H',data)
        
        try:
            result = utils.int2store(data)
        except ValueError, e:
            self.fail("int2store failed: %s" % e)
        else:
            if not isinstance(result, str):
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (type(exp), type(result)))
            elif exp != result:
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (data, result))

    def test_int3store(self):
        """Use int3store to pack an integer (2^24) as a string."""
        data = 2**(24-1)
        exp = struct.pack('<I',data)[0:3]
        
        try:
            result = utils.int3store(data)
        except ValueError, e:
            self.fail("int3store failed: %s" % e)
        else:
            if not isinstance(result, str):
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (type(exp), type(result)))
            elif exp != result:
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (data, result))

    def test_int4store(self):
        """Use int4store to pack an integer (2^32) as a string."""
        data = 2**(32-1)
        exp = struct.pack('<I',data)
        
        try:
            result = utils.int4store(data)
        except ValueError, e:
            self.fail("int4store failed: %s" % e)
        else:
            if not isinstance(result, str):
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (type(exp), type(result)))
            elif exp != result:
                self.fail("Wrong result. Expected %s, we got %s" %\
                    (data, result))

    def test_intstore(self):
        """Use intstore to pack valid integers (2^32 max) as a string."""
        try:
            for i,r in enumerate((8, 16, 24, 32)):
                val = 2**(r-1)
                utils.intstore(val)
        except ValueError, e:
            self.fail("intstore failed with 'int%dstore: %s" %\
                (i,e))
    
    def test_read_bytes(self):
        """Read a number of bytes from a bufffer"""
        buf = "ABCDEFghijklm"
        readsize = 6
        exp = "ghijklm"
        expsize = len(exp)
        
        try:
            (result, s) = utils.read_bytes(buf, readsize)
        except:
            self.fail("Failed reading bytes using read_bytes.")
        else:
            if result != exp or len(result) != expsize:
                self.fail("Wrong result. Expected: '%s' / %d, got '%s'/%d" %\
                    (exp, expsize, result, len(result)))
    
    def test_read_lc_string_1(self):
        """Read a length code string from a buffer ( <= 250 bytes)"""
        exp = "a" * 2**(8-1)
        expsize = len(exp)
        lcs = utils.int1store(expsize) + exp
        
        (rest, result) = utils.read_lc_string(lcs)
        if result != exp or len(result) != expsize:
            self.fail("Wrong result. Expected '%d', got '%d'" %\
                expsize, len(result))

    def test_read_lc_string_2(self):
        """Read a length code string from a buffer ( <= 2^16 bytes)"""
        exp = "a" * 2**(16-1)
        expsize = len(exp)
        lcs = '\xfc' + utils.int2store(expsize) + exp

        (rest, result) = utils.read_lc_string(lcs)
        if result != exp or len(result) != expsize:
            self.fail("Wrong result. Expected '%d', got '%d'" %\
                expsize, len(result))

    def test_read_lc_string_3(self):
        """Read a length code string from a buffer ( <= 2^24 bytes)"""
        exp = "a" * 2**(24-1)
        expsize = len(exp)
        lcs = '\xfd' + utils.int3store(expsize) + exp

        (rest, result) = utils.read_lc_string(lcs)
        if result != exp or len(result) != expsize:
            self.fail("Wrong result. Expected size'%d', got '%d'" %\
                expsize, len(result))

    def test_read_lc_string_4(self):
        """Read a length code string from a buffer ( <= 2^32 bytes)"""
        exp = "a" * 2**(24+2)  # doing 2**(32-1) overflows because long
        expsize = len(exp)
        lcs = '\xfe' + utils.int4store(expsize) + exp

        (rest, result) = utils.read_lc_string(lcs)
        if result != exp or len(result) != expsize:
            self.fail("Wrong result. Expected size '%d', got '%d'" %\
                expsize, len(result))
    
    def test_read_lc_string_5(self):
        """Read a length code string from a buffer which is 'NULL'"""
        exp = 'abc'
        lcs = '\xfb' + 'abc'
        
        (rest, result) = utils.read_lc_string(lcs)
        if result != None or rest != 'abc':
            self.fail("Wrong result. Expected None.")
    
    def test_read_string_1(self):
        """Read a string from a buffer up until a certain character."""
        buf = 'abcdef\x00ghijklm'
        exp = 'abcdef'
        exprest = 'ghijklm'
        end = '\x00'
        
        (rest, result) = utils.read_string(buf, end=end)
        if result != exp:
            self.fail("Wrong result. Expected '%s', got '%s'" %\
                exp, result)
        elif rest != exprest:
            self.fail("Wrong result. Expected '%s', got '%s'" %\
                exp, result)
    
    def test_read_string_2(self):
        """Read a string from a buffer up until a certain size."""
        buf = 'abcdefghijklm'
        exp = 'abcdef'
        exprest = 'ghijklm'
        size = 6
        
        (rest, result) = utils.read_string(buf, size=size)
        if result != exp:
            self.fail("Wrong result. Expected '%s', got '%s'" %\
                exp, result)
        elif rest != exprest:
            self.fail("Wrong result. Expected '%s', got '%s'" %\
                exp, result)
        