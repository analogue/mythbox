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

import datetime, decimal
import tests

from mysql.connector import mysql, connection, cursor, conversion, protocol, utils, errors, constants



class ClientTests(tests.MySQLConnectorTests):

    def setUp(self):
        self.client = None
        
    def tearDown(self):
        if self.client:
            self.client.disconnect()

class PacketTests(tests.MySQLConnectorTests):
    """Tests for protocol.Packet"""
    
    def test_init(self):
        """Check if Packet instance is initialized correctly"""
        pkt = protocol.Packet(None, 2)
        
        self.assertEqual('',pkt.buffer)
        self.assertEqual(0,pkt.length)
        self.assertEqual(2,pkt.pktnr)
        self.assertEqual(10,pkt.protocol)

    def test__make_header(self):
        """Make header of packet"""
        exp = '\x10\x00\x00\x00'
        data =  '\x43\x6f\x6e\x6e\x65\x63\x74\x6f\x72\x2f\x50\x79\x74\x68\x6f\x6e'
        pkt = protocol.Packet()
        pkt.buffer = data
        
        self.assertEqual(exp, pkt._make_header())

    def test_get(self):
        """Get the buffer of the packet"""
        data = '\x43\x6f\x6e\x6e\x65\x63\x74\x6f\x72\x2f\x50\x79\x74\x68\x6f\x6e'
        exp = '\x10\x00\x00\x00' + data
        pkt = protocol.Packet()
        pkt.buffer = data
        
        self.assertEqual(exp,pkt.get())
    
    def test_is_valid(self):
        """Test validity of the buffer"""
        data = '\x10\x00\x00\x00' + '\x43\x6f\x6e\x6e\x65\x63\x74\x6f\x72\x2f\x50\x79\x74\x68\x6f\x6e'
        pkt = protocol.Packet()
        
        self.assertTrue(pkt.is_valid(data))
        self.assertFalse(pkt.is_valid(data[0:10]))

    def test_set(self):
        """Set the buffer of the packet"""
        data = '\x43\x6f\x6e\x6e\x65\x63\x74\x6f\x72\x2f\x50\x79\x74\x68\x6f\x6e'
        exp = '\x10\x00\x00\x00' + data
        exp_len = len(data)
        pkt = protocol.Packet()
        pkt.set(exp)

        self.assertEqual(exp,pkt.get())
        self.assertEqual(exp_len,pkt.get_length())

    def test_get_header(self):
        """Get header of packet"""
        exp = '\x10\x00\x00\x00'
        data =  exp + '\x43\x6f\x6e\x6e\x65\x63\x74\x6f\x72\x2f\x50\x79\x74\x68\x6f\x6e'
        pkt = protocol.Packet(data)

        self.assertEqual(exp, pkt.get_header())
    
    def test_add(self):
        """Add 3 strings to the packet"""
        
        # data == 'Connector/Python'
        data = '\x43\x6f\x6e\x6e\x65\x63\x74\x6f\x72\x2f\x50\x79\x74\x68\x6f\x6e'
        exp = '\x10\x00\x00\x00' + data
        pkt = protocol.Packet()
        pkt.add('Connector')
        pkt.add('/')
        pkt.add('Python')
        
        self.assertEqual(exp,pkt.get())
    
    def test_add_1_int(self):
        """Add a 0 < integer < 2**8 to the packet"""
        data = 2**8-1
        exp = '\x01\x00\x00\x00\xff'
        
        pkt = protocol.Packet()
        pkt.add_1_int(data)
        
        self.assertEqual(exp,pkt.get())
    
    def test_add_2_int(self):
        """Add a 0 < integer < 2**16 to the packet"""
        data = 2**16-1
        exp = '\x02\x00\x00\x00\xff\xff'

        pkt = protocol.Packet()
        pkt.add_2_int(data)

        self.assertEqual(exp,pkt.get())

    def test_add_3_int(self):
        """Add a 0 < integer < 2**24 to the packet"""
        data = 2**24-1
        exp = '\x03\x00\x00\x00\xff\xff\xff'

        pkt = protocol.Packet()
        pkt.add_3_int(data)

        self.assertEqual(exp,pkt.get())
        
    def test_add_4_int(self):
        """Add a 0 < integer < 2**32 to the packet"""
        data = 2**32-1
        exp = '\x04\x00\x00\x00\xff\xff\xff\xff'

        pkt = protocol.Packet()
        pkt.add_4_int(data)

        self.assertEqual(exp,pkt.get())
    
    def test_add_null(self):
        """Add some null values to a the packet"""
        data = 5
        exp = '\x05\x00\x00\x00' + ('\x00' * 5)
        
        pkt = protocol.Packet()
        pkt.add_null(data)
        
        self.assertEqual(exp,pkt.get())
    
    def test__is_valid_extra(self):
        """Extra validation of buffer"""
        pkt = protocol.Packet()
        
        self.assertEqual(None, pkt._is_valid_extra())

class HandshakeTest(tests.MySQLConnectorTests):
    
    _handshake = '\x47\x00\x00\x00\x0a\x35\x2e\x30\x2e\x33\x30\x2d\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72\x59\x48\x00'
    
    def test_get_dict(self):
        """Parse a handshake packet"""
        data = self._handshake
        pkt = protocol.Handshake(data)
        info = {
            'charset': 8,
            'thrdid': 265, 
            'capabilities': 41516,
            'version': '5.0.30-enterprise-gpl-log',
            'serverstatus': 2,
            'seed': 'h4i6oP!OLng9&PD@WrYH'
            }
            
        self.assertEqual(pkt.get_dict(), info)

    def test__is_valid_extra(self):
        """Extra validity test"""
        data = self._handshake
        data_false = '\x47\x00\x00\x10\x0a\x35\x2e\x30' # 4th byte is wrong
        pkt = protocol.Handshake()
        
        self.assertTrue(pkt._is_valid_extra(data))
        self.assertFalse(pkt._is_valid_extra(data_false))

class AuthTest(tests.MySQLConnectorTests):
    
    def test__init(self):
        """Check if Auth instance is initialized correctly"""
        pkt = protocol.Auth()
        
        self.assertEqual(0, pkt.client_flags)
        self.assertEqual(None, pkt.username)
        self.assertEqual(None, pkt.username)
        self.assertEqual(None, pkt.database)
    
    def test_set_client_flags(self):
        """Set the client flags"""
        exp = constants.ClientFlag.CONNECT_WITH_DB | constants.ClientFlag.RESERVED
        pkt = protocol.Auth()
        pkt.set_client_flags(exp)
        pkt2 = protocol.Auth(client_flags=exp)
        
        self.assertEqual(exp, pkt.client_flags)
        self.assertEqual(exp, pkt2.client_flags)
    
    def test_set_login(self):
        """Set the credentials and database"""
        exp = ('userA','passwordA','db')
        pkt = protocol.Auth()
        pkt.set_login(*exp)
        
        self.assertEqual(exp[0], pkt.username)
        self.assertEqual(exp[1], pkt.password)
        self.assertEqual(exp[2], pkt.database)
        
    def test_scramble(self):
        """Scramble the password using a seed"""
        password = 'passwordA'
        seed = 'h4i6oP!OLng9&PD@WrYH'
        exp = '\xd73M\xd89w\x15\xc6f\x819\x11\x81g\x00\xa8b\x1b\xbaI'
        pkt = protocol.Auth()
        
        self.assertEqual(exp, pkt.scramble(password, seed))
    
    def test_create(self):
        """Create the Auth packet"""
        data = {
            'username' : 'userA',
            'password' : 'passwordA',
            'database' : 'db',
            'seed' : 'h4i6oP!OLng9&PD@WrYH',
        }
        exp = '\x00\x00\x00\x00\x00\x00\xa0\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00userA\x00\x14\xd73M\xd89w\x15\xc6f\x819\x11\x81g\x00\xa8b\x1b\xbaIdb\x00'
        pkt = protocol.Auth()
        pkt.create(**data)
        
        self.assertEqual(exp, pkt.buffer)

class ChangeUserPacketTest(tests.MySQLConnectorTests):
    
    def test__init(self):
        """Check if ChangeUserPacket instance is initialized correctly"""
        pkt = protocol.ChangeUserPacket()
        
        self.assertEqual(constants.ServerCmd.CHANGE_USER, pkt.command)
    
    def test_create(self):
        """Create the ChangeUser packet"""
        data = {
            'username' : 'userA',
            'password' : 'passwordA',
            'database' : 'db',
            'seed' : 'h4i6oP!OLng9&PD@WrYH',
            'charset': 32,
        }
        exp = '\x11userA\x00\x14\xd73M\xd89w\x15\xc6f\x819\x11\x81g\x00\xa8b\x1b\xbaIdb\x00 \x00'
        pkt = protocol.ChangeUserPacket()
        pkt.create(**data)
        
        self.assertEqual(exp, pkt.buffer)
        
