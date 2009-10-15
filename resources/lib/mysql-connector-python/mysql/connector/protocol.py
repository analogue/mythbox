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

import string
import socket
import re

try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1

from datetime import datetime
from time import strptime
from decimal import Decimal

from constants import *
from conversion import MySQLConverter
from errors import *
from utils import *
import utils

_default_client_flags = [
    ClientFlag.LONG_PASSWD,
    ClientFlag.LONG_FLAG,
    ClientFlag.CONNECT_WITH_DB,
    ClientFlag.PROTOCOL_41,
    ClientFlag.TRANSACTIONS,
    ClientFlag.SECURE_CONNECTION,
    ClientFlag.MULTI_STATEMENTS,
    ClientFlag.MULTI_RESULTS,
]

class MySQLBaseProtocol(object):
    """Base class handling the MySQL Protocol.
    
    By default the MySQL 4.1 Client/Server is implemented here, but
    MySQLProtocol41 should actually be used.
    """
    conn = None
    client_flags = 0
    
    def __init__(self, conn, handshake=None):
        self.conn = conn # MySQL Connection
        if handshake:
            self.set_handshake(handshake)
    
    def handle_header(self, buf):
        """Takes a buffer and readers information from header.
        
        Returns a tuple (pktsize, pktnr)
        """
        pktsize = utils.int3read(buf[0:3])
        pktnr = utils.int1read(buf[3])
        
        return (pktsize, pktnr)

    def do_auth(self,  username=None, password=None, database=None,
        client_flags=None):
        """
        Make and send the authentication using information found in the
        handshake packet.
        """
        if not client_flags:
            client_flags = 0
            for flag in _default_client_flags:
                client_flags |= flag
        
        auth = protocol.Auth(client_flags=client_flags,
            pktnr=self.handshake.pktnr+1)
        auth.create(username=username, password=password,
            seed=self.handshake.data['seed'], database=database)

        self.conn.send(auth.get())
        buf = self.conn.recv()[0]
        if database:
            self.cmd_init_db(database)
            
    def handle_handshake(self, buf):
        """
        Check whether the buffer is a valid handshake. If it is, we set some
        member variables for later usage. The handshake packet is returned for later
        usuage, e.g. authentication.
        """
        
        if self.is_error(buf):
            # an ErrorPacket is returned by the server
            self._handle_error(buf)
        
        handshake = None
        try:
            handshake = protocol.Handshake(buf)
        except InterfaceError, msg:
            raise InterfaceError(msg)
        self.set_handshake(handshake)
    
    def set_handshake(self, handshake):
        """Gather data from the given handshake."""
        ver = re.compile("^(\d{1,2})\.(\d{1,2})\.(\d{1,3})(.*)")
        version = handshake.data['version']
        m = ver.match(version)
        if not m:
            raise InterfaceError("Could not parse MySQL version, was '%s'" % version)
        else:
            self.server_version = tuple([ int(v) for v in m.groups()[0:3]])

        self.server_version_original = handshake.data['version']
        self.server_threadid = handshake.data['thrdid']
        self.capabilities = handshake.data['capabilities']
        self.charset = handshake.data['charset']
        self.threadid = handshake.data['thrdid']
        self.handshake = handshake

    def _handle_error(self, buf):
        """
        When we get an Error Result Packet, we raise an InterfaceError.
        """
        try:
            err = protocol.ErrorResultPacket(buf)
        except InterfaceError, e:
            raise e
        else:
            raise InterfaceError(err)
    
    def is_error(self, buf):
        """Check if the given buffer is a MySQL Error Packet.
        
        Buffer should start with \xff.

        Returns boolean.
        """
        if buf and buf[4] == '\xff':
            self._handle_error(buf)
            return True
        return False

    def _handle_ok(self, buf):
        """
        Handle an OK Result Packet. If we got an InterfaceError, raise that
        instead.
        """
        try:
            ok = protocol.OKResultPacket(buf)
        except InterfaceError, e:
            raise e
        else:
            self.server_status = ok.server_status
            self.warning_count = ok.warning_count
            self.field_count = ok.field_count
            self.affected_rows = ok.affected_rows
            self.info_msg = ok.info_msg

    def is_ok(self, buf):
        """
        Check if the given buffer is a MySQL OK Packet. It should
        start with \x00.

        Returns boolean.
        """
        if buf and buf[4] == '\x00':
            self._handle_ok(buf)
            return True
        return False

    def _handle_fields(self, nrflds):
        """Reads a number of fields from a result set."""
        i = 0
        fields = []
        while i < nrflds:
            buf = self.conn.recv()[0]
            fld = protocol.FieldPacket(buf)
            fields.append(fld)
            i += 1
        return fields
    
    def is_eof(self, buf):
        """
        Check if the given buffer is a MySQL EOF Packet. It should
        start with \xfe and be smaller 9 bytes.

        Returns boolean.
        """
        l = read_int(buf, 3)[1]
        if buf and buf[4] == '\xfe' and l < 9:
            return True
        return False

    def _handle_resultset(self, pkt):
        """Processes a resultset getting fields information.
        
        The argument pkt must be a protocol.Packet with length 1, a byte
        which contains the number of fields.
        """
        if not isinstance(pkt, protocol.Packet):
            raise ValueError, "%s is not a protocol.Packet" % startpkt
        
        if pkt.get_length() == 1:
            (buf,nrflds) = utils.read_lc_int(pkt.buffer)
            
            # Get the fields
            fields = self._handle_fields(nrflds)

            buf = self.conn.recv()[0]
            eof = protocol.EOFPacket(buf)

            return (nrflds, fields, eof)
        else:
            raise InterfaceError, 'Something wrong reading result after query. Doing something unsupported?'


    def result_get_rows(self, limit=-1):
        """
        Get all rows data. Should be called after getting the field
        descriptions.

        Returns a tuple with 2 elemends: list of rows and the
        EOF packet useful getting the nr warnings.
        """
        rows = []
        eof = None
        nr = 0
        while True:
            buf = self.conn.recv()[0]
            if self.is_eof(buf):
                eof = protocol.EOFPacket(buf)
                break
            rowdata = protocol.RowDataPacket(buf)
            rows.append(rowdata)
            if len(rows) == limit and limit != -1:
                break
        return ( rows, eof )

    def result_get_row(self):
        """
        Get one row's data. Should be called after getting the field
        descriptions.

        Returns a tuple with 2 elemends: a row's data and the
        EOF packet useful getting the nr warnings.
        """
        buf = self.conn.recv()[0]
        if self.is_eof(buf):
            eof = protocol.EOFPacket(buf)
            rowdata = None
        else:
            eof = None
            rowdata = protocol.RowDataPacket(buf)
        return (rowdata, eof)

    def cmd_query(self, query):
        """
        Sends a query to the server.
        
        Returns a tuple, when the query returns a result. The tuple
        consist number of fields and a list containing their descriptions.
        If the query doesn't return a result set, the an OKResultPacket
        will be returned.
        """
        cmd = protocol.CommandPacket()
        cmd.set_command(ServerCmd.QUERY)
        cmd.set_argument(query)
        cmd.create()
        self.conn.send(cmd.get()) # Errors handled in _handle_error()
        
        buf = self.conn.recv()[0]
        if self.is_ok(buf):
            # Query does not return a result (INSERT/DELETE/..)
            return protocol.OKResultPacket(buf)

        try:
            p = protocol.Packet(buf)
            (nrflds, fields, eof) = self._handle_resultset(p)
        except:
            raise
        else:
            return (nrflds, fields)
    
        return (0, ())
    
    def _cmd_simple(self, servercmd, arg=''):
        """Makes a simple CommandPacket with no arguments"""
        cmd = protocol.CommandPacket()
        cmd.set_command(servercmd)
        cmd.set_argument(arg)
        cmd.create()

        return cmd
    
    def cmd_refresh(self, opts):
        """Send the Refresh command to the MySQL server.
        
        The argument should be a bitwise value using the protocol.RefreshOption
        constants.
        
        Usage:
        
         RefreshOption = mysql.connector.RefreshOption
         refresh = RefreshOption.LOG | RefreshOption.THREADS
         db.cmd_refresh(refresh)
         
        """
        cmd = self._cmd_simple(ServerCmd.REFRESH, opts)
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise
        
        if self.is_ok(buf):
            return True

        return False
    
    def cmd_quit(self):
        """Closes the current connection with the server."""
        cmd = self._cmd_simple(ServerCmd.QUIT)
        self.conn.send(cmd.get())
               
    def cmd_init_db(self, database):
        """
        Send command to server to change databases.
        """
        cmd = self._cmd_simple(ServerCmd.INIT_DB, database)
        self.conn.send(cmd.get())
        self.conn.recv()[0]
        
    def cmd_shutdown(self):
        """Shuts down the MySQL Server.
        
        Careful with this command if you have SUPER privileges! (Which your
        scripts probably don't need!)
        
        Returns True if it succeeds.
        """
        cmd = self._cmd_simple(ServerCmd.SHUTDOWN)
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise

        return True
    
    def cmd_statistics(self):
        """Sends statistics command to the MySQL Server
        
        Returns a dictionary with various statistical information.
        """
        cmd = self._cmd_simple(ServerCmd.STATISTICS)
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise
        
        p = Packet(buf)
        info = str(p.buffer)
        
        res = {}
        pairs = info.split('\x20\x20') # Information is separated by 2 spaces
        for pair in pairs:
            (lbl,val) = [ v.strip() for v in pair.split(':') ]
            # It's either an integer or a decimal
            try:
                res[lbl] = long(val)
            except:
                try:
                    res[lbl] = Decimal(val)
                except:
                    raise ValueError, "Got wrong value in COM_STATISTICS information (%s : %s)." % (lbl, val)
        return res

    def cmd_process_info(self):
        """Gets the process list from the MySQL Server.
        
        Returns a list of dictionaries which corresponds to the output of
        SHOW PROCESSLIST of MySQL. The data is converted to Python types.
        """
        cmd = self._cmd_simple(ServerCmd.PROCESS_INFO)
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise
        
        conv = MySQLConverter(use_unicode=True)
        p = Packet(buf)
        (nrflds, flds, eof) = self._handle_resultset(p)
        (rows, eof) = self.result_get_rows()
        res = []
        for row in rows:
            d = {}
            for f,v in zip(flds,row.values):
                d[f.name] = conv.to_python(f.get_description(),v)
            res.append(d)
        return res
    
    def cmd_process_kill(self, mypid):
        """Kills a MySQL process using it's ID.
        
        The mypid must be an integer.
        
        """
        cmd = KillPacket(mypid)
        cmd.create()
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise
        
        if self.is_eof(buf):
            return True

        return False
    
    def cmd_debug(self):
        """Send DEBUG command to the MySQL Server
        
        Needs SUPER privileges. The output will go to the MySQL server error log.
        
        Returns True when it was succesful.
        """
        cmd = self._cmd_simple(ServerCmd.DEBUG)
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise
        
        if self.is_eof(buf):
            return True
        
        return False
        
    def cmd_ping(self):
        """
        Ping the MySQL server to check if the connection is still alive.

        Returns True when alive, False when server doesn't respond.
        """
        cmd = self._cmd_simple(ServerCmd.PING)
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            return False
        else:
            if self.is_ok(buf):
                return True

        return False

    def cmd_change_user(self, username, password, database=None):
        """Change the user with given username and password to another optional database.
        """
        if not database:
            database = self.database
        
        cmd = ChangeUserPacket()
        cmd.create(username=username, password=password, database=database,
            charset=self.charset, seed=self.handshake.data['seed'])
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise
        
        if not self.is_ok(buf):
            raise errors.DatabaseError, \
                "Failed getting OK Packet after changing user to '%s'" % username
        
        return True

class MySQLProtocol41(MySQLBaseProtocol):
    
    def __init__(self, conn, handshake=None):
        MySQLBaseProtocol.__init__(self, conn, handshake=handshake)
        
class Packet(object):
    """
    Each packet type used in the MySQL Client Protocol is build on the Packet
    class. It defines lots of useful functions for parsing and sending
    data to and from the MySQL Server.
    """
    
    def __init__(self, buf=None, pktnr=0):
        self.buffer = ''
        self.length = 0
        self.pktnr = pktnr
        self.protocol = 10
        
        if buf:
            self.set(buf)
        
        if self.buffer:
            self._parse()

    def _make_header(self):
        h = int3store(self.get_length()) + int1store(self.pktnr)
        return h
    
    def _parse(self):
        pass

    def add(self, s):
        if not s:
            self.add_null()
        else:
            self.buffer = self.buffer + s
            self.length = self.get_length()
    
    def add_1_int(self, i):
        self.add(int1store(i))
    
    def add_2_int(self, i):
        self.add(int2store(i))
    
    def add_3_int(self, i):
        self.add(int3store(i))
    
    def add_4_int(self, i):
        self.add(int4store(i))
        
    def add_null(self, nr=1):
        self.add('\x00'*nr)

    def get(self):
        return self._make_header() + self.buffer
    
    def get_header(self):
        return self._make_header()
    
    def get_length(self):
        return len(self.buffer)

    def set(self, buf):
        if not self.is_valid(buf):
            raise InterfaceError('Packet not valid.')

        self.buffer = buf[4:]
        self.length = self.get_length()
    
    def _is_valid_extra(self, buf=None):
        return None
        
    def is_valid(self, buf=None):
        if not buf:
            buf = self.buffer

        (l, n) = (buf[0:3], buf[3])
        hlength = int3read(l)
        rlength = len(buf) - 4

        if hlength != rlength:
            return False
    
        res = self._is_valid_extra(buf)
        if res != None:
            return res

        return True

class Handshake(Packet):
    
    def __init__(self, buf=None):
        Packet.__init__(self, buf)

    def _parse(self):
        version = ''
        options = 0
        srvstatus = 0

        buf = self.buffer
        (buf,self.protocol) = read_int(buf,1)
        (buf,version) = read_string(buf,end='\x00')
        (buf,thrdid) = read_int(buf,4)
        (buf,scramble) = read_bytes(buf, 8)
        buf = buf[1:] # Filler 1 * \x00
        (buf,srvcap) = read_int(buf,2)
        (buf,charset) = read_int(buf,1)
        (buf,serverstatus) = read_int(buf,2)
        buf = buf[13:] # Filler 13 * \x00
        (buf,scramble_next) = read_bytes(buf,12)
        scramble += scramble_next

        self.data = {
            'version' : version,
            'thrdid' : thrdid,
            'seed' : scramble,
            'capabilities' : srvcap,
            'charset' : charset,
            'serverstatus' : serverstatus,
        }

    def get_dict(self):
        self._parse()
        return self.data
    
    def _is_valid_extra(self, buf):
        
        if buf[3] != '\x00':
            return False
        
        return True

class Auth(Packet):

    def __init__(self, packet=None, client_flags=0, pktnr=0):
        Packet.__init__(self, packet, pktnr)
        self.client_flags = 0
        self.username = None
        self.password = None
        self.database = None
        if client_flags:
            self.set_client_flags(client_flags)
        
    def set_client_flags(self, flags):
        self.client_flags = flags
    
    def set_login(self, username, password, database=None):
        self.username = username
        self.password = password
        self.database = database
        
    def scramble(self, passwd, seed):
        
        if not passwd:
            raise AuthError('Failed scrambling password (none given).')
        
        hash1 = sha1(passwd).digest()
        hash2 = sha1(hash1).digest() # Password as found in mysql.user()
        hash3 = sha1(seed + hash2).digest()
        xored = [ int1read(h1) ^ int1read(h3) for (h1,h3) in zip(hash1, hash3) ]
        hash4 = struct.pack('20B', *xored)
        
        return hash4
        
    def create(self, username=None, password=None, database=None, seed=None):
        self.add_4_int(self.client_flags)
        self.add_4_int(10 * 1024 * 1024)
        self.add_1_int(8)
        self.add_null(23)
        self.add(username + '\x00')
        if password:
            self.add_1_int(20)
            self.add(self.scramble(password,seed))
        else:
            self.add_null(1)
        
        if database:
            self.add(database + '\x00')
        else:
            self.add_null()


class ChangeUserPacket(Auth):
    def __init__(self):
        self.command = ServerCmd.CHANGE_USER
        Auth.__init__(self)

    def create(self, username=None, password=None, database=None, charset=8, seed=None):
        self.add_1_int(self.command)
        self.add(username + '\x00')
        if password:
            self.add_1_int(20)
            self.add(self.scramble(password,seed))
        else:
            self.add_null(1)
        if database:
            self.add(database + '\x00')
        else:
            self.add_null()

        self.add_2_int(charset)

class ErrorResultPacket(Packet):
    
    def __init__(self, buf=None):
        self.errno = 0
        self.errmsg = ''
        self.sqlstate = None
        Packet.__init__(self, buf)
        
    def _parse(self):
        buf = self.buffer
        
        if buf[0] != '\xff':
            raise InterfaceError('Expected an Error Packet.')
        buf = buf[1:]
        
        (buf,self.errno) = read_int(buf, 2)
        
        if buf[0] != '\x23':
            # Error without SQLState
            self.errmsg = buf
        else:
            (buf,self.sqlstate) = read_bytes(buf[1:],5)
            self.errmsg = buf
        
class OKResultPacket(Packet):
    def __init__(self, buf=None):
        self.affected_rows = None
        self.insert_id = None
        self.server_status = 0
        self.warning_count = 0
        self.field_count = 0
        self.info_msg = ''
        Packet.__init__(self, buf)
    
    def __str__(self):
        if self.affected_rows == 1:
            lbl_rows = 'row'
        else:
            lbl_rows = 'rows'
        
        xtr = []
        if self.insert_id:
            xtr.append('last insert: %d ' % self.insert_id)
        if self.warning_count:
            xtr.append('warnings: %d' % self.warning_count)
            
        return "Query OK, %d %s affected %s( sec)" % (self.affected_rows, lbl_rows, ', '.join(xtr))

    def _parse(self):
        buf = self.buffer
        (buf,self.field_count)      = read_int(buf,1)
        (buf,self.affected_rows)    = read_lc_int(buf)
        (buf,self.insert_id)        = read_lc_int(buf)
        (buf,self.server_status)    = read_int(buf,2)
        (buf,self.warning_count)    = read_int(buf,2)
        if buf:
            (buf,self.info_msg)     = read_lc_string(buf)

class CommandPacket(Packet):
    def __init__(self, cmd=None, arg=None):
        self.command = cmd
        self.argument = arg
        Packet.__init__(self)
    
    def create(self):
        self.add_1_int(self.command)
        self.add(str(self.argument))
            
    def set_command(self, cmd):
        self.command = cmd
    
    def set_argument(self, arg):
        self.argument = arg

class KillPacket(CommandPacket):
    
    def __init__(self, arg):
        CommandPacket.__init__(self)
        self.set_command(ServerCmd.PROCESS_KILL)
        self.set_argument(arg)
    
    def create(self):
        """"""
        self.add_1_int(self.command)
        self.add_4_int(self.argument)
    
    def set_argument(self, arg):
        if arg and not isinstance(int, long) and arg > 2**32:
            raise ValueError, "KillPacket needs integer value as argument not larger than 2^32."
        self.argument = arg

class FieldPacket(Packet):
    def __init__(self, buf=None):
        self.catalog = None
        self.db = None
        self.table = None
        self.org_table = None
        self.name = None
        self.org_name = None
        self.charset = None
        self.length = None
        self.type = None
        self.flags = None
        Packet.__init__(self, buf)
    
    def __str__(self):
        flags = []
        for k,f in FieldFlag.desc.items():
            if int(self.flags) & f[0]:
                flags.append(k)
        return """
            Field: catalog: %s ; db:%s ; table:%s ; org_table: %s ;
                   name: %s ; org_name: %s ;
                   charset: %s ; lenght: %s ;
                   type: %02x ;
                   flags(%d): %s;
            """ % (self.catalog,self.db,self.table,self.org_table,self.name,self.org_name,
                self.charset, self.length, self.type,
                self.flags, '|'.join(flags))

    def _parse(self):
        buf = self.buffer
        
        (buf,self.catalog)   = read_lc_string(buf)
        (buf,self.db)        = read_lc_string(buf)
        (buf,self.table)     = read_lc_string(buf)
        (buf,self.org_table) = read_lc_string(buf)
        (buf,self.name)      = read_lc_string(buf)
        (buf,self.org_name)  = read_lc_string(buf)
        buf = buf[1:] # filler 1 * \x00
        (buf,self.charset)   = read_int(buf, 2)
        (buf,self.length)    = read_int(buf, 4)
        (buf,self.type)      = read_int(buf, 1)
        (buf,self.flags)     = read_int(buf, 2)
        (buf,self.decimal)   = read_int(buf, 1)
        buf = buf[2:] # filler 2 * \x00

    def get_description(self):
        """Returns a description as a list useful for cursors.
        
        This function returns a list as defined in the Python Db API v2.0
        specification.
        
        """
        return (
            self.name,
            self.type,
            None, # display_size
            None, # internal_size
            None, # precision
            None, # scale
            ~self.flags & FieldFlag.NOT_NULL, # null_ok
            self.flags, # MySQL specific
        )
class EOFPacket(Packet):
    def __init__(self, buf=None):
        self.warning_count = None
        self.status_flag = None
        Packet.__init__(self, buf)
    
    def __str__(self):
        return "EOFPacket: warnings %d / status: %d" % (self.warning_count,self.status_flag)
    
    def _is_valid_extra(self, buf=None):
        if not buf:
            buf = self.buffer
        else:
            buf = buf[4:]
        if buf[0] == '\xfe' and len(buf) == 5:
            # An EOF should always start with \xfe and smaller than 9 bytes
            return True
        return False
    
    def _parse(self):
        buf = self.buffer
        
        buf = buf[1:] # disregard the first checking byte
        (buf, self.warning_count) = read_int(buf, 2)
        (buf, self.status_flag) = read_int(buf, 2)

class RowDataPacket(Packet):
    """
    """
    def __init__(self, buf=None):
        self.values = []
        Packet.__init__(self, buf)
        
    def _parse(self):
        buf = self.buffer
        
        while buf:
            if buf[0] == '\xfb':
                # Field contains a NULL
                v = None
                buf = buf[1:]
            else:
                # Read field
                (buf, v) = read_lc_string(buf)
            self.values.append(v)

