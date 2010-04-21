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

"""Implementing communication to MySQL servers
"""

import socket
import os

import protocol
import errors
from constants import CharacterSet

class MySQLBaseConnection(object):
    """Base class for MySQL Connections subclasses.
    
    Should not be used directly but overloaded, changing the
    open_connection part. Examples over subclasses are
      MySQLTCPConnection
      MySQLUNIXConnection
    """
    def __init__(self, prtcls=None):
        self.sock = None # holds the socket connection
        self.connection_timeout = None
        self.protocol = None
        self.socket_flags = 0
        try:
            self.protocol = prtcls(self)
        except:
            self.protocol = protocol.MySQLProtocol(self)
        self._set_socket_flags()
        
    def open_connection(self):
        pass
    
    def close_connection(self):
        try:
            self.sock.close()
        except:
            pass

    def send(self, buf):
        """
        Send packets using the socket to the server.
        """
        pktlen = len(buf)
        try:
            while pktlen:
                pktlen -= self.sock.send(buf)
        except Exception, e:
            raise errors.OperationalError('%s' % e)

#    def recv(self):
#        """
#        Receive packets using the socket from the server.
#        """
#        try:
#            header = self.sock.recv(4, self.socket_flags)
#            (pktsize, pktnr) = self.protocol.handle_header(header)
#            buf = header + self.sock.recv(pktsize, self.socket_flags)
#            self.protocol.is_error(buf)
#        except:
#            raise
#
#        return (buf, pktsize, pktnr)

    def recv(self):
        """
        Receive packets using the socket from the server.
        """
        try:
            #header = self.sock.recv(4, self.socket_flags)
            header = self.recv_all(self.sock, 4)
            (pktsize, pktnr) = self.protocol.handle_header(header)
            #buf = header + self.sock.recv(pktsize, self.socket_flags)
            buf = header + self.recv_all(self.sock, pktsize)
            #print('buflen=%d pktsize=%d pktnr=%d sum=%d' % (len(buf), pktsize, pktnr, pktsize + 4))
            self.protocol.is_error(buf)
        except: # socket.timeout, errmsg:
            raise # InterfaceError('Timed out reading from socket.')

        return (buf, pktsize, pktnr)

    def recv_all(self, socket, bytes):
        """Receive an exact number of bytes.
    
        Regular Socket.recv() may return less than the requested number of bytes,
        dependning on what's in the OS buffer.  MSG_WAITALL is not available
        on all platforms, but this should work everywhere.  This will return
        less than the requested amount if the remote end closes.
    
        This isn't optimized and is intended mostly for use in testing.
        """
        b = ''
        while len(b) < bytes:
            left = bytes - len(b)
            try:
                new = socket.recv(left)
            except Exception, e:
                print('left bytes = %d out of %d'  % (left, bytes))
                raise e
            if new == '':
                break # eof
            b += new
        return b

    def set_protocol(self, prtcls):
        try:
            self.protocol = prtcls(self, self.protocol.handshake)
        except:
            self.protocol = protocol.MySQLProtocol(self)
    
    def set_connection_timeout(self, timeout):
        self.connection_timeout = timeout

    def _set_socket_flags(self, flags=None):
        self.socket_flags = 0
        if flags is None:
            if os.name == 'nt':
                flags = 0
            else:
                flags = socket.MSG_WAITALL
                
        if flags is not None:
            self.socket_flags = flags
    

class MySQLUnixConnection(MySQLBaseConnection):
    """Opens a connection through the UNIX socket of the MySQL Server."""
    
    def __init__(self, prtcls=None,unix_socket='/tmp/mysql.sock'):
        MySQLBaseConnection.__init__(self, prtcls=prtcls)
        self.unix_socket = unix_socket
        self.socket_flags = socket.MSG_WAITALL
        
    def open_connection(self):
        """Opens a UNIX socket and checks the MySQL handshake."""
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.settimeout(self.connection_timeout)
            self.sock.connect(self.unix_socket)
        except StandardError, e:
            raise errors.OperationalError('%s' % e)
        
        buf = self.recv()[0]
        self.protocol.handle_handshake(buf)

class MySQLTCPConnection(MySQLBaseConnection):
    """Opens a TCP connection to the MySQL Server."""
    
    def __init__(self, prtcls=None, host='127.0.0.1', port=3306):
        MySQLBaseConnection.__init__(self, prtcls=prtcls)
        self.server_host = host
        self.server_port = port
        
    def open_connection(self):
        """Opens a TCP Connection and checks the MySQL handshake."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.connection_timeout)
            self.sock.connect( (self.server_host, self.server_port) )
        except StandardError, e:
            raise errors.OperationalError('%s' % e)
            
        buf = self.recv()[0]
        self.protocol.handle_handshake(buf)

        
