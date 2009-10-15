# -*- coding: utf-8 -*-
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

__MYSQL_DEBUG__ = False

import struct

def int1read(c):
    """
    Takes a bytes and returns it was an integer.
    
    Returns integer.
    """
    return int('%02x' % ord(c),16)

def int2read(s):
    """
    Takes a string of 2 bytes and unpacks it as unsigned integer.
    
    Returns integer.
    """
    if len(s) > 2:
        raise ValueError('int2read require s length of maximum 3 bytes')
    elif len(s) < 2:
        s = s + '\x00'
    return struct.unpack('<H', s)[0]

def int3read(s):
    """
    Takes a string of 3 bytes and unpacks it as integer.
    
    Returns integer.
    """
    if len(s) > 3:
        raise ValueError('int3read require s length of maximum 3 bytes')
    elif len(s) < 4:
        s = s + '\x00'*(4-len(s))
    return struct.unpack('<I', s)[0]
    
def int4read(s):
    """
    Takes a string of 4 bytes and unpacks it as integer.
    
    Returns integer.
    """
    if len(s) > 4:
        raise ValueError('int4read require s length of maximum 4 bytes')
    elif len(s) < 4:
        s = s + '\x00'*(4-len(s))
    return struct.unpack('<I', s)[0]

def intread(s):
    """
    Takes a string and unpacks it as an integer.
    
    This function uses int1read, int2read, int3read and int4read by
    checking the length of the given string.
    
    Returns integer.
    """
    l = len(s)
    if l < 1 or l > 4:
        raise ValueError('intread expects a string not longer than 4 bytes')
    if not isinstance(s, str):
        raise ValueError('intread expects a string')
    fs = {
        1 : int1read,
        2 : int2read,
        3 : int3read,
        4 : int4read,
    }
    return fs[l](s)

def int1store(i):
    """
    Takes an unsigned byte (1 byte) and packs it as string.
    
    Returns string.
    """
    if i < 0 or i > 255:
        raise ValueError('int1store requires 0 <= i <= 255')
    else:
        return struct.pack('<B',i)

def int2store(i):
    """
    Takes an unsigned short (2 bytes) and packs it as string.
    
    Returns string.
    """
    if i < 0 or i > 65535:
        raise ValueError('int2store requires 0 <= i <= 65535')
    else:
        return struct.pack('<H',i)

def int3store(i):
    """
    Takes an unsigned integer (3 bytes) and packs it as string.
    
    Returns string.
    """
    if i < 0 or i > 16777215:
        raise ValueError('int3store requires 0 <= i <= 16777215')
    else:
        return struct.pack('<I',i)[0:3]

def int4store(i):
    """
    Takes an unsigned integer (4 bytes) and packs it as string.
    
    Returns string.
    """
    if i < 0 or i > 4294967295L:
        raise ValueError('int4store requires 0 <= i <= 4294967295')
    else:
        return struct.pack('<I',i)

def intstore(i):
    """
    Takes an unsigned integers and packs it as a string.
    
    This function uses int1store, int2store, int3store and
    int4store depending on the integer value.
    
    returns string.
    """
    if i < 0 or i > 4294967295L:
        raise ValueError('intstore requires 0 <= i <= 4294967295')
        
    if i <= 255:
        fs = int1store
    elif i <= 65535:
        fs = int2store
    elif i <= 16777215:
        fs = int3store
    else:
        fs = int4store
        
    return fs(i)

def read_bytes(buf, size):
    """
    Reads bytes from a buffer.
    
    Returns a tuple with buffer less the read bytes, and the bytes.
    """
    s = buf[0:size]
    return (buf[size:], s)

def read_lc_string(buf):
    """
    Takes a buffer and reads a length coded string from the start.
    
    This is how Length coded strings work
    
    If the string is 250 bytes long or smaller, then it looks like this:

      <-- 1b  -->
      +----------+-------------------------
      |  length  | a string goes here
      +----------+-------------------------
  
    If the string is bigger than 250, then it looks like this:
    
      <- 1b -><- 2/3/4 ->
      +------+-----------+-------------------------
      | type |  length   | a string goes here
      +------+-----------+-------------------------
      
      if type == \xfc:
          length is code in next 2 bytes
      elif type == \xfd:
          length is code in next 3 bytes
      elif type == \xfe:
          length is code in next 4 bytes
     
    NULL has a special value. If the buffer starts with \xfb then
    it's a NULL and we return None as value.
    
    Returns a tuple (trucated buffer, string).
    """    
    if buf[0] == '\xfb':
        # NULL value
        return (buf[1:], None)
        
    l = lsize = start = 0
    fst = l = ord(buf[0])
    # Remove the type byte, we got the length information.
    buf = buf[1:]
    
    if fst <= 250:
        # Returns result right away.
        s = buf[:l]
        return (buf[l:], s)
    elif fst == 252:
        lsize = 2
    elif fst == 253:
        lsize = 3
    elif fst == 254:
        lsize = 4
    
    l = intread(buf[0:lsize])
    # Chop of the bytes which hold the length
    buf = buf[lsize:]
    # Get the actual string
    s = buf[0:l]
    # Set the buffer so we can return it
    buf = buf[l:]
    
    return (buf, s)

def read_string(buf, end=None, size=None):
    """
    Reads a string up until a character or for a given size.
    
    Returns a tuple (trucated buffer, string).
    """
    l = 0
    if end:
        # Get the length of string we need to get
        while buf[l] != end:
            l += 1
        if l > 0:
            return (buf[l+1:], buf[0:l])
    elif size:
        return read_bytes(buf,size)
    else:
        ValueError('read_string() needs either end or size.')
    
    return (buf, None)
    
def read_int(buf, size):
    """
    Take a buffer and reads an integer of a certain size (1 <= size <= 4).
    
    Returns a tuple (truncated buffer, int)
    """
    if len(buf) == 0:
        raise ValueError("Empty buffer.")

    i = None
    if size < 1 or size > 4:
        raise ValueError('read_int requires size of 1,2,3 or 4')
    else:
        if size == 1:
            i = int1read(buf[0])
        elif size == 2:
            i = int2read(buf[0:2])
        elif size == 3:
            i = int3read(buf[0:3])
        elif size == 4:
            i = int4read(buf[0:4])

    return (buf[size:], int(i))

def read_lc_int(buf):
    """
    Takes a buffer and reads an length code string from the start.
    
    Returns a tuple with buffer less the integer and the integer read.
    """
    (buf,s) = read_int(buf,1)    
    if s == 251:
        l = 0
        return (buf,None)
    elif s == 252:
        (buf,i) = read_int(buf,2)
    elif s == 253:
        (buf,i) = read_int(buf,4)
    elif s == 254:
        (buf,i) = read_int(buf,8)
    else:
        i = s
    
    return (buf, int(i))

#
# For debugging
#
def _dump_buffer(buf, label=None):
    import __main__
    if not __main__.__dict__.has_key('__MYSQL_DEBUG__'):
        return
    else:
        debug = __main__.__dict__['__MYSQL_DEBUG__']
        
    try:
        if debug:
            if len(buf) == 0:
                print "%s : EMPTY BUFFER" % label
            import string
            print "%s: %s" % (label,string.join( [ "%02x" % ord(c) for c in buf ], ' '))
            if debug > 1:
                print "%s: %s" % (label,string.join( [ "%s" % chr(ord(c)) for c in buf ], ''))
    except:
        raise
