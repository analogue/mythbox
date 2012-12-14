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

"""Unittests for mysql.connector.connection
"""

import os
import socket
import logging
import inspect
import timeit
from decimal import Decimal

SSL_SUPPORT = False
try:
    import ssl
    SSL_SUPPORT = True
except ImportError:
    # If import fails, we don't have SSL support.
    pass

import os
import tests
from tests import mysqld
from mysql.connector import (connection, network, errors, constants, utils,
    cursor)

logger = logging.getLogger(tests.LOGGER_NAME)

OK_PACKET = '\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00'
OK_PACKET_RESULT = {
    'insert_id': 0,
    'affected_rows': 0,
    'field_count': 0,
    'warning_count': 0,
    'server_status': 0
    }

ERR_PACKET = '\x47\x00\x00\x02\xff\x15\x04\x23\x32\x38\x30\x30\x30'\
             '\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69\x65\x64'\
             '\x20\x66\x6f\x72\x20\x75\x73\x65\x72\x20\x27\x68\x61'\
             '\x6d\x27\x40\x27\x6c\x6f\x63\x61\x6c\x68\x6f\x73\x74'\
             '\x27\x20\x28\x75\x73\x69\x6e\x67\x20\x70\x61\x73\x73'\
             '\x77\x6f\x72\x64\x3a\x20\x59\x45\x53\x29'

EOF_PACKET = '\x05\x00\x00\x00\xfe\x00\x00\x00\x00'
EOF_PACKET_RESULT = {'status_flag': 0, 'warning_count': 0}

class _DummyMySQLConnection(connection.MySQLConnection):
    def _open_connection(self, *args, **kwargs):
        pass
    def _post_connection(self, *args, **kwargs):
        pass

class ConnectionTests(tests.MySQLConnectorTests):
    def test_DEFAULT_CONFIGURATION(self):
        exp = {
            'database': None,
            'user': '',
            'password': '',
            'host': '127.0.0.1',
            'port': 3306,
            'unix_socket': None,
            'use_unicode': True,
            'charset': 'utf8',
            'collation': None,
            'autocommit': False,
            'time_zone': None,
            'sql_mode': None,
            'get_warnings': False,
            'raise_on_warnings': False,
            'connection_timeout': None,
            'client_flags': 0,
            'buffered': False,
            'raw': False,
            'ssl_ca': None,
            'ssl_cert': None,
            'ssl_key': None,
            'passwd': None,
            'db': None,
            'connect_timeout': None,
            'dsn': None
        }
        self.assertEqual(exp, connection.DEFAULT_CONFIGURATION)

class MySQLConnectionTests(tests.MySQLConnectorTests):
    def setUp(self):
        config = self.getMySQLConfig()
        self.cnx = connection.MySQLConnection(**config)
    
    def tearDown(self):
        try:
            self.cnx.close()
        except:
            pass
    
    def test___init__(self):
        """MySQLConnection initialization"""
        cnx = connection.MySQLConnection()
        exp = {
             'converter': None,
             '_client_flags': constants.ClientFlag.get_default(),
             '_charset_id': 33,
             '_user': '',
             '_password': '',
             '_database': '',
             '_host': '127.0.0.1',
             '_port': 3306,
             '_unix_socket': None,
             '_use_unicode': True,
             '_get_warnings': False,
             '_raise_on_warnings': False,
             '_connection_timeout': None,
             '_buffered': False,
             '_unread_result': False,
             '_have_next_result': False,
             '_raw': False,
             '_client_host': '',
             '_client_port': 0,
             '_ssl': None,
         }
        for key, value in exp.items():
            self.assertEqual(value, getattr(cnx, key),
                             msg="Default for '%s' did not match." % key)
        
        # Make sure that when at least one argument is given,
        # connect() is called
        class FakeMySQLConnection(connection.MySQLConnection):
            def connect(self, *args, **kwargs):
                self._database = kwargs['database']
        exp = 'test'
        cnx = FakeMySQLConnection(database=exp)
        self.assertEqual(exp, cnx._database)
    
    def test__get_self(self):
        """Return self"""
        self.assertEqual(self.cnx, self.cnx._get_self())
    
    def test__send_cmd(self):
        """Send a command to MySQL"""
        cmd = constants.ServerCmd.QUERY
        arg = 'SELECT 1'
        pktnr = 2
        
        self.cnx._socket.sock = None
        self.assertRaises(errors.OperationalError, self.cnx._send_cmd,
                          cmd, arg, pktnr)
                          
        self.cnx._socket.sock = tests.DummySocket()
        exp = '\x07\x00\x00\x03\x00\x00\x00\x02\x00\x00\x00'
        self.cnx._socket.sock.add_packet(exp)
        res = self.cnx._send_cmd(cmd, arg, pktnr)
        self.assertEqual(exp, res)
        
        # Send an unknown command, the result should be an error packet
        exp = '\x18\x00\x00\x01\xff\x17\x04\x23\x30\x38\x53\x30\x31\x55'\
              '\x6e\x6b\x6e\x6f\x77\x6e\x20\x63\x6f\x6d\x6d\x61\x6e\x64'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(exp)
        res = self.cnx._send_cmd(90, 'spam', 0)

    def test__toggle_have_next_result(self):
        """Toggle _have_next_results based on server/status flags"""
        flags = constants.ServerFlag.MORE_RESULTS_EXISTS
        self.cnx._have_next_result = False
        self.cnx._toggle_have_next_result(flags)
        self.assertTrue(self.cnx._have_next_result)
        self.cnx._toggle_have_next_result(0)
        self.assertFalse(self.cnx._have_next_result)
    
    def test__handle_ok(self):
        """Handle an OK-packet sent by MySQL"""
        self.assertEqual(OK_PACKET_RESULT, self.cnx._handle_ok(OK_PACKET))
        self.assertRaises(errors.ProgrammingError,
                          self.cnx._handle_ok, ERR_PACKET)
        self.assertRaises(errors.InterfaceError,
                          self.cnx._handle_ok, EOF_PACKET)
        
        # Test for multiple results
        self.cnx._have_next_result = False
        packet = OK_PACKET[:-4] + '\x08' + OK_PACKET[-3:]
        self.cnx._handle_ok(packet)
        self.assertTrue(self.cnx._have_next_result)

    def test__handle_eof(self):
        """Handle an EOF-packet sent by MySQL"""
        self.assertEqual(EOF_PACKET_RESULT, self.cnx._handle_eof(EOF_PACKET))
        self.assertRaises(errors.ProgrammingError,
                          self.cnx._handle_eof, ERR_PACKET)
        self.assertRaises(errors.InterfaceError,
                          self.cnx._handle_eof, OK_PACKET)

        # Test for multiple results
        self.cnx._have_next_result = False
        packet = EOF_PACKET[:-2] + '\x08' + EOF_PACKET[-1:]
        self.cnx._handle_eof(packet)
        self.assertTrue(self.cnx._have_next_result)

    def test__handle_result(self):
        """Handle the result after sending a command to MySQL"""
        self.assertRaises(errors.InterfaceError, self.cnx._handle_result,
                          '\x00')
        self.assertRaises(errors.InterfaceError, self.cnx._handle_result,
                          None)
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packets([
                '\x17\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x01'\
                '\x31\x00\x0c\x3f\x00\x01\x00\x00\x00\x08\x81\x00'\
                '\x00\x00\x00',
                '\x05\x00\x00\x03\xfe\x00\x00\x00\x00'])
        
        exp = {
            'eof': {'status_flag': 0, 'warning_count': 0},
            'columns': [('1', 8, None, None, None, None, 0, 129)]
            }
        res = self.cnx._handle_result('\x01\x00\x00\x01\x01')
        self.assertEqual(exp, res)
        
        self.assertEqual(EOF_PACKET_RESULT,
                         self.cnx._handle_result(EOF_PACKET))
        
        # Column count is invalid (is None)
        packet = '\x01\x00\x00\x01\xfb\xa3\x00\xa3'
        self.assertRaises(errors.InterfaceError,
                          self.cnx._handle_result, packet)
        
        # First byte in first packet is wrong
        self.cnx._socket.sock.add_packets([
                '\x00\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x01'\
                '\x31\x00\x0c\x3f\x00\x01\x00\x00\x00\x08\x81\x00'\
                '\x00\x00\x00',
                '\x05\x00\x00\x03\xfe\x00\x00\x00\x00'])
        
        self.assertRaises(errors.InterfaceError,
                          self.cnx._handle_result, '\x01\x00\x00\x01\x00')

    def __helper_get_rows_buffer(self, pkts=None, toggle_next_result=False):
        self.cnx._socket.sock.reset()
        
        packets = [
            '\x07\x00\x00\x04\x06\x4d\x79\x49\x53\x41\x4d',
            '\x07\x00\x00\x05\x06\x49\x6e\x6e\x6f\x44\x42',
            '\x0a\x00\x00\x06\x09\x42\x4c\x41\x43\x4b\x48\x4f\x4c\x45',
            '\x04\x00\x00\x07\x03\x43\x53\x56',
            '\x07\x00\x00\x08\x06\x4d\x45\x4d\x4f\x52\x59',
            '\x0a\x00\x00\x09\x09\x46\x45\x44\x45\x52\x41\x54\x45\x44',
            '\x08\x00\x00\x0a\x07\x41\x52\x43\x48\x49\x56\x45',
            '\x0b\x00\x00\x0b\x0a\x4d\x52\x47\x5f\x4d\x59\x49\x53\x41\x4d',
            '\x05\x00\x00\x0c\xfe\x00\x00\x20\x00',
        ]
        
        if toggle_next_result:
            packets[-1] = packets[-1][:-2] + '\x08' + packets[-1][-1:]
        
        self.cnx._socket.sock.add_packets(packets)
        self.cnx.unread_result = True
    
    def test_get_rows(self):
        """Get rows from the MySQL resultset"""
        self.cnx._socket.sock = tests.DummySocket()
        self.__helper_get_rows_buffer()
        exp = (
            [('MyISAM',), ('InnoDB',), ('BLACKHOLE',), ('CSV',), ('MEMORY',),
             ('FEDERATED',), ('ARCHIVE',), ('MRG_MYISAM',)],
            {'status_flag': 32, 'warning_count': 0}
            )
        res = self.cnx.get_rows()
        self.assertEqual(exp, res)
        
        self.__helper_get_rows_buffer()
        rows = exp[0]
        i = 0
        while i < len(rows):
            exp = (rows[i:i + 2], None)
            res = self.cnx.get_rows(2)
            self.assertEqual(exp, res)
            i += 2
        exp = ([], {'status_flag': 32, 'warning_count': 0})
        self.assertEqual(exp, self.cnx.get_rows())
        
        # Test unread results
        self.cnx.unread_result = False
        self.assertRaises(errors.InternalError, self.cnx.get_rows)

        # Test multiple results
        self.cnx._have_next_results = False
        self.__helper_get_rows_buffer(toggle_next_result=True)
        exp = {'status_flag': 8, 'warning_count': 0}
        self.assertEqual(exp, self.cnx.get_rows()[-1])
        self.assertTrue(self.cnx._have_next_result)

    def test_get_row(self):
        """Get a row from the MySQL resultset"""
        self.cnx._socket.sock = tests.DummySocket()
        self.__helper_get_rows_buffer()
        expall = (
            [('MyISAM',), ('InnoDB',), ('BLACKHOLE',), ('CSV',), ('MEMORY',),
             ('FEDERATED',), ('ARCHIVE',), ('MRG_MYISAM',)],
            {'status_flag': 32, 'warning_count': 0}
            )
            
        rows = expall[0]
        for row in rows:
            res = self.cnx.get_row()
            exp = (row, None)
            self.assertEqual(exp, res)
        exp = ([], {'status_flag': 32, 'warning_count': 0})
        self.assertEqual(exp, self.cnx.get_rows())
        
        # Test unread results
        self.cnx.unread_results = False
        self.assertRaises(errors.InternalError, self.cnx.get_row)

    def test_cmd_init_db(self):
        """Send the Init_db-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packet(OK_PACKET)
        self.assertEqual(OK_PACKET_RESULT, self.cnx.cmd_init_db('test'))
        
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(
            '\x2c\x00\x00\x01\xff\x19\x04\x23\x34\x32\x30\x30'\
            '\x30\x55\x6e\x6b\x6e\x6f\x77\x6e\x20\x64\x61\x74'\
            '\x61\x62\x61\x73\x65\x20\x27\x75\x6e\x6b\x6e\x6f'\
            '\x77\x6e\x5f\x64\x61\x74\x61\x62\x61\x73\x65\x27'
            )
        self.assertRaises(errors.ProgrammingError,
                          self.cnx.cmd_init_db, 'unknown_database')

    def test_cmd_query(self):
        """Send a query to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packet(OK_PACKET)
        res = self.cnx.cmd_query("SET AUTOCOMMIT = OFF")
        self.assertEqual(OK_PACKET_RESULT, res)
        
        packets = [
            '\x01\x00\x00\x01\x01',
            '\x17\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x01'\
            '\x31\x00\x0c\x3f\x00\x01\x00\x00\x00\x08\x81\x00'\
            '\x00\x00\x00',
            '\x05\x00\x00\x03\xfe\x00\x00\x00\x00'
            ]
        
        # query = "SELECT 1"
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packets(packets)
        exp = {
            'eof': {'status_flag': 0, 'warning_count': 0}, 
            'columns': [('1', 8, None, None, None, None, 0, 129)]
        }
        res = self.cnx.cmd_query("SELECT 1")
        self.assertEqual(exp, res)
        self.assertRaises(errors.InternalError,
                          self.cnx.cmd_query, 'SELECT 2')
        self.cnx.unread_result = False
        
        # Forge the packets so the multiple result flag is set
        packets[-1] = packets[-1][:-2] + '\x08' + packets[-1][-1:]
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packets(packets)
        self.assertRaises(errors.InterfaceError,
                          self.cnx.cmd_query, "SELECT 1")

    def test_cmd_query_iter(self):
        """Send queries to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packet(OK_PACKET)
        res = self.cnx.cmd_query_iter("SET AUTOCOMMIT = OFF").next()
        self.assertEqual(OK_PACKET_RESULT, res)
        
        packets = [
            '\x01\x00\x00\x01\x01',
            '\x17\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x01'\
            '\x31\x00\x0c\x3f\x00\x01\x00\x00\x00\x08\x81\x00'\
            '\x00\x00\x00',
            '\x05\x00\x00\x03\xfe\x00\x00\x08\x00',
            '\x02\x00\x00\x04\x01\x31',
            '\x05\x00\x00\x05\xfe\x00\x00\x08\x00',
            '\x07\x00\x00\x06\x00\x01\x00\x08\x00\x00\x00',
            '\x01\x00\x00\x07\x01',
            '\x17\x00\x00\x08\x03\x64\x65\x66\x00\x00\x00\x01'\
            '\x32\x00\x0c\x3f\x00\x01\x00\x00\x00\x08\x81\x00'\
            '\x00\x00\x00',
            '\x05\x00\x00\x09\xfe\x00\x00\x00\x00',
            '\x02\x00\x00\x0a\x01\x32',
            '\x05\x00\x00\x0b\xfe\x00\x00\x00\x00',
            ]
        exp = [
            { 'columns': [('1', 8, None, None, None, None, 0, 129)],
              'eof': {'status_flag': 8, 'warning_count': 0} },
            ([('1',)], {'status_flag': 8, 'warning_count': 0}),
             {'affected_rows': 1,
              'field_count': 0,
              'insert_id': 0,
              'server_status': 8,
              'warning_count': 0},
            {'columns': [('2', 8, None, None, None, None, 0, 129)],
             'eof': {'status_flag': 0, 'warning_count': 0}},
            ([('2',)], {'status_flag': 0, 'warning_count': 0}),
            ]
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packets(packets)
        results = []
        for result in self.cnx.cmd_query_iter("SELECT 1; SELECT 2"):
            results.append(result)
            if 'columns' in result:
                results.append(self.cnx.get_rows())
        self.assertEqual(exp, results)

    def test_cmd_refresh(self):
        """Send the Refresh-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packet(OK_PACKET)
        refresh = constants.RefreshOption.LOG | constants.RefreshOption.THREADS
        
        self.assertEqual(OK_PACKET_RESULT, self.cnx.cmd_refresh(refresh))

    def test_cmd_quit(self):
        """Send the Quit-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.assertEqual('\x01', self.cnx.cmd_quit())

    def test_cmd_shutdown(self):
        """Send the Shutdown-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packet(EOF_PACKET)
        self.assertEqual(EOF_PACKET_RESULT, self.cnx.cmd_shutdown())
        
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(
            '\x4a\x00\x00\x01\xff\xcb\x04\x23\x34\x32\x30\x30'\
            '\x30\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69'\
            '\x65\x64\x3b\x20\x79\x6f\x75\x20\x6e\x65\x65\x64'\
            '\x20\x74\x68\x65\x20\x53\x48\x55\x54\x44\x4f\x57'\
            '\x4e\x20\x70\x72\x69\x76\x69\x6c\x65\x67\x65\x20'\
            '\x66\x6f\x72\x20\x74\x68\x69\x73\x20\x6f\x70\x65'\
            '\x72\x61\x74\x69\x6f\x6e'
        )
        self.assertRaises(errors.ProgrammingError, self.cnx.cmd_shutdown)
    
    def test_cmd_statistics(self):
        """Send the Statistics-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        goodpkt = '\x88\x00\x00\x01\x55\x70\x74\x69\x6d\x65\x3a\x20'\
            '\x31\x34\x36\x32\x34\x35\x20\x20\x54\x68\x72\x65'\
            '\x61\x64\x73\x3a\x20\x32\x20\x20\x51\x75\x65\x73'\
            '\x74\x69\x6f\x6e\x73\x3a\x20\x33\x36\x33\x35\x20'\
            '\x20\x53\x6c\x6f\x77\x20\x71\x75\x65\x72\x69\x65'\
            '\x73\x3a\x20\x30\x20\x20\x4f\x70\x65\x6e\x73\x3a'\
            '\x20\x33\x39\x32\x20\x20\x46\x6c\x75\x73\x68\x20'\
            '\x74\x61\x62\x6c\x65\x73\x3a\x20\x31\x20\x20\x4f'\
            '\x70\x65\x6e\x20\x74\x61\x62\x6c\x65\x73\x3a\x20'\
            '\x36\x34\x20\x20\x51\x75\x65\x72\x69\x65\x73\x20'\
            '\x70\x65\x72\x20\x73\x65\x63\x6f\x6e\x64\x20\x61'\
            '\x76\x67\x3a\x20\x30\x2e\x32\x34'
        self.cnx._socket.sock.add_packet(goodpkt)
        exp = {
            'Uptime': 146245L,
            'Open tables': 64L, 
            'Queries per second avg': Decimal('0.24'),
            'Slow queries': 0L,
            'Threads': 2L,
            'Questions': 3635L,
            'Flush tables': 1L,
            'Opens': 392L
            }
        self.assertEqual(exp, self.cnx.cmd_statistics())
        
        badpkt = '\x88\x00\x00\x01\x55\x70\x74\x69\x6d\x65\x3a\x20'\
            '\x31\x34\x36\x32\x34\x35\x20\x54\x68\x72\x65'\
            '\x61\x64\x73\x3a\x20\x32\x20\x20\x51\x75\x65\x73'\
            '\x74\x69\x6f\x6e\x73\x3a\x20\x33\x36\x33\x35\x20'\
            '\x20\x53\x6c\x6f\x77\x20\x71\x75\x65\x72\x69\x65'\
            '\x73\x3a\x20\x30\x20\x20\x4f\x70\x65\x6e\x73\x3a'\
            '\x20\x33\x39\x32\x20\x20\x46\x6c\x75\x73\x68\x20'\
            '\x74\x61\x62\x6c\x65\x73\x3a\x20\x31\x20\x20\x4f'\
            '\x70\x65\x6e\x20\x74\x61\x62\x6c\x65\x73\x3a\x20'\
            '\x36\x34\x20\x20\x51\x75\x65\x72\x69\x65\x73\x20'\
            '\x70\x65\x72\x20\x73\x65\x63\x6f\x6e\x64\x20\x61'\
            '\x76\x67\x3a\x20\x30\x2e\x32\x34'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(badpkt)
        self.assertRaises(errors.InterfaceError, self.cnx.cmd_statistics)
        
        badpkt = '\x88\x00\x00\x01\x55\x70\x74\x69\x6d\x65\x3a\x20'\
            '\x55\x70\x36\x32\x34\x35\x20\x20\x54\x68\x72\x65'\
            '\x61\x64\x73\x3a\x20\x32\x20\x20\x51\x75\x65\x73'\
            '\x74\x69\x6f\x6e\x73\x3a\x20\x33\x36\x33\x35\x20'\
            '\x20\x53\x6c\x6f\x77\x20\x71\x75\x65\x72\x69\x65'\
            '\x73\x3a\x20\x30\x20\x20\x4f\x70\x65\x6e\x73\x3a'\
            '\x20\x33\x39\x32\x20\x20\x46\x6c\x75\x73\x68\x20'\
            '\x74\x61\x62\x6c\x65\x73\x3a\x20\x31\x20\x20\x4f'\
            '\x70\x65\x6e\x20\x74\x61\x62\x6c\x65\x73\x3a\x20'\
            '\x36\x34\x20\x20\x51\x75\x65\x72\x69\x65\x73\x20'\
            '\x70\x65\x72\x20\x73\x65\x63\x6f\x6e\x64\x20\x61'\
            '\x76\x67\x3a\x20\x30\x2e\x32\x34'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(badpkt)
        self.assertRaises(errors.InterfaceError, self.cnx.cmd_statistics)
        
    def test_cmd_process_info(self):
        """Send the Process-Info-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.assertRaises(errors.NotSupportedError, self.cnx.cmd_process_info)
    
    def test_cmd_process_kill(self):
        """Send the Process-Kill-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packet(OK_PACKET)
        self.assertEqual(OK_PACKET_RESULT, self.cnx.cmd_process_kill(1))
        
        pkt = '\x1f\x00\x00\x01\xff\x46\x04\x23\x48\x59\x30\x30'\
            '\x30\x55\x6e\x6b\x6e\x6f\x77\x6e\x20\x74\x68\x72'\
            '\x65\x61\x64\x20\x69\x64\x3a\x20\x31\x30\x30'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(pkt)
        self.assertRaises(errors.DatabaseError,
                          self.cnx.cmd_process_kill, 100)
        
        pkt = '\x29\x00\x00\x01\xff\x47\x04\x23\x48\x59\x30\x30'\
            '\x30\x59\x6f\x75\x20\x61\x72\x65\x20\x6e\x6f\x74'\
            '\x20\x6f\x77\x6e\x65\x72\x20\x6f\x66\x20\x74\x68'\
            '\x72\x65\x61\x64\x20\x31\x36\x30\x35'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(pkt)
        self.assertRaises(errors.DatabaseError,
                          self.cnx.cmd_process_kill, 1605)
        
    def test_cmd_debug(self):
        """Send the Debug-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        pkt = '\x05\x00\x00\x01\xfe\x00\x00\x00\x00'
        self.cnx._socket.sock.add_packet(pkt)
        exp = {
            'status_flag': 0,
            'warning_count': 0
            }
        self.assertEqual(exp, self.cnx.cmd_debug())
        
        pkt = '\x47\x00\x00\x01\xff\xcb\x04\x23\x34\x32\x30\x30'\
            '\x30\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69'\
            '\x65\x64\x3b\x20\x79\x6f\x75\x20\x6e\x65\x65\x64'\
            '\x20\x74\x68\x65\x20\x53\x55\x50\x45\x52\x20\x70'\
            '\x72\x69\x76\x69\x6c\x65\x67\x65\x20\x66\x6f\x72'\
            '\x20\x74\x68\x69\x73\x20\x6f\x70\x65\x72\x61\x74'\
            '\x69\x6f\x6e'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(pkt)
        self.assertRaises(errors.ProgrammingError, self.cnx.cmd_debug)
        
    def test_cmd_ping(self):
        """Send the Ping-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._socket.sock.add_packet(OK_PACKET)
        self.assertEqual(OK_PACKET_RESULT, self.cnx.cmd_ping())
        
        self.assertRaises(errors.Error, self.cnx.cmd_ping)
        
    def test_cmd_change_user(self):
        """Send the Change-User-command to MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        self.cnx._handshake = {
            'protocol': 10,
            'server_version_original': '5.0.30-enterprise-gpl-log',
            'charset': 8,
            'server_threadid': 265,
            'capabilities': 41516,
            'server_status': 2,
            'scramble': 'h4i6oP!OLng9&PD@WrYH'
            }
        
        self.cnx._socket.sock.add_packet(OK_PACKET)
        exp = OK_PACKET_RESULT.copy()
        exp['server_status'] = 2
        self.cnx.cmd_change_user(username='ham', password='spam',
                                 database='python')
        
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(
            '\x45\x00\x00\x01\xff\x14\x04\x23\x34\x32\x30\x30'\
            '\x30\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69'\
            '\x65\x64\x20\x66\x6f\x72\x20\x75\x73\x65\x72\x20'\
            '\x27\x68\x61\x6d\x27\x40\x27\x6c\x6f\x63\x61\x6c'\
            '\x68\x6f\x73\x74\x27\x20\x74\x6f\x20\x64\x61\x74'\
            '\x61\x62\x61\x73\x65\x20\x27\x6d\x79\x73\x71\x6c'\
            '\x27')
        self.assertRaises(errors.ProgrammingError, self.cnx.cmd_change_user,
                          username='ham', password='spam', database='mysql')

    def test__do_handshake(self):
        """Handle the handshake-packet sent by MySQL"""
        self.cnx._socket.sock = tests.DummySocket()
        handshake = \
            '\x47\x00\x00\x00\x0a\x35\x2e\x30\x2e\x33\x30\x2d'\
            '\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67'\
            '\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68'\
            '\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02'\
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            '\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72'\
            '\x59\x48\x00'
        exp = {
            'protocol': 10,
            'server_version_original': '5.0.30-enterprise-gpl-log',
            'charset': 8,
            'server_threadid': 265,
            'capabilities': 41516,
            'server_status': 2,
            'scramble': 'h4i6oP!OLng9&PD@WrYH'
            }
        
        self.cnx._socket.sock.add_packet(handshake)
        self.cnx._do_handshake()
        self.assertEqual(exp, self.cnx._handshake)
    
        self.assertRaises(errors.InterfaceError, self.cnx._do_handshake)
        
        # Handshake with version set to Z.Z.ZZ to simulate bad version
        false_handshake = \
            '\x47\x00\x00\x00\x0a\x5a\x2e\x5a\x2e\x5a\x5a\x2d'\
            '\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67'\
            '\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68'\
            '\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02'\
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            '\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72'\
            '\x59\x48\x00'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(false_handshake)
        self.assertRaises(errors.InterfaceError, self.cnx._do_handshake)
        
        # Handshake with version set to 4.0.23
        unsupported_handshake = \
            '\x47\x00\x00\x00\x0a\x34\x2e\x30\x2e\x32\x33\x2d'\
            '\x65\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67'\
            '\x70\x6c\x2d\x6c\x6f\x67\x00\x09\x01\x00\x00\x68'\
            '\x34\x69\x36\x6f\x50\x21\x4f\x00\x2c\xa2\x08\x02'\
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            '\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72'\
            '\x59\x48\x00'
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet(unsupported_handshake)
        self.assertRaises(errors.InterfaceError, self.cnx._do_handshake)
            
    def test__do_auth(self):
        """Authenticate with the MySQL server"""
        if not SSL_SUPPORT:
            self.fail("No support for SSL. Please use a Python installation "
                      "compiled with OpenSSL support.")
        self.cnx._socket.sock = tests.DummySocket()
        flags = constants.ClientFlag.get_default()
        kwargs = {
            'username': 'ham',
            'password': 'spam',
            'database': 'test',
            'charset': 33,
            'client_flags': flags,
            }
        
        self.cnx._socket.sock.add_packet(OK_PACKET)
        self.assertEqual(True, self.cnx._do_auth(**kwargs))
        
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packet('\x01\x00\x00\x02\xfe')
        self.assertRaises(errors.NotSupportedError,
                          self.cnx._do_auth, **kwargs)
        
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packets([
            '\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00',
            '\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00'])
        self.cnx.set_client_flags([-constants.ClientFlag.CONNECT_WITH_DB])
        self.assertEqual(True, self.cnx._do_auth(**kwargs))
        
        # Using an unknown database should raise an error
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packets([
            '\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00',
            '\x24\x00\x00\x01\xff\x19\x04\x23\x34\x32\x30\x30'\
            '\x30\x55\x6e\x6b\x6e\x6f\x77\x6e\x20\x64\x61\x74'\
            '\x61\x62\x61\x73\x65\x20\x27\x61\x73\x64\x66\x61'\
            '\x73\x64\x66\x27'])
        flags &= ~constants.ClientFlag.CONNECT_WITH_DB
        kwargs['client_flags'] = flags
        self.assertRaises(errors.ProgrammingError,
                          self.cnx._do_auth, **kwargs)

        # Testing SSL
        flags = constants.ClientFlag.get_default()
        flags |= constants.ClientFlag.SSL
        kwargs = {
            'username': 'ham',
            'password': 'spam',
            'database': 'test',
            'charset': 33,
            'client_flags': flags,
            'ssl_options': {
                'ca': os.path.join(tests.SSL_DIR, 'tests_CA_cert.pem'),
                'cert': os.path.join(tests.SSL_DIR, 'tests_client_cert.pem'),
                'key': os.path.join(tests.SSL_DIR, 'tests_client_key.pem'),
            },
        }
        
        self.cnx._handshake['scramble'] = 'h4i6oP!OLng9&PD@WrYH'
        
        # We check if do_auth send the autherization for SSL and the
        # normal authorization.
        exp = [
            self.cnx._protocol.make_auth_ssl(
                charset=kwargs['charset'],
                client_flags=kwargs['client_flags']),
            self.cnx._protocol.make_auth(
                self.cnx._handshake['scramble'], kwargs['username'],
                kwargs['password'], kwargs['database'],
                charset=kwargs['charset'],
                client_flags=kwargs['client_flags']),
        ]
        self.cnx._socket.switch_to_ssl = lambda ca,cert,key: None
        self.cnx._socket.sock.reset()
        self.cnx._socket.sock.add_packets([
            '\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00',
            '\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00'])    
        self.cnx._do_auth(**kwargs)
        self.assertEqual(
            exp, [ p[4:] for p in self.cnx._socket.sock._client_sends])
        
    def test_config(self):
        """Configure the MySQL connection

        These tests do not actually connect to MySQL, but they make
        sure everything is setup before calling _open_connection() and
        _post_connection().
        """
        cnx = _DummyMySQLConnection()
        default_config = connection.DEFAULT_CONFIGURATION.copy()

        # Should fail because 'dsn' is given
        self.assertRaises(errors.NotSupportedError, cnx.config,
                          **default_config)
        
        # Remove unsupported arguments
        del default_config['dsn']
        try:
            cnx.config(**default_config)
        except AttributeError, e:
            self.fail("Config does not accept a supported argument: %s" %\
                      str(e))
        
        # Add an argument which we don't allow
        default_config['spam'] = 'SPAM'
        self.assertRaises(AttributeError, cnx.config, **default_config)
        
        # We do not support dsn
        self.assertRaises(errors.NotSupportedError, cnx.connect, dsn='ham')

        exp = {
            'host': 'localhost.local',
            'port': 3306,
            'unix_socket': '/tmp/mysql.sock'
        }
        cnx.config(**exp)
        self.assertEqual(exp['port'], cnx._port)
        self.assertEqual(exp['host'], cnx._host)
        self.assertEqual(exp['unix_socket'], cnx._unix_socket)

        exp = (None, 'test', 'mysql  ')
        for database in exp:
            cnx.config(database=database)
            if database is not None:
                database = database.strip()
            failmsg = "Failed setting database to '%s'" % database
            self.assertEqual(database, cnx._database, msg=failmsg)
        cnx.config(user='ham')
        self.assertEqual('ham', cnx._user)

        cnx.config(raise_on_warnings=True)
        self.assertEqual(True, cnx._raise_on_warnings)
        cnx.config(get_warnings=False)
        self.assertEqual(False, cnx._get_warnings)
        cnx.config(connection_timeout=123)
        self.assertEqual(123, cnx._connection_timeout)
        for toggle in [True,False]:
            cnx.config(buffered=toggle)
            self.assertEqual(toggle, cnx._buffered)
            cnx.config(raw=toggle)
            self.assertEqual(toggle, cnx._raw)
        for toggle in [False,True]:
            cnx.config(use_unicode=toggle)
            self.assertEqual(toggle, cnx._use_unicode)

        # Test client flags
        cnx = _DummyMySQLConnection()
        cnx.client_flags = constants.ClientFlag.get_default()
        flag = exp = constants.ClientFlag.COMPRESS
        cnx.config(client_flags=flag)
        self.assertEqual(exp, cnx._client_flags)

        # Setting client flags using a list
        cnx = _DummyMySQLConnection()
        cnx.client_flags = constants.ClientFlag.get_default()
        flags = [constants.ClientFlag.COMPRESS,
                 constants.ClientFlag.FOUND_ROWS]
        exp = constants.ClientFlag.get_default()
        for flag in flags:
            exp |= flag
        cnx.config(client_flags=flags)
        self.assertEqual(exp, cnx._client_flags)

        # and unsetting client flags again
        exp = constants.ClientFlag.get_default()
        flags = [-constants.ClientFlag.COMPRESS,
                 -constants.ClientFlag.FOUND_ROWS]
        cnx.config(client_flags=flags)
        self.assertEqual(exp, cnx._client_flags)

        # Test character set
        # utf8 is default, which is mapped to 33
        self.assertEqual(33, cnx._charset_id)
        cnx.config(charset='latin1')
        self.assertEqual(8, cnx._charset_id)
        cnx.config(charset='latin1', collation='latin1_general_ci')
        self.assertEqual(48, cnx._charset_id)
        cnx.config(collation='latin1_general_ci')
        self.assertEqual(48, cnx._charset_id)
        
        # Test SSL configuration
        exp = {
            'ca': 'CACert',
            'cert': 'ServerCert',
            'key': 'ServerKey',
        }
        cnx.config(ssl_ca=exp['ca'], ssl_cert=exp['cert'], ssl_key=exp['key'])
        self.assertEqual(exp, cnx._ssl)

        # Compatibility tests: MySQLdb
        cnx = _DummyMySQLConnection()
        cnx.connect(db='mysql', passwd='spam', connect_timeout=123)
        self.assertEqual('mysql', cnx._database)
        self.assertEqual('spam', cnx._password)
        self.assertEqual(123, cnx._connection_timeout)

    def test__get_connection(self):
        """Get connection based on configuration"""
        if os.name != 'nt':
            res = self.cnx._get_connection()
            self.assertTrue(isinstance(res, network.MySQLUnixSocket))
        
        self.cnx._unix_socket = None
        self.cnx._connection_timeout = 123
        res = self.cnx._get_connection()
        self.assertTrue(isinstance(res, network.MySQLTCPSocket))
        self.assertEqual(self.cnx._connection_timeout,
                         res._connection_timeout)

    def test__open_connection(self):
        """Open the connection to the MySQL server"""
        # Force TCP Connection
        self.cnx._unix_socket = None
        flags = constants.ClientFlag.get_default()
        self.cnx._open_connection()
        self.assertTrue(isinstance(self.cnx._socket,
                                   network.MySQLTCPSocket))
        self.cnx.close()
        
        self.cnx._client_flags |= constants.ClientFlag.COMPRESS
        self.cnx._open_connection()
        self.assertEqual(self.cnx._socket.recv_compressed,
                         self.cnx._socket.recv)
        self.assertEqual(self.cnx._socket.send_compressed,
                         self.cnx._socket.send)

    def test__post_connection(self):
        """Executes commands after connection has been established"""
        self.cnx._charset_id = 33
        self.cnx._autocommit = True
        self.cnx._time_zone = "-09:00"
        self.cnx._sql_mode = "NO_ZERO_DATE"
        self.cnx._post_connection()
        self.assertEqual('utf8', self.cnx.charset)
        self.assertEqual(self.cnx._autocommit, self.cnx.autocommit)
        self.assertEqual(self.cnx._time_zone, self.cnx.time_zone)
        self.assertEqual(self.cnx._sql_mode, self.cnx.sql_mode)

    def test_connect(self):
        """Connect to the MySQL server"""
        config = self.getMySQLConfig()
        config['unix_socket'] = None
        config['connection_timeout'] = 1

        cnx = connection.MySQLConnection()
        for host in ('localhost','127.0.0.1'):
            try:
                config['host'] = host
                cnx.connect(**config)
                cnx.close()
            except StandardError, e:
                self.fail("Failed connecting to '%s': %s" % (host,str(e)))
        
        config['host'] = self.getFakeHostname()
        self.assertRaises(errors.InterfaceError, cnx.connect, **config)
    
    def test_is_connected(self):
        """Check connection to MySQL Server"""
        self.assertEqual(True, self.cnx.is_connected())
        self.cnx.disconnect()
        self.assertEqual(False, self.cnx.is_connected())
    
    def test_reconnect(self):
        """Reconnecting to the MySQL Server"""
        supported_arguments = {
           'attempts': 1,
           'delay': 0, 
        }
        self.checkArguments(self.cnx.reconnect, supported_arguments)
        
        _test_reconnect_delay = """
            from mysql.connector import connection
            config = {
                'unix_socket': None,
                'host': 'some-fake-hostname.on.mars',
                'connection_timeout': 1, 
            }
            cnx = connection.MySQLConnection()
            cnx.config(**config)
            try:
                cnx.reconnect(attempts=2, delay=3)
            except:
                pass
            """
        
        # Check the delay
        timer = timeit.Timer(_test_reconnect_delay)
        result = timer.timeit(number=1)
        self.assertTrue(result > 3 and result < 12,
                        "3 <= result < 12, was %d" % result)

    def test_ping(self):
        """Ping the MySQL server"""
        supported_arguments = {
            'reconnect': False,
            'attempts': 1,
            'delay': 0, 
        }
        self.checkArguments(self.cnx.ping, supported_arguments)

        try:
            self.cnx.ping()
        except errors.InterfaceError, e:
            self.fail("Ping should have not raised an error")
        
        self.cnx.disconnect()
        self.assertRaises(errors.InterfaceError, self.cnx.ping)
    
    def test_set_converter_class(self):
        """Set the converter class"""
        class TestConverter(object):
            def __init__(self, charset, unicode):
                pass
        
        self.cnx.set_converter_class(TestConverter)
        self.assertTrue(isinstance(self.cnx.converter, TestConverter))
        self.assertEqual(self.cnx._converter_class, TestConverter)
    
    def test_get_server_version(self):
        """Get the MySQL version"""
        self.assertEqual(self.cnx._server_version,
                         self.cnx.get_server_version())
    
    def test_get_server_info(self):
        """Get the original MySQL version information"""
        self.assertEqual(self.cnx._handshake['server_version_original'],
                         self.cnx.get_server_info())
        
        del self.cnx._handshake['server_version_original']
        self.assertEqual(None, self.cnx.get_server_info())
    
    def test_connection_id(self):
        """MySQL connection ID"""
        self.assertEqual(self.cnx._handshake['server_threadid'],
                         self.cnx.connection_id)
        
        del self.cnx._handshake['server_threadid']
        self.assertEqual(None, self.cnx.connection_id)
    
    def test_set_login(self):
        """Set login information for MySQL"""
        exp = ('Ham ', ' Spam ')
        self.cnx.set_login(*exp)
        self.assertEqual(exp[0].strip(), self.cnx._user)
        self.assertEqual(exp[1].strip(), self.cnx._password)
        
        self.cnx.set_login()
        self.assertEqual('', self.cnx._user)
        self.assertEqual('', self.cnx._password)
        
    def test__set_unread_result(self):
        """Toggle unread result set"""
        self.cnx._set_unread_result(True)
        self.assertEqual(True, self.cnx._unread_result)
        self.cnx._set_unread_result(False)
        self.assertEqual(False, self.cnx._unread_result)
        self.assertRaises(ValueError, self.cnx._set_unread_result, 1)
    
    def test__get_unread_result(self):
        """Check for unread result set"""
        self.cnx._unread_result = True
        self.assertEqual(True, self.cnx._get_unread_result())
        self.cnx._unread_result = False
        self.assertEqual(False, self.cnx._get_unread_result())
    
    def test_unread_results(self):
        """Check and toggle unread result using property"""
        self.cnx.unread_result = True
        self.assertEqual(True, self.cnx._unread_result)
        self.cnx.unread_result = False
        self.assertEqual(False, self.cnx._unread_result)

        try:
            self.cnx.unread_result = 1
        except ValueError:
            pass # Expected
        except:
            self.fail("Expected ValueError to be raised")

    def test__set_getwarnings(self):
        """Toggle whether to get warnings"""
        self.cnx._set_getwarnings(True)
        self.assertEqual(True, self.cnx._get_warnings)
        self.cnx._set_getwarnings(False)
        self.assertEqual(False, self.cnx._get_warnings)
        self.assertRaises(ValueError, self.cnx._set_getwarnings, 1)
    
    def test__get_getwarnings(self):
        """Check whether we need to get warnings"""
        self.cnx._get_warnings = True
        self.assertEqual(True, self.cnx._get_getwarnings())
        self.cnx._get_warnings = False
        self.assertEqual(False, self.cnx._get_getwarnings())
    
    def test_get_warnings(self):
        """Check and toggle the get_warnings property"""
        self.cnx.get_warnings = True
        self.assertEqual(True, self.cnx._get_warnings)
        self.cnx.get_warnings = False
        self.assertEqual(False, self.cnx._get_warnings)

        try:
            self.cnx.get_warnings = 1
        except ValueError:
            pass # Expected
        except:
            self.fail("Expected ValueError to be raised")

    def test_set_charset_collation(self):
        """Set the characater set and collation"""
        self.cnx.set_charset_collation('latin1')
        self.assertEqual(8, self.cnx._charset_id)
        self.cnx.set_charset_collation('latin1', 'latin1_general_ci')
        self.assertEqual(48, self.cnx._charset_id)
        self.cnx.set_charset_collation('latin1', None)
        self.assertEqual(8, self.cnx._charset_id)

        self.cnx.set_charset_collation(collation='greek_bin')
        self.assertEqual(70, self.cnx._charset_id)

        self.assertRaises(errors.ProgrammingError,
                          self.cnx.set_charset_collation, 666)
        self.assertRaises(errors.ProgrammingError,
                          self.cnx.set_charset_collation, 'spam')
        self.assertRaises(errors.ProgrammingError,
                          self.cnx.set_charset_collation, 'latin1', 'spam')
        self.assertRaises(errors.ProgrammingError,
                          self.cnx.set_charset_collation, None, 'spam')
        self.assertRaises(ValueError,
                          self.cnx.set_charset_collation, object())
    
    def test_charset(self):
        """Get characater set name"""
        self.cnx.set_charset_collation('latin1', 'latin1_general_ci')
        self.assertEqual('latin1', self.cnx.charset)
        self.cnx._charset_id = 70
        self.assertEqual('greek', self.cnx.charset)
        self.cnx._charset_id = 9
        self.assertEqual('latin2', self.cnx.charset)
        self.cnx._charset_id = 1234567
        try:
            self.cnx.charset
        except errors.ProgrammingError:
            pass # This is expected
        except:
            self.fail("Expected errors.ProgrammingError to be raised")

    def test_collation(self):
        """Get collation name"""
        exp = 'latin2_general_ci'
        self.cnx.set_charset_collation(collation=exp)
        self.assertEqual(exp, self.cnx.collation)
        self.cnx._charset_id = 70
        self.assertEqual('greek_bin', self.cnx.collation)
        self.cnx._charset_id = 9
        self.assertEqual('latin2_general_ci', self.cnx.collation)

        self.cnx._charset_id = 1234567
        try:
            self.cnx.collation
        except errors.ProgrammingError:
            pass # This is expected
        except:
            self.fail("Expected errors.ProgrammingError to be raised")
    
    def test_set_client_flags(self):
        """Set the client flags"""
        self.assertRaises(errors.ProgrammingError,
                          self.cnx.set_client_flags, 'Spam')
        self.assertRaises(errors.ProgrammingError,
                          self.cnx.set_client_flags, 0)
        
        default_flags = constants.ClientFlag.get_default()
        
        exp = default_flags
        self.assertEqual(exp, self.cnx.set_client_flags(exp))
        self.assertEqual(exp, self.cnx._client_flags)
        
        exp = default_flags
        exp |= constants.ClientFlag.SSL
        exp |= constants.ClientFlag.FOUND_ROWS
        exp &= ~constants.ClientFlag.MULTI_RESULTS
        flags = [
            constants.ClientFlag.SSL,
            constants.ClientFlag.FOUND_ROWS,
            -constants.ClientFlag.MULTI_RESULTS
        ]
        self.assertEqual(exp, self.cnx.set_client_flags(flags))
        self.assertEqual(exp, self.cnx._client_flags)
    
    def test_isset_client_flag(self):
        """Check if a client flag is set"""
        default_flags = constants.ClientFlag.get_default()
        self.cnx._client_flags = default_flags
        cases = [
            (constants.ClientFlag.LONG_PASSWD, True),
            (constants.ClientFlag.SSL, False)
        ]
        for flag, exp in cases:
            self.assertEqual(exp, self.cnx.isset_client_flag(flag))
    
    def test_user(self):
        exp = 'ham'
        self.cnx._user = exp
        self.assertEqual(exp, self.cnx.user)

    def test_host(self):
        exp = 'ham'
        self.cnx._host = exp
        self.assertEqual(exp, self.cnx.server_host)

    def test_port(self):
        exp = 'ham'
        self.cnx._port = exp
        self.assertEqual(exp, self.cnx.server_port)

    def test_unix_socket(self):
        exp = 'ham'
        self.cnx._unix_socket = exp
        self.assertEqual(exp, self.cnx.unix_socket)

    def test_set_database(self):
        exp = 'mysql'
        self.cnx.set_database(exp)
        self.assertEqual(exp, self.cnx._info_query("SELECT DATABASE()")[0])
    
    def test_get_database(self):
        exp = 'mysql'
        exp = self.cnx._info_query("SELECT DATABASE()")[0]
        self.assertEqual(exp, self.cnx.get_database())
    
    def test_database(self):
        exp = 'mysql'
        self.cnx.database = exp
        self.assertEqual(exp, self.cnx.database)

    def test_set_time_zone(self):
        """Set the time zone"""
        cnx = _DummyMySQLConnection()
        exp = "-09:00"
        cnx.connect(time_zone=exp)
        self.assertEqual(exp,cnx._time_zone)
        
        exp = "+03:00"
        self.cnx.set_time_zone(exp)
        self.assertEqual(exp,self.cnx._time_zone)
        self.assertEqual(exp,self.cnx._info_query(
            "SELECT @@session.time_zone")[0])
    
    def test_get_time_zone(self):
        """Get the time zone from current MySQL Session"""
        exp = "-08:00"
        self.cnx._info_query("SET @@session.time_zone = '%s'" % exp)
        self.assertEqual(exp,self.cnx.get_time_zone())
    
    def test_time_zone(self):
        """Set and get the time zone through property"""
        exp = "+05:00"
        self.cnx.time_zone = exp
        self.assertEqual(exp,self.cnx._time_zone)
        self.assertEqual(exp,self.cnx.time_zone)
        self.assertEqual(self.cnx.get_time_zone(),self.cnx.time_zone)

    def test_set_sql_mode(self):
        """Set SQL Mode"""
        # Use an unknown SQL Mode
        self.assertRaises(errors.ProgrammingError,self.cnx.set_sql_mode, 'HAM')
        
        # Set an SQL Mode
        try:
            self.cnx.set_sql_mode('TRADITIONAL')
        except Exception, e:
            self.fail("Failed setting SQL Mode")
        
        # Set SQL Mode to a list of modes
        sql_mode = 'TRADITIONAL'
        exp = ('STRICT_TRANS_TABLES,STRICT_ALL_TABLES,NO_ZERO_IN_DATE,'
            'NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,TRADITIONAL,'
            'NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION')
        try:
            self.cnx.set_sql_mode(exp)
            result = self.cnx.get_sql_mode()
        except Exception, e:
            self.fail("Failed setting SQL Mode with multiple modes")
        self.assertEqual(exp,result)

        exp = sorted([
            constants.SQLMode.NO_ZERO_DATE,
            constants.SQLMode.REAL_AS_FLOAT
            ])
        self.cnx.sql_mode = exp
        self.assertEqual(exp, sorted(self.cnx.sql_mode.split(',')))
    
    def test_get_sql_mode(self):
        """Get SQL Mode"""
        config = self.getMySQLConfig()
        config['sql_mode'] = ''
        self.cnx = connection.MySQLConnection(**config)

        # SQL Modes must be empty
        self.assertEqual('',self.cnx.get_sql_mode())

        # Set SQL Mode and check
        sql_mode = exp = 'NO_ZERO_IN_DATE'
        self.cnx.set_sql_mode(sql_mode)
        self.assertEqual(exp,self.cnx.get_sql_mode())

        # Unset the SQL Mode again
        self.cnx.set_sql_mode('')
        self.assertEqual('',self.cnx.get_sql_mode())

    def test_sql_mode(self):
        """Set and get SQL Mode through property"""
        config = self.getMySQLConfig()
        config['sql_mode'] = ''
        self.cnx = connection.MySQLConnection(**config)

        sql_mode = exp = 'NO_ZERO_IN_DATE'
        self.cnx.sql_mode = sql_mode
        self.assertEqual(exp,self.cnx.sql_mode)

    def test_set_autocommit(self):
        self.cnx.set_autocommit(True)
        res = self.cnx._info_query("SELECT @@session.autocommit")[0]
        self.assertEqual(1, res)
        self.cnx.set_autocommit(0)
        res = self.cnx._info_query("SELECT @@session.autocommit")[0]
        self.assertEqual(0, res)

    def test_get_autocommit(self):
        cases = [False, True]
        for exp in cases:
            self.cnx.set_autocommit(exp)
            res = self.cnx._info_query("SELECT @@session.autocommit")[0]
            self.assertEqual(exp, cases[res])
    
    def test_autocommit(self):
        for exp in [False, True]:
            self.cnx.autocommit = exp
            self.assertEqual(exp, self.cnx.autocommit)

    def test__set_raise_on_warnings(self):
        """Toggle whether to get warnings"""
        self.cnx._set_raise_on_warnings(True)
        self.assertEqual(True, self.cnx._raise_on_warnings)
        self.cnx._set_raise_on_warnings(False)
        self.assertEqual(False, self.cnx._raise_on_warnings)
        self.assertRaises(ValueError, self.cnx._set_raise_on_warnings, 1)
    
    def test__get_raise_on_warnings(self):
        """Check whether we need to get warnings"""
        self.cnx._raise_on_warnings = True
        self.assertEqual(True, self.cnx._get_raise_on_warnings())
        self.cnx._raise_on_warnings = False
        self.assertEqual(False, self.cnx._get_raise_on_warnings())
    
    def test_raise_on_warnings(self):
        """Check and toggle the get_warnings property"""
        self.cnx.raise_on_warnings = True
        self.assertEqual(True, self.cnx._get_raise_on_warnings())
        self.cnx.raise_on_warnings = False
        self.assertEqual(False, self.cnx._get_raise_on_warnings())

        try:
            self.cnx.get_warnings = 1
        except ValueError:
            pass # Expected
        except:
            self.fail("Expected ValueError to be raised")

    def test_cursor(self):
        class FalseCursor(object):
            pass
        
        class TrueCursor(cursor.CursorBase):
            def __init__(self, cnx):
                pass
        
        self.assertRaises(errors.ProgrammingError, self.cnx.cursor,
                          cursor_class=FalseCursor)
        self.assertTrue(isinstance(self.cnx.cursor(cursor_class=TrueCursor),
                                                   TrueCursor))
        
        cases = [
           ({}, cursor.MySQLCursor),
           ({'buffered': True}, cursor.MySQLCursorBuffered),
           ({'raw': True}, cursor.MySQLCursorRaw),
           ({'buffered': True, 'raw': True}, cursor.MySQLCursorBufferedRaw),
        ]
        for kwargs, exp in cases:
            self.assertTrue(isinstance(self.cnx.cursor(**kwargs),exp))
        
        # Test when connection is closed
        self.cnx.close()
        self.assertRaises(errors.OperationalError, self.cnx.cursor)


