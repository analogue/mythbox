# MySQL Connector/Python - MySQL driver written in Python.
# Copyright (c) 2009, 2012, Oracle and/or its affiliates. All rights reserved.

# MySQL Connector/Python is licensed under the terms of the GPLv2
# <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>, like most
# MySQL Connectors. There are special exceptions to the terms and
# conditions of the GPLv2 as it is applied to this software, see the
# FOSS License Exception
# <http://www.mysql.com/about/legal/licensing/foss-exception.html>.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
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
from mysql.connector import (connection, network,
                             protocol, errors, constants)

OK_PACKET = b'\x07\x00\x00\x01\x00\x01\x00\x00\x00\x01\x00'
OK_PACKET_RESULT = {
    'insert_id': 0,
    'affected_rows': 1,
    'field_count': 0,
    'warning_count': 1,
    'server_status': 0
    }

ERR_PACKET = b'\x47\x00\x00\x02\xff\x15\x04\x23\x32\x38\x30\x30\x30'\
             b'\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69\x65\x64'\
             b'\x20\x66\x6f\x72\x20\x75\x73\x65\x72\x20\x27\x68\x61'\
             b'\x6d\x27\x40\x27\x6c\x6f\x63\x61\x6c\x68\x6f\x73\x74'\
             b'\x27\x20\x28\x75\x73\x69\x6e\x67\x20\x70\x61\x73\x73'\
             b'\x77\x6f\x72\x64\x3a\x20\x59\x45\x53\x29'

EOF_PACKET = b'\x01\x00\x00\x00\xfe\x00\x00\x00\x00'
EOF_PACKET_RESULT = {'status_flag': 0, 'warning_count': 0}

SEED = b'\x3b\x55\x78\x7d\x2c\x5f\x7c\x72\x49\x52'\
       b'\x3f\x28\x47\x6f\x77\x28\x5f\x28\x46\x69'

class MySQLProtocolTests(tests.MySQLConnectorTests):
    def setUp(self):
        self._protocol = protocol.MySQLProtocol()
    
    def test__scramble_password(self):
        """Scramble a password ready to send to MySQL"""
        password = "spam".encode('utf-8')
        hashed = b'\x3a\x07\x66\xba\xba\x01\xce\xbe\x55\xe6'\
                 b'\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91\x5b'
        
        res = self._protocol._scramble_password(password, SEED)
        self.assertEqual(hashed, res)
    
    def test_make_auth(self):
        """Make a MySQL authentication packet"""
        exp = {
            'allset':\
            b'\x0d\xa2\x03\x00\x00\x00\x00\x40'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x68\x61\x6d\x00\x14\x3a\x07\x66\xba\xba\x01\xce'\
            b'\xbe\x55\xe6\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91'\
            b'\x5b\x74\x65\x73\x74\x00',
            'nopass':\
            b'\x0d\xa2\x03\x00\x00\x00\x00\x40'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x68\x61\x6d\x00\x00\x74\x65\x73\x74\x00',
            'nouser':\
            b'\x0d\xa2\x03\x00\x00\x00\x00\x40'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x14\x3a\x07\x66\xba\xba\x01\xce'\
            b'\xbe\x55\xe6\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91'\
            b'\x5b\x74\x65\x73\x74\x00',
            'nodb':\
            b'\x0d\xa2\x03\x00\x00\x00\x00\x40'\
            b'\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x68\x61\x6d\x00\x14\x3a\x07\x66\xba\xba\x01\xce'\
            b'\xbe\x55\xe6\x29\x88\xaa\xae\xdb\x00\xb3\x4d\x91'\
            b'\x5b\x00',
            }
        flags = constants.ClientFlag.get_default()
        kwargs = {
            'seed': None,
            'username': 'ham',
            'password': 'spam',
            'database': 'test',
            'charset': 33,
            'client_flags': flags}
        
        self.assertRaises(errors.ProgrammingError,
                          self._protocol.make_auth, **kwargs)
            
        kwargs['seed'] = SEED
        res = self._protocol.make_auth(**kwargs)
        self.assertEqual(exp['allset'], res)
        
        kwargs['password'] = None
        res = self._protocol.make_auth(**kwargs)
        self.assertEqual(exp['nopass'], res)
        
        kwargs['password'] = 'spam'
        kwargs['database'] = None
        res = self._protocol.make_auth(**kwargs)
        self.assertEqual(exp['nodb'], res)
        
        kwargs['username'] = None
        kwargs['database'] = 'test'
        res = self._protocol.make_auth(**kwargs)
        self.assertEqual(exp['nouser'],res)

    def test_make_auth_ssl(self):
        """Make a SSL authentication packet"""
        cases = [
            ({},
             b'\x00\x00\x00\x00\x00\x00\x00\x40\x21\x00\x00\x00\x00\x00'\
             b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
             b'\x00\x00\x00\x00'),
            ({'charset': 8},
             b'\x00\x00\x00\x00\x00\x00\x00\x40\x08\x00\x00\x00\x00\x00'\
             b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
             b'\x00\x00\x00\x00'),
            ({'client_flags': 240141},
             b'\x0d\xaa\x03\x00\x00\x00\x00\x40\x21\x00\x00\x00\x00\x00'\
             b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
             b'\x00\x00\x00\x00'),
            ({'charset': 8, 'client_flags': 240141,
              'max_allowed_packet': 2147483648},
              b'\x0d\xaa\x03\x00\x00\x00\x00\x80\x08\x00\x00\x00\x00\x00'\
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
              b'\x00\x00\x00\x00'),
        ]
        for kwargs, exp in cases:
            self.assertEqual(exp, self._protocol.make_auth_ssl(**kwargs))
    
    def test_make_command(self):
        """Make a generic MySQL command packet"""
        exp = b'\x01\x68\x61\x6d'
        arg = 'ham'.encode('utf-8')
        res = self._protocol.make_command(1, arg)
        self.assertEqual(exp, res)
        res = self._protocol.make_command(1, argument=arg)
        self.assertEqual(exp, res)
        
        exp = b'\x03'
        res = self._protocol.make_command(3)
        self.assertEqual(exp, res)
    
    def test_make_changeuser(self):
        """Make a change user MySQL packet"""
        exp = {
            'allset':\
            b'\x11\x68\x61\x6d\x00\x14\x3a\x07'\
            b'\x66\xba\xba\x01\xce\xbe\x55\xe6\x29\x88\xaa\xae'\
            b'\xdb\x00\xb3\x4d\x91\x5b\x74\x65\x73\x74\x00\x08'\
            b'\x00',
            'nopass':\
            b'\x11\x68\x61\x6d\x00\x00\x74\x65'\
            b'\x73\x74\x00\x08\x00',
            }
        kwargs = {
            'seed': None,
            'username': 'ham',
            'password': 'spam',
            'database': 'test',
            'charset': 8,
            'client_flags': constants.ClientFlag.get_default()
        }
        self.assertRaises(errors.ProgrammingError,
                          self._protocol.make_change_user, **kwargs)

        kwargs['seed'] = SEED
        res = self._protocol.make_change_user(**kwargs)
        self.assertEqual(exp['allset'], res)
        
        kwargs['password'] = None
        res = self._protocol.make_change_user(**kwargs)
        self.assertEqual(exp['nopass'], res)
    
    def test_parse_handshake(self):
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
        
        res = self._protocol.parse_handshake(handshake)
        self.assertEqual(exp, res)
        
    def test_parse_ok(self):
        """Parse OK-packet sent by MySQL"""
        res = self._protocol.parse_ok(OK_PACKET)
        self.assertEqual(OK_PACKET_RESULT, res)
        
        okpkt = OK_PACKET + b'\x04spam'
        exp = OK_PACKET_RESULT.copy()
        exp['info_msg'] = b'spam'
        res = self._protocol.parse_ok(okpkt)
        self.assertEqual(exp, res)
    
    def test_parse_column_count(self):
        """Parse the number of columns"""
        packet = b'\x01\x00\x00\x01\x03'
        res = self._protocol.parse_column_count(packet)
        self.assertEqual(3, res)
        
    def test_parse_column(self):
        """Parse field-packet sent by MySQL"""
        column_packet = \
            b'\x1a\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x04'\
            b'\x53\x70\x61\x6d\x00\x0c\x21\x00\x09\x00\x00\x00'\
            b'\xfd\x01\x00\x1f\x00\x00'
        exp = ('Spam', 253, None, None, None, None, 0, 1)
        res = self._protocol.parse_column(column_packet)
        self.assertEqual(exp, res)

    def test_parse_eof(self):
        """Parse EOF-packet sent by MySQL"""
        res = self._protocol.parse_eof(EOF_PACKET)
        self.assertEqual(EOF_PACKET_RESULT, res)

    def test_read_text_result(self):
        # Tested by MySQLConnectionTests.test_get_rows() and .test_get_row()
        pass

