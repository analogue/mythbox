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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USAs

"""Implementing the MySQL Client/Server protocol
"""

import string
import socket
import re
import struct

try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1

from datetime import datetime
from time import strptime
from decimal import Decimal

from constants import *
import errors
import utils

class MySQLProtocol(object):
    """Class handling the MySQL Protocol.
    
    MySQL v4.1 Client/Server Protocol is currently supported.
    """
    def __init__(self, conn, handshake=None):
        self.client_flags = 0
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
            client_flags = ClientFlag.get_default()
        
        auth = Auth(client_flags=client_flags,
            pktnr=self.handshake.pktnr+1)
        auth.create(username=username, password=password,
            seed=self.handshake.info['seed'], database=database)

        self.conn.send(auth.get())
        buf = self.conn.recv()[0]
        if self.is_eof(buf):
            raise errors.InterfaceError("Found EOF after Auth, expecting OK. Using old passwords?")
        
        connect_with_db = client_flags & ClientFlag.CONNECT_WITH_DB
        if self.is_ok(buf) and database and not connect_with_db:
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
            handshake = Handshake(buf)
        except errors.InterfaceError, msg:
            raise errors.InterfaceError(msg)
        self.set_handshake(handshake)
    
    def set_handshake(self, handshake):
        """Gather data from the given handshake."""
        ver = re.compile("^(\d{1,2})\.(\d{1,2})\.(\d{1,3})(.*)")
        version = handshake.info['version']
        m = ver.match(version)
        if not m:
            raise errors.InterfaceError("Could not parse MySQL version, was '%s'" % version)
        else:
            self.server_version = tuple([ int(v) for v in m.groups()[0:3]])

        self.server_version_original = handshake.info['version']
        self.server_threadid = handshake.info['thrdid']
        self.capabilities = handshake.info['capabilities']
        self.charset = handshake.info['charset']
        self.threadid = handshake.info['thrdid']
        self.handshake = handshake

    def _handle_error(self, buf):
        """Raise an OperationalError if result is an error
        """
        try:
            err = ErrorResultPacket(buf)
        except errors.InterfaceError, e:
            raise e
        else:
            raise errors.OperationalError(err)
    
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
            ok = OKResultPacket(buf)
        except errors.InterfaceError, e:
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
            fld = FieldPacket(buf)
            fields.append(fld)
            i += 1
        return fields
    
    def is_eof(self, buf):
        """
        Check if the given buffer is a MySQL EOF Packet. It should
        start with \xfe and be smaller 9 bytes.

        Returns boolean.
        """
        l = utils.read_int(buf, 3)[1]
        if buf and buf[4] == '\xfe' and l < 9:
            return True
        return False

    def _handle_resultset(self, pkt):
        """Processes a resultset getting fields information.
        
        The argument pkt must be a protocol.Packet with length 1, a byte
        which contains the number of fields.
        """
        if not isinstance(pkt, PacketIn):
            raise ValueError("%s is not a protocol.PacketIn" % pkt)
        
        if len(pkt) == 1:
            (buf,nrflds) = utils.read_lc_int(pkt.data)
            
            # Get the fields
            fields = self._handle_fields(nrflds)

            buf = self.conn.recv()[0]
            eof = EOFPacket(buf)

            return (nrflds, fields, eof)
        else:
            raise errors.InterfaceError('Something wrong reading result after query.')

    def result_get_row(self):
        """Get data for 1 row
        
        Get one row's data. Should be called after getting the field
        descriptions.

        Returns a tuple with 2 elements: a row's data and the
        EOF packet.
        """
        buf = self.conn.recv()[0]
        if self.is_eof(buf):
            eof = EOFPacket(buf)
            rowdata = None
        else:
            eof = None
            rowdata = utils.read_lc_string_list(buf[4:])
        return (rowdata, eof)
    
    def result_get_rows(self, cnt=None):
        """Get all rows
        
        Returns a tuple with 2 elements: a list with all rows and
        the EOF packet.
        """
        rows = []
        eof = None
        rowdata = None
        while eof is None:
            (rowdata,eof) = self.result_get_row()
            if eof is None and rowdata is not None:
                rows.append(rowdata)
        return (rows,eof)

    def cmd_query(self, query):
        """
        Sends a query to the server.
        
        Returns a tuple, when the query returns a result. The tuple
        consist number of fields and a list containing their descriptions.
        If the query doesn't return a result set, the an OKResultPacket
        will be returned.
        """
        try:
            cmd = CommandPacket()
            cmd.set_command(ServerCmd.QUERY)
            cmd.set_argument(query)
            cmd.create()
            self.conn.send(cmd.get()) # Errors handled in _handle_error()
        
            buf = self.conn.recv()[0]
            if self.is_ok(buf):
                # Query does not return a result (INSERT/DELETE/..)
                return OKResultPacket(buf)

            p = PacketIn(buf)
            (nrflds, fields, eof) = self._handle_resultset(p)
        except:
            raise
        else:
            return (nrflds, fields)
    
        return (0, ())
    
    def _cmd_simple(self, servercmd, arg=''):
        """Makes a simple CommandPacket with no arguments"""
        cmd = CommandPacket()
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
        info = str(p.data)
        
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
                    raise ValueError(
                        "Got wrong value in COM_STATISTICS information (%s : %s)." % (lbl, val))
        return res

    def cmd_process_info(self):
        """Gets the process list from the MySQL Server.
        
        Returns a list of dictionaries which corresponds to the output of
        SHOW PROCESSLIST of MySQL. The data is converted to Python types.
        """
        raise errors.NotSupportedError(
            "Not implemented. Use a cursor to get processlist information.")
    
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
            charset=self.charset, seed=self.handshake.info['seed'])
        try:
            self.conn.send(cmd.get())
            buf = self.conn.recv()[0]
        except:
            raise
        
        if not self.is_ok(buf):
            raise errors.OperationalError(
                "Failed getting OK Packet after changing user")
        
        return True

class BasePacket(object):
    
    def __len__(self):
        try:
            return len(self.data)
        except:
            return 0
    
    def is_valid(self, buf=None):
        if buf is None:
            buf = self.data

        (l, n) = (buf[0:3], buf[3])
        hlength = utils.int3read(l)
        rlength = len(buf) - 4

        if hlength != rlength:
            return False

        res = self._is_valid_extra(buf)
        if res != None:
            return res

        return True
    
    def _is_valid_extra(self, buf):
        return True

class PacketIn(BasePacket):
    def __init__(self, buf=None, pktnr=0):
        self.data = ''
        self.pktnr = pktnr
        self.protocol = 10
        
        if buf:
            self.is_valid(buf)
            self.data = buf[4:]
        
        if self.data:
            self._parse()
    
    def _parse(self):
        pass
            
class PacketOut(BasePacket):
    """
    Each packet type used in the MySQL Client Protocol is build on the Packet
    class. It defines lots of useful functions for parsing and sending
    data to and from the MySQL Server.
    """
    
    def __init__(self, buf=None, pktnr=0):
        self.data = ''
        self.pktnr = pktnr
        self.protocol = 10
        
        if buf:
            self.set(buf)
        
        if self.data:
            self._parse()

    def _make_header(self):
        h = utils.int3store(len(self)) + utils.int1store(self.pktnr)
        return h
    
    def _parse(self):
        pass

    def add(self, s):
        if not s:
            self.add_null()
        else:
            self.data = self.data + s
    
    def add_1_int(self, i):
        self.add(utils.int1store(i))
    
    def add_2_int(self, i):
        self.add(utils.int2store(i))
    
    def add_3_int(self, i):
        self.add(utils.int3store(i))
    
    def add_4_int(self, i):
        self.add(utils.int4store(i))
        
    def add_null(self, nr=1):
        self.add('\x00'*nr)

    def get(self):
        return self._make_header() + self.data
    
    def get_header(self):
        return self._make_header()

    def set(self, buf):
        if not self.is_valid(buf):
            raise errors.InterfaceError('Packet not valid.')

        self.data = buf[4:]
        
    def _is_valid_extra(self, buf=None):
        return None

class Handshake(PacketIn):
    
    def __init__(self, buf=None):
        PacketIn.__init__(self, buf)

    def _parse(self):
        version = ''
        options = 0
        srvstatus = 0

        buf = self.data
        (buf,self.protocol) = utils.read_int(buf,1)
        (buf,version) = utils.read_string(buf,end='\x00')
        (buf,thrdid) = utils.read_int(buf,4)
        (buf,scramble) = utils.read_bytes(buf, 8)
        buf = buf[1:] # Filler 1 * \x00
        (buf,srvcap) = utils.read_int(buf,2)
        (buf,charset) = utils.read_int(buf,1)
        (buf,serverstatus) = utils.read_int(buf,2)
        buf = buf[13:] # Filler 13 * \x00
        (buf,scramble_next) = utils.read_bytes(buf,12)
        scramble += scramble_next

        self.info = {
            'version' : version,
            'thrdid' : thrdid,
            'seed' : scramble,
            'capabilities' : srvcap,
            'charset' : charset,
            'serverstatus' : serverstatus,
        }

    def get_dict(self):
        self._parse()
        return self.info
    
    def _is_valid_extra(self, buf):
        
        if buf[3] != '\x00':
            return False
        
        return True

class Auth(PacketOut):

    def __init__(self, packet=None, client_flags=0, pktnr=0):
        PacketOut.__init__(self, packet, pktnr)
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
        
        hash4 = None
        try: 
            hash1 = sha1(passwd).digest()
            hash2 = sha1(hash1).digest() # Password as found in mysql.user()
            hash3 = sha1(seed + hash2).digest()
            xored = [ utils.int1read(h1) ^ utils.int1read(h3) 
                for (h1,h3) in zip(hash1, hash3) ]
            hash4 = struct.pack('20B', *xored)
        except StandardError, e:
            raise errors.ProgrammingError('Failed scrambling password; %s' % e)
        else:
            return hash4
        return None
        
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

class ErrorResultPacket(PacketIn):
    
    def __init__(self, buf=None):
        self.errno = 0
        self.errmsg = ''
        self.sqlstate = None
        PacketIn.__init__(self, buf)
        
    def _parse(self):
        buf = self.data
        
        if buf[0] != '\xff':
            raise errors.InterfaceError('Expected an Error Packet.')
        buf = buf[1:]
        
        (buf,self.errno) = utils.read_int(buf, 2)
        
        if buf[0] != '\x23':
            # Error without SQLState
            self.errmsg = buf
        else:
            (buf,self.sqlstate) = utils.read_bytes(buf[1:],5)
            self.errmsg = buf
        
class OKResultPacket(PacketIn):
    def __init__(self, buf=None):
        self.affected_rows = None
        self.insert_id = None
        self.server_status = 0
        self.warning_count = 0
        self.field_count = 0
        self.info_msg = ''
        PacketIn.__init__(self, buf)
    
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
            
        return "Query OK, %d %s affected %s( sec)" % (self.affected_rows,
            lbl_rows, ', '.join(xtr))

    def _parse(self):
        buf = self.data
        (buf,self.field_count) = utils.read_int(buf,1)
        (buf,self.affected_rows) = utils.read_lc_int(buf)
        (buf,self.insert_id) = utils.read_lc_int(buf)
        (buf,self.server_status) = utils.read_int(buf,2)
        (buf,self.warning_count) = utils.read_int(buf,2)
        if buf:
            (buf,self.info_msg) = utils.read_lc_string(buf)

class CommandPacket(PacketOut):
    def __init__(self, cmd=None, arg=None):
        self.command = cmd
        self.argument = arg
        PacketOut.__init__(self)
    
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

class FieldPacket(PacketIn):
    def __init__(self, buf=None):
        self.catalog = None
        self.db = None
        self.table = None
        self.org_table = None
        self.name = None
        self.length = None
        self.org_name = None
        self.charset = None
        self.type = None
        self.flags = None
        PacketIn.__init__(self, buf)
    
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
                self.charset, len(self), self.type,
                self.flags, '|'.join(flags))

    def _parse(self):
        buf = self.data
        
        (buf,self.catalog) = utils.read_lc_string(buf)
        (buf,self.db) = utils.read_lc_string(buf)
        (buf,self.table) = utils.read_lc_string(buf)
        (buf,self.org_table) = utils.read_lc_string(buf)
        (buf,self.name) = utils.read_lc_string(buf)
        (buf,self.org_name) = utils.read_lc_string(buf)
        buf = buf[1:] # filler 1 * \x00
        (buf,self.charset) = utils.read_int(buf, 2)
        (buf,self.length) = utils.read_int(buf, 4)
        (buf,self.type) = utils.read_int(buf, 1)
        (buf,self.flags) = utils.read_int(buf, 2)
        (buf,self.decimal) = utils.read_int(buf, 1)
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
        
class EOFPacket(PacketIn):
    def __init__(self, buf=None):
        self.warning_count = None
        self.status_flag = None
        PacketIn.__init__(self, buf)
    
    def __str__(self):
        return "EOFPacket: warnings %d / status: %d" % (self.warning_count,self.status_flag)
    
    def _is_valid_extra(self, buf=None):
        if not buf:
            buf = self.data
        else:
            buf = buf[4:]
        if buf[0] == '\xfe' and len(buf) == 5:
            # An EOF should always start with \xfe and smaller than 9 bytes
            return True
        return False
    
    def _parse(self):
        buf = self.data
        
        buf = buf[1:] # disregard the first checking byte
        (buf, self.warning_count) = utils.read_int(buf, 2)
        (buf, self.status_flag) = utils.read_int(buf, 2)
