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

"""Python exceptions
"""

class Error(StandardError):
    
    def __init__(self, m):
        try:
            # process MySQL error packet
            self._process_packet(m)
        except:
            # else the message should be a string
            self.errno = -1
            self.errmsg = str(m)
            self.sqlstate = -1
            self.msg = str(m)

    def _process_packet(self, packet):
        self.errno = packet.errno
        self.errmsg = packet.errmsg
        self.sqlstate = packet.sqlstate
        if self.sqlstate:
            m = '%d (%s): %s' % (self.errno, self.sqlstate, self.errmsg)
        else:
            m = '%d: %s' % (self.errno, self.errmsg)
        self.errmsglong = m
        self.msg = m
    
    def __str__(self):
        return self.msg
        
    def __unicode__(self):
        return self.msg
        
class Warning(StandardError):
    pass

class InterfaceError(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class DatabaseError(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class InternalError(DatabaseError):
    pass

class OperationalError(DatabaseError):
    pass

class ProgrammingError(DatabaseError):
    pass

class IntegrityError(DatabaseError):
    pass

class DataError(DatabaseError):
    pass

class NotSupportedError(DatabaseError):
    pass
