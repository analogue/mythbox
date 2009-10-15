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

import sys
import getpass
sys.path.append('../')

import unittest

MYSQL_CONFIG = {
    'host' : 'localhost',
    'unix_socket' : None,
    'user' : getpass.getuser(),
    'password' : '',
    'database' : 'test',
}

__all__ = [
    'MySQLConnectorTests',
    
    'active_testcases',
]

active_testcases = [
    'tests.test_utils',
    'tests.test_protocol',
    'tests.test_constants',
    'tests.test_conversion',
    'tests.test_pep249',
    'tests.test_bugs',
]

class MySQLConnectorTests(unittest.TestCase):
    pass


