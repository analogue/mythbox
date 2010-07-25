# MySQL Connector/Python - MySQL driver written in Python.
# Copyright (c) 2009,2010, Oracle and/or its affiliates. All rights reserved.
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

"""Unittests for mysql.connector.protocol
"""

import datetime
import decimal
from collections import deque

import tests
from mysql.connector import mysql, connection, cursor, conversion, protocol, utils, errors, constants

class Decorators(tests.MySQLConnectorTests):
    
    def test_packet_is_error(self):
        """Decorator raises when buffer is an Error packet"""
        errpkt = \
            b'\x47\x00\x00\x02\xff\x15\x04\x23\x32\x38\x30\x30\x30'\
            b'\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69\x65\x64'\
            b'\x20\x66\x6f\x72\x20\x75\x73\x65\x72\x20\x27\x68\x61'\
            b'\x6d\x27\x40\x27\x6c\x6f\x63\x61\x6c\x68\x6f\x73\x74'\
            b'\x27\x20\x28\x75\x73\x69\x6e\x67\x20\x70\x61\x73\x73'\
            b'\x77\x6f\x72\x64\x3a\x20\x59\x45\x53\x29'

        @protocol.packet_is_error(0)
        def check(buf):
            self.fail("Decorator did not raise error")
        self.assertRaises(errors.OperationalError,check,errpkt)
        
        @protocol.packet_is_error(99)
        def check(buf):
            self.fail("Decorator did not raise error")
        self.assertRaises(errors.InterfaceError,check,errpkt)
        
        noterr = b'\x05\x00\x00\x00\xfe\x01'
        self.assertRaises(errors.InterfaceError,check,noterr)
    
    def test_packet_is_ok(self):
        """Decorator raises when buffer is not OK packet"""
        
        okpkt = b'\x01\x00\x00\x01\x00'
        
        @protocol.packet_is_ok(0)
        def check(buf):
            return True
        self.assertEqual(True,check(okpkt))
        
        @protocol.packet_is_ok(99)
        def check(buf):
            return True
        self.assertRaises(errors.InterfaceError,check,okpkt)
        
        notok = b'\x01\x00\x00\x00\xff'
        self.assertRaises(errors.InterfaceError,check,notok)
    
    def test_packet_is_eof(self):
        """Decorator raises when buffer is not EOF packet"""
        
        eofpkt = b'\x01\x00\x00\x00\xfe\x00\x00\x00\x00'
        
        @protocol.packet_is_eof(0)
        def check(buf):
            return True
        self.assertEqual(True,check(eofpkt))
        
        @protocol.packet_is_eof(99)
        def check(buf):
            return True
        self.assertRaises(errors.InterfaceError,check,eofpkt)
        
        noteof = b'\x01\x00\x00\x00\xff'
        self.assertRaises(errors.InterfaceError,check,noteof)
    
    def test_set_pktnr(self):
        """Decorator sets the pktnr-member from given packet"""
        
        pkt = b'\x01\x00\x00\x01\x00'
        
        class Check(object):
            
            @protocol.set_pktnr(1)
            def check(self, buf):
                pass
            
            @protocol.set_pktnr(2)
            def check_broken(self, buf):
                pass
            
            @protocol.set_pktnr(1)
            def check_broken2(self, buf):
                pass
        
        c = Check()
        c.check(pkt)
        self.assertEqual(1,c.pktnr)
        self.assertRaises(errors.InterfaceError,c.check_broken,pkt)
        
        pkt = b'\x01\x00\x00'
        self.assertRaises(errors.InterfaceError,c.check_broken2,pkt)
    
    def test_reset_pktnr(self):
        """Decorator resetting pktnr-member to -1"""
        
        class Check(object):
            
            @protocol.reset_pktnr
            def check(self):
                pass
        
        c = Check()
        c.pktnr = 2
        c.check()
        self.assertEqual(-1,c.pktnr)

class MySQLProtocol(tests.MySQLConnectorTests):
    
    def setUp(self):
        
        class Cnx(object):
            def queue_buffer(self, pkts):
                for p in pkts:
                    self.buf.append(p)
            
            def __init__(self):
                self.buf = deque()
                
            def recv(self):
                try:
                    return self.buf.popleft()
                except:
                    raise errors.InterfaceError('Failed recv')
                
            def send(self, buf):
                pass
            
            def open_connection(self):
                pass
        
        self.cnx = Cnx()
        self.prtcl = protocol.MySQLProtocol(self.cnx)
    
    def test_MySQLProtocol_raise_error(self):
        """Raise an errors.Error when buffer has a MySQL error
        """
        errpkt = \
            b'\x47\x00\x00\x02\xff\x15\x04\x23\x32\x38\x30\x30\x30'\
            b'\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69\x65\x64'\
            b'\x20\x66\x6f\x72\x20\x75\x73\x65\x72\x20\x27\x68\x61'\
            b'\x6d\x27\x40\x27\x6c\x6f\x63\x61\x6c\x68\x6f\x73\x74'\
            b'\x27\x20\x28\x75\x73\x69\x6e\x67\x20\x70\x61\x73\x73'\
            b'\x77\x6f\x72\x64\x3a\x20\x59\x45\x53\x29'

        self.assertRaises(errors.OperationalError,
            protocol.MySQLProtocol.raise_error,errpkt)
        
        try:
            protocol.MySQLProtocol.raise_error(errpkt)
        except errors.Error as e:
            self.assertEqual(1045,e.errno)
    
    def test___init__(self):
        """Initializing a MySQLProtocol instance"""
        self.assertEqual(0,self.prtcl.client_flags)
        self.assertEqual(self.cnx,self.prtcl.conn)
        self.assertEqual(-1,self.prtcl.pktnr)
    
    def test__recv_packet(self):
        """Getting a packet from socket connection"""
        self.cnx.buf.append(b'\x47\x00\x00\x02\xff')
        self.assertRaises(errors.Error,self.prtcl._recv_packet)
        
        exp = b'\x01\x00\x00\x01\x00'
        self.cnx.buf.append(exp)
        self.assertEqual(exp,self.prtcl._recv_packet())
    
    def test__scramble_password(self):
        """Scramble a password ready to send to MySQL"""
        password = "spam".encode('utf-8')
        seed =  b'\x3b\x55\x78\x7d\x2c\x5f\x7c\x72\x49\x52'\
                b'\x3f\x28\x47\x6f\x77\x28\x5f\x28\x46\x69'
        hashed = b'\x3a\x07\x66\xba\xba\x01\xce\xbe\x55\xe6'\
                 b'\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91\x5b'
        
        self.assertEqual(hashed,self.prtcl._scramble_password(password,seed))
    
    def test__pkt_make_header(self):
        """Make a MySQL packet header"""
        pkt = b'\x02\x00\x00\x01\x00\x01'
        self.assertEqual(pkt[0:4],
            self.prtcl._pkt_make_header(len(pkt[4:]),1))
        
        pkt = b'\x02\x00\x00\x02\x00\x01'
        self.prtcl.pktnr = 1
        self.assertEqual(pkt[0:4],self.prtcl._pkt_make_header(len(pkt[4:])))
    
    def test__pkt_make_auth(self):
        """Make a MySQL authentication packet"""
        seed =  b'\x3b\x55\x78\x7d\x2c\x5f\x7c\x72\x49\x52'\
                b'\x3f\x28\x47\x6f\x77\x28\x5f\x28\x46\x69'
        exp = {
            'allset':\
            b'\x3e\x00\x00\x00\x0d\xa2\x03\x00\x00\x00\xa0\x00'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x68\x61\x6d\x00\x14\x3a\x07\x66\xba\xba\x01\xce'\
            b'\xbe\x55\xe6\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91'\
            b'\x5b\x74\x65\x73\x74\x00',
            'nopass':\
            b'\x2a\x00\x00\x00\x0d\xa2\x03\x00\x00\x00\xa0\x00'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x68\x61\x6d\x00\x00\x74\x65\x73\x74\x00',
            'nouser':\
            b'\x3b\x00\x00\x00\x0d\xa2\x03\x00\x00\x00\xa0\x00'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x14\x3a\x07\x66\xba\xba\x01\xce'\
            b'\xbe\x55\xe6\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91'\
            b'\x5b\x74\x65\x73\x74\x00',
            'nodb':\
            b'\x3a\x00\x00\x00\x0d\xa2\x03\x00\x00\x00\xa0\x00'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x68\x61\x6d\x00\x14\x3a\x07\x66\xba\xba\x01\xce'\
            b'\xbe\x55\xe6\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91'\
            b'\x5b\x00',
            }
        flags = constants.ClientFlag.get_default()
        kwargs = dict(username="ham",password="spam",
                database="test",seed=None, charset=33,
                client_flags=flags)
        self.assertRaises(errors.ProgrammingError,
            self.prtcl._pkt_make_auth,**kwargs)
            
        kwargs['seed'] = seed
        res = self.prtcl._pkt_make_auth(**kwargs)
        self.assertEqual(exp['allset'],res)
        
        kwargs['seed'] = None
        self.prtcl.scramble = seed
        res = self.prtcl._pkt_make_auth(**kwargs)
        self.assertEqual(exp['allset'],res)
        
        kwargs['password'] = None
        res = self.prtcl._pkt_make_auth(**kwargs)
        self.assertEqual(exp['nopass'],res)
        
        kwargs['password'] = 'spam'
        kwargs['database'] = None
        res = self.prtcl._pkt_make_auth(**kwargs)
        self.assertEqual(exp['nodb'],res)
        
        kwargs['username'] = None
        kwargs['database'] = 'test'
        res = self.prtcl._pkt_make_auth(**kwargs)
        self.assertEqual(exp['nouser'],res)
    
    def test__pkt_make_command(self):
        """Make a generic MySQL command packet"""
        exp = b'\x04\x00\x00\x00\x01\x68\x61\x6d'
        arg = 'ham'.encode('utf-8')
        res = self.prtcl._pkt_make_command(1,arg)
        self.assertEqual(exp, res)
        res = self.prtcl._pkt_make_command(1,arg)
        self.assertEqual(exp, res)
        
        exp = b'\x01\x00\x00\x00\x03'
        res = self.prtcl._pkt_make_command(3)
        self.assertEqual(exp, res)
    
    def test__pkt_make_changeuser(self):
        """Make a change user MySQL packet"""
        seed =  b'\x3b\x55\x78\x7d\x2c\x5f\x7c\x72\x49\x52'\
                b'\x3f\x28\x47\x6f\x77\x28\x5f\x28\x46\x69'
        
        exp = {
            'allset':\
            b'\x21\x00\x00\x00\x11\x68\x61\x6d\x00\x14\x3a\x07'\
            b'\x66\xba\xba\x01\xce\xbe\x55\xe6\x29\x88\xaa\xae'\
            b'\xdb\x00\xb3\x4d\x91\x5b\x74\x65\x73\x74\x00\x08'\
            b'\x00',
            'nopass':\
            b'\x0d\x00\x00\x00\x11\x68\x61\x6d\x00\x00\x74\x65'\
            b'\x73\x74\x00\x08\x00',
            }
        kwargs = dict(username='ham',
                password='spam', database='test',
                charset=8, seed=None)
        self.assertRaises(errors.ProgrammingError,
            self.prtcl._pkt_make_changeuser,**kwargs)
        self.prtcl.client_flags = constants.ClientFlag.get_default()    
        kwargs['seed'] = seed
        res = self.prtcl._pkt_make_changeuser(**kwargs)
        self.assertEqual(exp['allset'],res)
        
        kwargs['seed'] = None
        self.prtcl.scramble = seed
        res = self.prtcl._pkt_make_changeuser(**kwargs)
        self.assertEqual(exp['allset'],res)
        
        kwargs['password'] = None
        res = self.prtcl._pkt_make_changeuser(**kwargs)
        self.assertEqual(exp['nopass'],res)
    
    def test__pkt_parse_handshake(self):
        """Parse handshake-packet sent by MySQL"""
        handshake = \
            b'\x47\x00\x00\x00\x0a\x35\x2e\x30\x2e\x33\x30\x2d'\
            b'\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67'\
            b'\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68'\
            b'\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72'\
            b'\x59\x48\x00'
        exp = {
            'protocol': 10,
            'server_version_original': b'5.0.30-enterprise-gpl-log',
            'charset': 8,
            'server_threadid': 265,
            'capabilities': 41516,
            'server_status': 2,
            'scramble': b'h4i6oP!OLng9&PD@WrYH'
            }
        
        res = self.prtcl._pkt_parse_handshake(handshake)
        self.assertEqual(exp,res)
        
    def test__pkt_parse_ok(self):
        """Parse OK-packet sent by MySQL"""
        okpkt = b'\x07\x00\x00\x01\x00\x01\x00\x00\x00\x01\x00'
        exp = {
            'insert_id': 0,
            'affected_rows': 1,
            'field_count': 0,
            'warning_count': 1,
            'server_status': 0
            }
        res = self.prtcl._pkt_parse_ok(okpkt)
        self.assertEqual(exp,res)
        
        okpkt += b'\x04spam'
        exp['info_msg'] = b'spam'
        res = self.prtcl._pkt_parse_ok(okpkt)
        self.assertEqual(exp,res)
        
    def test__pkt_parse_field(self):
        """Parse field-packet sent by MySQL"""
        fldpkt = \
            b'\x1a\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x04'\
            b'\x53\x70\x61\x6d\x00\x0c\x21\x00\x09\x00\x00\x00'\
            b'\xfd\x01\x00\x1f\x00\x00'
        exp = (b'Spam', 253, None, None, None, None, 0, 1)
        res = self.prtcl._pkt_parse_field(fldpkt)
        self.assertEqual(exp,res)
        
    def test__pkt_parse_eof(self):
        """Parse EOF-packet sent by MySQL"""
        eofpkt = b'\x05\x00\x00\x05\xfe\x01\x00\x00\x00'
        exp = {'status_flag': 0, 'warning_count': 1}
        res = self.prtcl._pkt_parse_eof(eofpkt)
        self.assertEqual(exp,res)
    
    def test_do_handshake(self):
        """Get handshake sent by MySQL"""
        handshake = \
            b'\x47\x00\x00\x00\x0a\x35\x2e\x30\x2e\x33\x30\x2d'\
            b'\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67'\
            b'\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68'\
            b'\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72'\
            b'\x59\x48\x00'
        exp = {
            'protocol': 10,
            'server_version_original': '5.0.30-enterprise-gpl-log',
            'charset': 8,
            'server_threadid': 265,
            'capabilities': 41516,
            'server_status': 2,
            'scramble': b'h4i6oP!OLng9&PD@WrYH'
            }
        self.prtcl.conn.buf.append(handshake)
        self.prtcl.do_handshake()
        for k,v in exp.items():
            self.assertEqual(self.prtcl.__dict__[k],exp[k])
    
    def test_do_auth(self):
        """Authenticate with the MySQL server"""
        seed =  b'\x3b\x55\x78\x7d\x2c\x5f\x7c\x72\x49\x52'\
                b'\x3f\x28\x47\x6f\x77\x28\x5f\x28\x46\x69'
        okpkt = b'\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00'
        self.prtcl.scramble = seed
        flags = constants.ClientFlag.get_default()
        kwargs = dict(username='ham',password='spam',
            database='test',charset=33, client_flags=flags)
        
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00')
        res = self.prtcl.do_auth(**kwargs)
        self.assertEqual(True,res)
        
        self.prtcl.conn.buf.append(b'\x01\x00\x00\x02\xfe')
        self.assertRaises(errors.NotSupportedError,
            self.prtcl.do_auth,**kwargs)
        
        self.prtcl.conn.queue_buffer([
            b'\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00',
            b'\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00'])
        flags &= ~constants.ClientFlag.CONNECT_WITH_DB
        kwargs['client_flags'] = flags
        res = self.prtcl.do_auth(**kwargs)
        
        self.prtcl.conn.queue_buffer([
            b'\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00',
            b'\x24\x00\x00\x01\xff\x19\x04\x23\x34\x32\x30\x30'\
            b'\x30\x55\x6e\x6b\x6e\x6f\x77\x6e\x20\x64\x61\x74'\
            b'\x61\x62\x61\x73\x65\x20\x27\x61\x73\x64\x66\x61'\
            b'\x73\x64\x66\x27'])
        flags &= ~constants.ClientFlag.CONNECT_WITH_DB
        kwargs['client_flags'] = flags
        self.assertRaises(errors.ProgrammingError,self.prtcl.do_auth,**kwargs)
        
    def test_handle_handshake(self):
        """Handle the handshake-packet sent by MySQL"""
        handshake = \
            b'\x47\x00\x00\x00\x0a\x35\x2e\x30\x2e\x33\x30\x2d'\
            b'\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67'\
            b'\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68'\
            b'\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72'\
            b'\x59\x48\x00'
        exp = {
            'protocol': 10,
            'server_version_original': '5.0.30-enterprise-gpl-log',
            'charset': 8,
            'server_threadid': 265,
            'capabilities': 41516,
            'server_status': 2,
            'scramble': b'h4i6oP!OLng9&PD@WrYH'
            }
        
        self.prtcl.handle_handshake(handshake)
        for k,v in exp.items():
            self.assertEqual(self.prtcl.__dict__[k],exp[k])
    
        self.assertRaises(errors.InterfaceError,
            self.prtcl.handle_handshake,
            b'\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00')
        
    def test__handle_ok(self):
        """Handle an OK-packet sent by MySQL"""
        okpkt = b'\x07\x00\x00\x01\x00\x01\x00\x00\x00\x01\x00'
        exp = {
            'insert_id': 0,
            'affected_rows': 1,
            'field_count': 0,
            'warning_count': 1,
            'server_status': 0
            }
        
        self.assertEqual(exp,self.prtcl._handle_ok(okpkt))
        self.assertRaises(errors.InterfaceError,
            self.prtcl._handle_ok,b'\x01\x00\x00\x02\xfe')
    
    def test__handle_eof(self):
        """Handle an EOF-packet sent by MySQL"""
        eofpkt = b'\x05\x00\x00\x05\xfe\x01\x00\x00\x00'
        exp = {'status_flag': 0, 'warning_count': 1}
        
        self.assertEqual(exp,self.prtcl._handle_eof(eofpkt))
        
        okpkt = b'\x07\x00\x00\x01\x00\x01\x00\x00\x00\x01\x00'
        self.assertRaises(errors.InterfaceError,
            self.prtcl._handle_eof,okpkt)
    
    def test__handle_resultset(self):
        """Handle a resultset sent by MySQL"""
        def fillbuffer():
            self.prtcl.conn.queue_buffer([
                b'\x17\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x01'\
                b'\x31\x00\x0c\x3f\x00\x01\x00\x00\x00\x08\x81\x00'\
                b'\x00\x00\x00',
                b'\x05\x00\x00\x03\xfe\x00\x00\x00\x00'])
        
        fillbuffer()
        exp = (1, 
            [(b'1', 8, None, None, None, None, 0, 129)],
            {'status_flag': 0, 'warning_count': 0}
            )
        res = self.prtcl._handle_resultset(b'\x01\x00\x00\x01\x01')
        self.assertEqual(exp,res)
        
        fillbuffer()
        self.prtcl.conn.buf[1] = b'\x00'
        
        self.assertRaises(errors.InterfaceError,
            self.prtcl._handle_resultset,b'\x01\x00\x00\x01\x00')
    
    def __helper_get_rows_buffer(self, pkts=None):
        pkts = pkts or [
            b'\x07\x00\x00\x04\x06\x4d\x79\x49\x53\x41\x4d',
            b'\x07\x00\x00\x05\x06\x49\x6e\x6e\x6f\x44\x42',
            b'\x0a\x00\x00\x06\x09\x42\x4c\x41\x43\x4b\x48\x4f\x4c\x45',
            b'\x04\x00\x00\x07\x03\x43\x53\x56',
            b'\x07\x00\x00\x08\x06\x4d\x45\x4d\x4f\x52\x59',
            b'\x0a\x00\x00\x09\x09\x46\x45\x44\x45\x52\x41\x54\x45\x44',
            b'\x08\x00\x00\x0a\x07\x41\x52\x43\x48\x49\x56\x45',
            b'\x0b\x00\x00\x0b\x0a\x4d\x52\x47\x5f\x4d\x59\x49\x53\x41\x4d',
            b'\x05\x00\x00\x0c\xfe\x00\x00\x20\x00',
        ]
        self.prtcl.conn.queue_buffer(pkts)
    
    def test_get_rows(self):
        """Get rows from the MySQL resultset"""
        self.__helper_get_rows_buffer()
        exp = (
            [[b'MyISAM'], [b'InnoDB'], [b'BLACKHOLE'], [b'CSV'], [b'MEMORY'], 
            [b'FEDERATED'], [b'ARCHIVE'], [b'MRG_MYISAM']], 
            {'status_flag': 32, 'warning_count': 0}
            )
        res = self.prtcl.get_rows()
        self.assertEqual(exp,res)
        
        self.__helper_get_rows_buffer()
        rows = exp[0]
        i = 0
        while i < len(rows):
            exp = (rows[i:i+2], None)
            res = self.prtcl.get_rows(2)
            self.assertEqual(exp,res)
            i += 2
        exp = ([], {'status_flag': 32, 'warning_count': 0})
        self.assertEqual(exp,self.prtcl.get_rows())
            
    def test_get_row(self):
        """Get a row from the MySQL resultset"""
        self.__helper_get_rows_buffer()
        expall = (
            [[b'MyISAM'], [b'InnoDB'], [b'BLACKHOLE'], [b'CSV'], [b'MEMORY'], 
            [b'FEDERATED'], [b'ARCHIVE'], [b'MRG_MYISAM']],
            {'status_flag': 32, 'warning_count': 0}
            )
            
        rows = expall[0]
        for row in rows:
            res = self.prtcl.get_row()
            exp = (row,None)
            self.assertEqual(exp,res)
        exp = ([], {'status_flag': 32, 'warning_count': 0})
        self.assertEqual(exp,self.prtcl.get_rows())
            
    def test_cmd_query(self):
        """Send a query to MySQL"""
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
        exp = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0,
            'warning_count': 0, 'server_status': 0}
        res = self.prtcl.cmd_query("SET AUTOCOMMIT = OFF")
        self.assertEqual(exp,res)
        
        # query = "SET AUTOCOMMIT=OFF"
        self.prtcl.conn.queue_buffer([
            b'\x01\x00\x00\x01\x01',
            b'\x17\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x01'\
            b'\x31\x00\x0c\x3f\x00\x01\x00\x00\x00\x08\x81\x00'\
            b'\x00\x00\x00',
            b'\x05\x00\x00\x03\xfe\x00\x00\x00\x00'])
        exp = (1, [(b'1', 8, None, None, None, None, 0, 129)])
        res = self.prtcl.cmd_query("SELECT 1")
        self.assertEqual(exp,res)
        
    def test_cmd_refresh(self):
        """Send the Refresh-command to MySQL"""
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
        refresh = constants.RefreshOption.LOG|constants.RefreshOption.THREADS
        
        exp = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0,
            'warning_count': 0, 'server_status': 0}
        self.assertEqual(exp, self.prtcl.cmd_refresh(refresh))
        
    def test_cmd_quit(self):
        """Send the Quit-command to MySQL"""
        exp = b'\x01\x00\x00\x00\x01'
        self.assertEqual(exp, self.prtcl.cmd_quit())
        
    def test_cmd_init_db(self):
        """Send the Init_db-command to MySQL"""
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
        exp = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0,
                'warning_count': 0, 'server_status': 0}
        self.assertEqual(exp, self.prtcl.cmd_init_db('test'))
        
        self.prtcl.conn.buf.append(
            b'\x2c\x00\x00\x01\xff\x19\x04\x23\x34\x32\x30\x30'\
            b'\x30\x55\x6e\x6b\x6e\x6f\x77\x6e\x20\x64\x61\x74'\
            b'\x61\x62\x61\x73\x65\x20\x27\x75\x6e\x6b\x6e\x6f'\
            b'\x77\x6e\x5f\x64\x61\x74\x61\x62\x61\x73\x65\x27'
            )
        self.assertRaises(errors.ProgrammingError,
            self.prtcl.cmd_init_db,'unknown_database')
        
    def test_cmd_shutdown(self):
        """Send the Shutdown-command to MySQL"""
        
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
        exp = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0,
                'warning_count': 0, 'server_status': 0}
        self.assertEqual(exp, self.prtcl.cmd_shutdown())
        
        self.prtcl.conn.buf.append(
            b'\x4a\x00\x00\x01\xff\xcb\x04\x23\x34\x32\x30\x30'\
            b'\x30\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69'\
            b'\x65\x64\x3b\x20\x79\x6f\x75\x20\x6e\x65\x65\x64'\
            b'\x20\x74\x68\x65\x20\x53\x48\x55\x54\x44\x4f\x57'\
            b'\x4e\x20\x70\x72\x69\x76\x69\x6c\x65\x67\x65\x20'\
            b'\x66\x6f\x72\x20\x74\x68\x69\x73\x20\x6f\x70\x65'\
            b'\x72\x61\x74\x69\x6f\x6e'
        )
        self.assertRaises(errors.OperationalError,
            self.prtcl.cmd_shutdown)
    
    def test_cmd_statistics(self):
        """Send the Statistics-command to MySQL"""
        goodpkt = b'\x88\x00\x00\x01\x55\x70\x74\x69\x6d\x65\x3a\x20'\
            b'\x31\x34\x36\x32\x34\x35\x20\x20\x54\x68\x72\x65'\
            b'\x61\x64\x73\x3a\x20\x32\x20\x20\x51\x75\x65\x73'\
            b'\x74\x69\x6f\x6e\x73\x3a\x20\x33\x36\x33\x35\x20'\
            b'\x20\x53\x6c\x6f\x77\x20\x71\x75\x65\x72\x69\x65'\
            b'\x73\x3a\x20\x30\x20\x20\x4f\x70\x65\x6e\x73\x3a'\
            b'\x20\x33\x39\x32\x20\x20\x46\x6c\x75\x73\x68\x20'\
            b'\x74\x61\x62\x6c\x65\x73\x3a\x20\x31\x20\x20\x4f'\
            b'\x70\x65\x6e\x20\x74\x61\x62\x6c\x65\x73\x3a\x20'\
            b'\x36\x34\x20\x20\x51\x75\x65\x72\x69\x65\x73\x20'\
            b'\x70\x65\x72\x20\x73\x65\x63\x6f\x6e\x64\x20\x61'\
            b'\x76\x67\x3a\x20\x30\x2e\x32\x34'
        self.prtcl.conn.buf.append(goodpkt)
        exp = {'Uptime': 146245, 'Open tables': 64, 
            'Queries per second avg': decimal.Decimal('0.24'),
            'Slow queries': 0, 'Threads': 2, 'Questions': 3635,
            'Flush tables': 1, 'Opens': 392}
        self.assertEqual(exp, self.prtcl.cmd_statistics())
        
        badpkt = b'\x88\x00\x00\x01\x55\x70\x74\x69\x6d\x65\x3a\x20'\
            b'\x31\x34\x36\x32\x34\x35\x20\x54\x68\x72\x65'\
            b'\x61\x64\x73\x3a\x20\x32\x20\x20\x51\x75\x65\x73'\
            b'\x74\x69\x6f\x6e\x73\x3a\x20\x33\x36\x33\x35\x20'\
            b'\x20\x53\x6c\x6f\x77\x20\x71\x75\x65\x72\x69\x65'\
            b'\x73\x3a\x20\x30\x20\x20\x4f\x70\x65\x6e\x73\x3a'\
            b'\x20\x33\x39\x32\x20\x20\x46\x6c\x75\x73\x68\x20'\
            b'\x74\x61\x62\x6c\x65\x73\x3a\x20\x31\x20\x20\x4f'\
            b'\x70\x65\x6e\x20\x74\x61\x62\x6c\x65\x73\x3a\x20'\
            b'\x36\x34\x20\x20\x51\x75\x65\x72\x69\x65\x73\x20'\
            b'\x70\x65\x72\x20\x73\x65\x63\x6f\x6e\x64\x20\x61'\
            b'\x76\x67\x3a\x20\x30\x2e\x32\x34'
        self.prtcl.conn.buf.append(badpkt)
        self.assertRaises(errors.InterfaceError, self.prtcl.cmd_statistics)
        
        badpkt = b'\x88\x00\x00\x01\x55\x70\x74\x69\x6d\x65\x3a\x20'\
            b'\x55\x70\x36\x32\x34\x35\x20\x20\x54\x68\x72\x65'\
            b'\x61\x64\x73\x3a\x20\x32\x20\x20\x51\x75\x65\x73'\
            b'\x74\x69\x6f\x6e\x73\x3a\x20\x33\x36\x33\x35\x20'\
            b'\x20\x53\x6c\x6f\x77\x20\x71\x75\x65\x72\x69\x65'\
            b'\x73\x3a\x20\x30\x20\x20\x4f\x70\x65\x6e\x73\x3a'\
            b'\x20\x33\x39\x32\x20\x20\x46\x6c\x75\x73\x68\x20'\
            b'\x74\x61\x62\x6c\x65\x73\x3a\x20\x31\x20\x20\x4f'\
            b'\x70\x65\x6e\x20\x74\x61\x62\x6c\x65\x73\x3a\x20'\
            b'\x36\x34\x20\x20\x51\x75\x65\x72\x69\x65\x73\x20'\
            b'\x70\x65\x72\x20\x73\x65\x63\x6f\x6e\x64\x20\x61'\
            b'\x76\x67\x3a\x20\x30\x2e\x32\x34'
        self.prtcl.conn.buf.append(badpkt)
        self.assertRaises(errors.InterfaceError, self.prtcl.cmd_statistics)
        
    def test_cmd_process_info(self):
        """Send the Process-Info-command to MySQL"""
        self.assertRaises(errors.NotSupportedError,
            self.prtcl.cmd_process_info)
    
    def test_cmd_process_kill(self):
        """Send the Process-Kill-command to MySQL"""
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
        exp = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0,
                'warning_count': 0, 'server_status': 0}
        self.assertEqual(exp, self.prtcl.cmd_process_kill(1))
        
        pkt = b'\x1f\x00\x00\x01\xff\x46\x04\x23\x48\x59\x30\x30'\
            b'\x30\x55\x6e\x6b\x6e\x6f\x77\x6e\x20\x74\x68\x72'\
            b'\x65\x61\x64\x20\x69\x64\x3a\x20\x31\x30\x30'
        self.prtcl.conn.buf.append(pkt)
        self.assertRaises(errors.InternalError,
            self.prtcl.cmd_process_kill, 100)
        
        pkt =  b'\x29\x00\x00\x01\xff\x47\x04\x23\x48\x59\x30\x30'\
            b'\x30\x59\x6f\x75\x20\x61\x72\x65\x20\x6e\x6f\x74'\
            b'\x20\x6f\x77\x6e\x65\x72\x20\x6f\x66\x20\x74\x68'\
            b'\x72\x65\x61\x64\x20\x31\x36\x30\x35'
        self.prtcl.conn.buf.append(pkt)
        self.assertRaises(errors.OperationalError,
            self.prtcl.cmd_process_kill, 1605)
        
    def test_cmd_debug(self):
        """Send the Debug-command to MySQL"""
        pkt = b'\x05\x00\x00\x01\xfe\x00\x00\x00\x00'
        self.prtcl.conn.buf.append(pkt)
        exp = {'status_flag': 0, 'warning_count': 0}
        self.assertEqual(exp, self.prtcl.cmd_debug())
        
        pkt =  b'\x47\x00\x00\x01\xff\xcb\x04\x23\x34\x32\x30\x30'\
            b'\x30\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69'\
            b'\x65\x64\x3b\x20\x79\x6f\x75\x20\x6e\x65\x65\x64'\
            b'\x20\x74\x68\x65\x20\x53\x55\x50\x45\x52\x20\x70'\
            b'\x72\x69\x76\x69\x6c\x65\x67\x65\x20\x66\x6f\x72'\
            b'\x20\x74\x68\x69\x73\x20\x6f\x70\x65\x72\x61\x74'\
            b'\x69\x6f\x6e'
        self.prtcl.conn.buf.append(pkt)
        self.assertRaises(errors.OperationalError,
            self.prtcl.cmd_debug)
        
    def test_cmd_ping(self):
        """Send the Ping-command to MySQL"""
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
        exp = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0,
                'warning_count': 0, 'server_status': 0}
        self.assertEqual(exp, self.prtcl.cmd_ping())
        
        self.assertRaises(errors.Error,self.prtcl.cmd_ping)
        
        
    def test_cmd_change_user(self):
        """Send the Change-User-command to MySQL"""
        
        handshake = \
            b'\x47\x00\x00\x00\x0a\x35\x2e\x30\x2e\x33\x30\x2d'\
            b'\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67'\
            b'\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68'\
            b'\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72'\
            b'\x59\x48\x00'
        self.prtcl.handle_handshake(handshake)
        
        self.prtcl.conn.buf.append(
            b'\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00')
        exp = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0,
            'warning_count': 0, 'server_status': 2}
        self.prtcl.cmd_change_user(username='ham',
            password='spam',database='python')
            
        self.prtcl.conn.buf.append(
            b'\x45\x00\x00\x01\xff\x14\x04\x23\x34\x32\x30\x30'\
            b'\x30\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69'\
            b'\x65\x64\x20\x66\x6f\x72\x20\x75\x73\x65\x72\x20'\
            b'\x27\x68\x61\x6d\x27\x40\x27\x6c\x6f\x63\x61\x6c'\
            b'\x68\x6f\x73\x74\x27\x20\x74\x6f\x20\x64\x61\x74'\
            b'\x61\x62\x61\x73\x65\x20\x27\x6d\x79\x73\x71\x6c'\
            b'\x27')
        self.assertRaises(errors.OperationalError,
            self.prtcl.cmd_change_user,username='ham',
            password='spam',database='mysql')

