# MySQL Connector/Python - MySQL driver written in Python.
# Copyright 2009 Sun Microsystems, Inc. All rights reserved
# Use is subject to license terms. (See COPYING)

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
# 
# There are special exceptions to the terms and conditions of the GNU
# General Public License as it is applied to this software. View the
# full text of the exception in file EXCEPTIONS-CLIENT in the directory
# of this software distribution or see the FOSS License Exception at
# www.mysql.com.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""Utilities
"""

__MYSQL_DEBUG__ = False

import struct

def int1read(c):
    """
    Takes a bytes and returns it was an integer.
    
    Returns integer.
    """
    if isinstance(c,int):
        if c < 0 or c > 254:
            raise ValueError('excepts int 0 <= x <= 254')
        return c
    elif len(c) > 1:
        raise ValueError('excepts 1 byte long bytes-object or int')
        
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

def int8read(s):
    """
    Takes a string of 8 bytes and unpacks it as integer.

    Returns integer.
    """
    if len(s) > 8:
        raise ValueError('int4read require s length of maximum 8 bytes')
    elif len(s) < 8:
        s = s + '\x00'*(8-len(s))
    return struct.unpack('<Q', s)[0]

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
        8 : int8read,
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
    fst = buf[0]
    # Remove the type byte, we got the length information.
    buf = buf[1:]
    
    if fst <= '\xFA':
        # Returns result right away.
        l = ord(fst)
        s = buf[:l]
        return (buf[l:], s)
    elif fst == '\xFC':
        lsize = 2
    elif fst == '\xFD':
        lsize = 3
    elif fst == '\xFE':
        lsize = 4
    
    l = intread(buf[0:lsize])
    # Chop of the bytes which hold the length
    buf = buf[lsize:]
    # Get the actual string
    s = buf[0:l]
    # Set the buffer so we can return it
    buf = buf[l:]
    
    return (buf, s)

def read_lc_string_list(buf):
    """
    Reads all length encoded strings from the given buffer.
    
    This is exact same function as read_lc_string() but duplicated
    in hopes for performance gain when reading results.
    """
    strlst = []
    
    while buf:
        if buf[0] == '\xfb':
            # NULL value
            buf = buf[1:]
            strlst.append(None)
            continue
        
        l = lsize = start = 0
        fst = buf[0]
        # Remove the type byte, we got the length information.
        buf = buf[1:]
    
        if fst <= '\xFA':
            # Returns result right away.
            l = ord(fst)
            strlst.append(buf[:l])
            buf = buf[l:]
            continue
        elif fst == '\xFC':
            lsize = 2
        elif fst == '\xFD':
            lsize = 3
        elif fst == '\xFE':
            lsize = 4
    
        l = intread(buf[0:lsize])
        # Chop of the bytes which hold the length
        buf = buf[lsize:]
        # Get the actual string
        s = buf[0:l]
        # Set the buffer so we can return it
        buf = buf[l:]
        
        strlst.append(s)

    return strlst

def read_string(buf, end=None, size=None):
    """
    Reads a string up until a character or for a given size.
    
    Returns a tuple (trucated buffer, string).
    """
    if end is None and size is None:
        raise ValueError('read_string() needs either end or size')
    
    if end is not None:
        try:
            idx = buf.index(end)
        except (ValueError), e:
            raise ValueError("end byte not precent in buffer")
        return (buf[idx+1:], buf[0:idx])
    elif size is not None:
        return read_bytes(buf,size)
    
    raise ValueError('read_string() needs either end or size (weird)')
    
def read_int(buf, size):
    """
    Take a buffer and reads an integer of a certain size (1 <= size <= 4).
    
    Returns a tuple (truncated buffer, int)
    """
    if len(buf) == 0:
        raise ValueError("Empty buffer.")
    if not isinstance(size,int) or (size not in [1,2,3,4,8]):
        raise ValueError('size should be int in range of 1..4 or 8')

    i = None
    if size == 1:
        i = int1read(buf[0])
    elif size == 2:
        i = int2read(buf[0:2])
    elif size == 3:
        i = int3read(buf[0:3])
    elif size == 4:
        i = int4read(buf[0:4])
    elif size == 8:
        i = int8read(buf[0:8])
    else:
        raise ValueError('size should be int in range of 1..4 or 8 (weird)')
        
    return (buf[size:], int(i))

def read_lc_int(buf):
    """
    Takes a buffer and reads an length code string from the start.
    
    Returns a tuple with buffer less the integer and the integer read.
    """
    if len(buf) == 0:
        raise ValueError("Empty buffer.")
    
    (buf,s) = read_int(buf,1)    
    if s == 251:
        l = 0
        return (buf,None)
    elif s == 252:
        (buf,i) = read_int(buf,2)
    elif s == 253:
        (buf,i) = read_int(buf,3)
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
