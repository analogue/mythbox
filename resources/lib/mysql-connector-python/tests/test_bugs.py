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

import sys, struct, os

import tests
from mysql.connector import mysql, connection, cursor, conversion, protocol, utils, errors, constants

class Bug328998Tests(tests.MySQLConnectorTests):
    
    def test_set_connection_timetout(self):
        config = tests.MYSQL_CONFIG.copy()
        config['connection_timeout'] = 5
        self.db = mysql.MySQL(**config)
        self.assertEqual(config['connection_timeout'],
            self.db.conn.connection_timeout)
        if self.db:
            self.db.disconnect()
    
    def test_timeout(self):
        config = tests.MYSQL_CONFIG.copy()
        config['connection_timeout'] = 1
        self.db = mysql.MySQL(**config)

        c = self.db.cursor()
        self.assertRaises(errors.InterfaceError,
            c.execute, "SELECT SLEEP(%d)" % (config['connection_timeout']+4))

        if self.db:
            self.db.disconnect()

class Bug437972Tests(tests.MySQLConnectorTests):

    def test_windows_tcp_connection(self):
        """lp:Bug#437972 TCP connection to Windows"""
        if os.name != 'nt':
            pass
        
        db = None
        try:
            db = mysql.MySQL(**tests.MYSQL_CONFIG)
        except errors.InterfaceError:
            self.fail()

        if db:
            db.close()

