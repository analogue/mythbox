# MySQL Connector/Python - MySQL driver written in Python.
# Copyright (c) 2012, Oracle and/or its affiliates. All rights reserved.

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

"""Unittests for mysql.connector.network
"""

import os
import socket
import logging
from collections import deque

import tests
from mysql.connector import (network, connection, errors, constants, utils)

logger = logging.getLogger(tests.LOGGER_NAME)

class NetworkTests(tests.MySQLConnectorTests):
    """Testing mysql.connector.network functions"""
    def test__prepare_packets(self):
        """Prepare packets for sending"""
        data = (b'abcdefghijklmn', 1)
        exp = [b'\x0e\x00\x00\x01abcdefghijklmn']
        self.assertEqual(exp, network._prepare_packets(*(data)))

        data = (b'a' * (constants.MAX_PACKET_LENGTH + 1000), 2)
        exp = [
            b'\xff\xff\xff\x02' + (b'a' * constants.MAX_PACKET_LENGTH),
            b'\xe8\x03\x00\x03' + (b'a' * 1000)
        ]
        self.assertEqual(exp, network._prepare_packets(*(data)))

class BaseMySQLSocketTests(tests.MySQLConnectorTests):
    """Testing mysql.connector.network.BaseMySQLSocket"""
    def setUp(self):
        config = self.getMySQLConfig()
        self._host = config['host']
        self._port = config['port']
        self.cnx = network.BaseMySQLSocket()
    
    def tearDown(self):
        try:
            self.cnx.close_connection()
        except:
            pass
    
    def _get_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug("Get socket for {}:{}".format(self._host, self._port))
        sock.connect((self._host, self._port))
        return sock
        
    def test_init(self):
        """MySQLSocket initialization"""
        exp = {
            'sock': None,
            '_connection_timeout': None,
            '_packet_queue': deque(),
            'recvsize': 1024*8,
        }
        
        for key, value in exp.items():
            self.assertEqual(value, self.cnx.__dict__[key])
    
    def test_next_packet_number(self):
        """Test packet number property"""
        self.assertEqual(0, self.cnx.next_packet_number)
        self.assertEqual(0, self.cnx._packet_number)
        self.assertEqual(1, self.cnx.next_packet_number)
        self.assertEqual(1, self.cnx._packet_number)
    
    def test_open_connection(self):
        """Opening a connection"""
        self.assertRaises(NotImplementedError, self.cnx.open_connection)

    def test_get_address(self):
        """Get the address of a connection"""
        self.assertRaises(NotImplementedError, self.cnx.get_address)
    
    def test_close_connection(self):
        """Closing a connection"""
        self.cnx.close_connection()
        self.assertEqual(None, self.cnx.sock)
    
    def test_send_plain(self):
        """Send plain data through the socket"""
        data = b'asddfasdfasdf'
        self.assertRaises(errors.OperationalError, self.cnx.send_plain, 
                          data, 0)
        
        self.cnx.sock = tests.DummySocket()
        data = [
            (b'\x03\x53\x45\x4c\x45\x43\x54\x20\x22\x61\x62\x63\x22',1),
            (b'\x03\x53\x45\x4c\x45\x43\x54\x20\x22'
             + (b'\x61' * (constants.MAX_PACKET_LENGTH + 1000)) + b'\x22', 2)]
        
        self.assertRaises(Exception, self.cnx.send_plain, None, None)
        
        for d in data:
            exp = network._prepare_packets(*d)
            try:
                self.cnx.send_plain(*d)
            except Exception as err:
                self.fail("Failed sending pktnr {}: {}".format(d[1],
                                                               str(err)))
            self.assertEqual(exp, self.cnx.sock._client_sends)
            self.cnx.sock.reset()
    
    def test_send_compressed(self):
        """Send compressed data through the socket"""
        data = b'asddfasdfasdf'
        self.assertRaises(errors.OperationalError, self.cnx.send_compressed, 
                          data, 0)

        self.cnx.sock = tests.DummySocket()
        self.assertRaises(Exception, self.cnx.send_compressed, None, None)

        # Small packet
        data = (b'\x03\x53\x45\x4c\x45\x43\x54\x20\x22\x61\x62\x63\x22', 1)
        exp = [b'\x11\x00\x00\x00\x00\x00\x00\r\x00\x00\x01\x03SELECT "abc"']
        try:
            self.cnx.send_compressed(*data)
        except Exception as err:
            self.fail("Failed sending pktnr {}: {}".format(d[1], err))
        self.assertEqual(exp, self.cnx.sock._client_sends)
        self.cnx.sock.reset()

        # Slightly bigger packet (not getting compressed)
        data = (b'\x03\x53\x45\x4c\x45\x43\x54\x20\x22\x61\x62\x63\x22', 1)
        exp = (24, b'\x11\x00\x00\x00\x00\x00\x00\x0d\x00\x00\x01\x03'
               b'\x53\x45\x4c\x45\x43\x54\x20\x22')
        try:
            self.cnx.send_compressed(*data)
        except Exception as err:
            self.fail("Failed sending pktnr {}: {}".format(d[1],str(err)))
        received = self.cnx.sock._client_sends[0]
        self.assertEqual(exp, (len(received), received[:20]))
        self.cnx.sock.reset()

        # Big packet
        data = (b'\x03\x53\x45\x4c\x45\x43\x54\x20\x22'
                + b'\x61'*(constants.MAX_PACKET_LENGTH+1000) + b'\x22', 2)
        exp = [
            (63,b'\x38\x00\x00\x00\x00\x40\x00\x78\x9c\xed\xc1\x31'
                b'\x0d\x00\x20\x0c\x00\xb0\x04\x8c'),
            (16322, b'\xbb\x3f\x00\x01\xf9\xc3\xff\x78\x9c\xec\xc1\x81'
                b'\x00\x00\x00\x00\x80\x20\xd6\xfd')]
        try:
            self.cnx.send_compressed(*data)
        except Exception as err:
            self.fail("Failed sending pktnr {}: {}".format(d[1], str(e)))
        received = [ (len(r), r[:20]) for r in self.cnx.sock._client_sends ]
        self.assertEqual(exp, received)
        self.cnx.sock.reset()
    
    def test_recv_plain(self):
        """Receive data from the socket"""
        self.cnx.sock = tests.DummySocket()

        # Receive a packet which is not 4 bytes long
        self.cnx.sock.add_packet(b'\01\01\01')
        self.assertRaises(errors.InterfaceError, self.cnx.recv_plain)

        # Receive the header of a packet, but nothing more
        self.cnx.sock.add_packet(b'\01\00\00\00')
        self.assertRaises(errors.InterfaceError, self.cnx.recv_plain)

        # Receive packets after a query, SELECT "Ham"
        exp = [
          b'\x01\x00\x00\x01\x01',
          b'\x19\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x03\x48\x61\x6d\x00'\
          b'\x0c\x21\x00\x09\x00\x00\x00\xfd\x01\x00\x1f\x00\x00',
          b'\x05\x00\x00\x03\xfe\x00\x00\x02\x00',
          b'\x04\x00\x00\x04\x03\x48\x61\x6d',
          b'\x05\x00\x00\x05\xfe\x00\x00\x02\x00',
        ]
        self.cnx.sock.reset()
        self.cnx.sock.add_packets(exp)
        length_exp = len(exp)
        result = []
        packet = self.cnx.recv_plain()
        while packet:
            result.append(packet)
            if length_exp == len(result):
                break
            packet = self.cnx.recv_plain()
        self.assertEqual(exp, result)

    def test_recv_compressed(self):
        """Receive compressed data from the socket"""
        self.cnx.sock = tests.DummySocket()

        # Receive a packet which is not 7 bytes long
        self.cnx.sock.add_packet(b'\01\01\01\01\01\01')
        self.assertRaises(errors.InterfaceError, self.cnx.recv_compressed)

        # Receive the header of a packet, but nothing more
        self.cnx.sock.add_packet(b'\01\00\00\00\00\00\00')
        self.assertRaises(errors.InterfaceError, self.cnx.recv_compressed)

        # Receive result of query SELECT REPEAT('a',1*1024*1024), 'XYZ'
        packets = (
            b'\x80\x00\x00\x01\x00\x40\x00\x78\x9c\xed\xcb\xbd\x0a\x81\x01'
            b'\x14\xc7\xe1\xff\xeb\xa5\x28\x83\x4d\x26\x99\x7c\x44\x21\x37'
            b'\x60\xb0\x4b\x06\x6c\x0a\xd7\xe3\x7a\x15\x79\xc9\xec\x0a\x9e'
            b'\x67\x38\x9d\xd3\xaf\x53\x24\x45\x6d\x96\xd4\xca\xcb\xf5\x96'
            b'\xa4\xbb\xdb\x6c\x37\xeb\xfd\x68\x78\x1e\x4e\x17\x93\xc5\x7c'
            b'\xb9\xfa\x8e\x71\xda\x83\xaa\xde\xf3\x28\xd2\x4f\x7a\x49\xf9'
            b'\x7b\x28\x0f\xc7\xd3\x27\xb6\xaa\xfd\xf9\x8d\x8d\xa4\xfe\xaa'
            b'\xae\x34\xd3\x69\x3c\x93\xce\x19\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\xf8\xeb\x0d\xe7\xa5\x29\xb8',

            b'\x05\x04\x00\x02\x68\xc0\x0f\x78\x9c\xed\xc1\x31\x01\x00\x00'
            b'\x08\x03\xa0\xc3\x92\xea\xb7\xfe\x25\x8c\x60\x01\x20\x01' +
            b'\x00'*999+b'\xe0\x53\x3d\x7b\x0a\x29\x40\x7b'
            )
        exp = [
            b'\x01\x00\x00\x01\x02',
            b'\x2d\x00\x00\x02\x03\x64\x65\x66\x00\x00\x00\x17\x52\x45\x50'
            b'\x45\x41\x54\x28\x27\x61\x27\x2c\x31\x2a\x31\x30\x32\x34\x2a'
            b'\x31\x30\x32\x34\x29\x00\x0c\x21\x00\x00\x00\x90\x00\xfa\x01'
            b'\x00\x1f\x00\x00',
            b'\x19\x00\x00\x03\x03\x64\x65\x66\x00\x00\x00\x03\x58\x59\x5a'
            b'\x00\x0c\x21\x00\x09\x00\x00\x00\xfd\x01\x00\x1f\x00\x00',
            b'\x05\x00\x00\x04\xfe\x00\x00\x00\x00',
            b'\x08\x00\x10\x05\xfd\x00\x00\x10' +
            b'\x61'*1*1024*1024+b'\x03\x58\x59\x5a'
            ]
        self.cnx.sock.reset()
        self.cnx.sock.add_packets(packets)
        length_exp = len(exp)
        packet = self.cnx.recv_compressed()
        counter = 0
        while packet and counter < length_exp:
            self.assertEqual(exp[counter],packet)
            packet = self.cnx.recv_compressed()
            counter += 1
        
    def test_set_connection_timeout(self):
        """Set the connection timeout"""
        exp = 5
        self.cnx.set_connection_timeout(exp)
        self.assertEqual(exp, self.cnx._connection_timeout)

    def test_switch_to_ssl(self):
        """Switch the socket to use SSL"""
        args = {
            'ca': os.path.join(tests.SSL_DIR, 'tests_CA_cert.pem'),
            'cert': os.path.join(tests.SSL_DIR, 'tests_client_cert.pem'),
            'key': os.path.join(tests.SSL_DIR, 'tests_client_key.pem'),
            }
        self.assertRaises(errors.InterfaceError,
                          self.cnx.switch_to_ssl, **args)

        # Handshake failure
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(4)
        sock.connect((self._host, self._port))
        self.cnx.sock = sock
        self.assertRaises(errors.InterfaceError,
                          self.cnx.switch_to_ssl, **args)

class MySQLUnixSocketTests(tests.MySQLConnectorTests):
    """Testing mysql.connector.network.MySQLUnixSocket"""
    def setUp(self):
        config = self.getMySQLConfig()
        self._unix_socket = config['unix_socket']
        self.cnx = network.MySQLUnixSocket(unix_socket=config['unix_socket'])
    
    def tearDown(self):
        try:
            self.cnx.close_connection()
        except:
            pass
    
    def test_init(self):
        """MySQLUnixSocket initialization"""
        exp = {
            'unix_socket': self._unix_socket,
        }
        
        for key, value in exp.items():
            self.assertEqual(value, self.cnx.__dict__[key])
    
    def test_get_address(self):
        """Get path to the Unix socket"""
        exp = self._unix_socket
        self.assertEqual(exp, self.cnx.get_address())
    
    def test_open_connection(self):
        """Open a connection using a Unix socket"""
        if os.name == 'nt':
            self.assertRaises(errors.InterfaceError, self.cnx.open_connection)
        else:
            try:
                self.cnx.open_connection()
            except Exception as err:
                self.fail(str(err))

class MySQLTCPSocketTests(tests.MySQLConnectorTests):
    """Testing mysql.connector.network..MySQLTCPSocket"""
    def setUp(self):
        config = self.getMySQLConfig()
        self._host = config['host']
        self._port = config['port']
        self.cnx = network.MySQLTCPSocket(host=self._host, port=self._port)
    
    def tearDown(self):
        try:
            self.cnx.close_connection()
        except:
            pass
        
    def test_init(self):
        """MySQLTCPSocket initialization"""
        exp = {
            'server_host': self._host,
            'server_port': self._port,
        }

        for key, value in exp.items():
            self.assertEqual(value, self.cnx.__dict__[key])
    
    def test_get_address(self):
        """Get TCP/IP address"""
        exp = "%s:%s" % (self._host, self._port)
        self.assertEqual(exp, self.cnx.get_address())

    def test_open_connection(self):
        """Open a connection using TCP"""
        try:
            self.cnx.open_connection()
        except Exception as err:
            self.fail(str(err))
