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

"""Unittests
"""

import os
import sys
import socket
import datetime
import logging
import inspect
import unittest

MYSQL_CONFIG = {
    'host' : '127.0.0.1',
    'port' : 33770,
    'unix_socket' : None,
    'user' : 'root',
    'password' : '',
    'database' : 'myconnpy',
    'connection_timeout': 10,
}

MYSQL_VERSION = None
SSL_DIR = os.path.join("support", "ssl")

LOGGER_NAME = "myconnpy_tests"

__all__ = [
    'MySQLConnectorTests',
    'get_test_names','printmsg',
    'active_testcases',
    'LOGGER_NAME',
    'DummySocket',
    'SSL_DIR',
]

active_testcases = [
    'tests.test_utils',
    'tests.test_protocol',
    'tests.test_constants',
    'tests.test_conversion',
    'tests.test_connection',
    'tests.test_network',
    'tests.test_cursor',
    'tests.test_pep249',
    'tests.test_bugs',
    'tests.test_examples',
    'tests.test_mysql_datatypes',
    'tests.test_errors',
    'tests.test_errorcode',
    'tests.test_locales',
]

class UTCTimeZone(datetime.tzinfo):
    def utcoffset(self,dt):
        return datetime.timedelta(0)
    def dst(self,dt):
        return datetime.timedelta(0)

class TestTimeZone(datetime.tzinfo):
    def __init__(self, hours=0):
        self._offset = datetime.timedelta(hours=hours)
    def utcoffset(self,dt):
        return self._offset
    def dst(self,dt):
        return datetime.timedelta(0)

class DummySocket(object):
    """Dummy socket class
    
    This class helps to test socket connection without actually making any
    network activity. It is a proxy class using socket.socket.
    """
    def __init__(self, *args):
        self._socket = socket.socket(*args)
        self._server_replies = ''
        self._client_sends = []
    
    def __getattr__(self, attr):
        return getattr(self._socket, attr)
    
    def recv(self, bufsize=4096, flags=0):
        res = self._server_replies[0:bufsize]
        self._server_replies = self._server_replies[bufsize:]
        return res
    
    def send(self, string, flags=0):
        self._client_sends.append(string)
        return len(string)
        
    def sendall(self, string, flags=0):
        self._client_sends.append(string)
        return None
    
    def add_packet(self, packet):
        self._server_replies += packet
        
    def add_packets(self, packets):
        for packet in packets:
            self._server_replies += packet
            
    def reset(self):
        self._server_replies = ''
        self._client_sends = []

class MySQLConnectorTests(unittest.TestCase):
    
    def getMySQLConfig(self):
        return MYSQL_CONFIG.copy()
    
    def getFakeHostname(self):
        return ''.join([ "%02x" % ord(c) for c in os.urandom(4)])

    def checkAttr(self, obj, attrname, default):
        cls_name = obj.__class__.__name__
        self.assertTrue(hasattr(obj,attrname),
            "%s object has no '%s' attribute" % (cls_name,attrname))
        self.assertEqual(default,getattr(obj,attrname),
            "%s object's '%s' should default to %s '%s'" % (
                cls_name, attrname, type(default).__name__, default)
            )
    
    def checkMethod(self, obj, method):
        cls_name = obj.__class__.__name__
        self.assertTrue(hasattr(obj,method),
            "%s object has no '%s' method" % (cls_name, method))
        self.assertTrue(inspect.ismethod(getattr(obj,method)),
            "%s object defines %s, but is not a method" % (
                cls_name, method))

    
    def checkArguments(self, function, supported_arguments):
        argspec = inspect.getargspec(function)
        function_arguments = dict(zip(argspec[0][1:],argspec[3]))
        for argument,default in function_arguments.items():
            try:
                self.assertEqual(supported_arguments[argument],
                    default, msg="Argument '%s' has wrong default" % argument)
            except KeyError:
                self.fail("Found unsupported or new argument '%s'" % argument)
        for argument,default in supported_arguments.items():
            if not argument in function_arguments:
                self.fail("Supported argument '%s' fails" % argument)

    def haveEngine(self, db, engine):
        """Check if the given storage engine is supported"""
        have = False
        engine = engine.lower()
        c = None
        try:
            c = db.cursor()
            # Should use INFORMATION_SCHEMA, but play nice with v4.1
            c.execute("SHOW ENGINES")
            rows = c.fetchall()
            for row in rows:
                if row[0].lower() == engine:
                    if row[1].lower() == 'yes':
                        have=True
                    break
        except:
            raise
        
            try:
                c.close()
            except:
                pass
        return have

    def cmpResult(self, res1, res2):
        """Compare results (list of tuples) comming from MySQL
        
        For certain results, like SHOW VARIABLES or SHOW WARNINGS, the
        order is unpredictable. To check if what is expected in the
        tests, we need to compare each row.
        """
        try:
            if len(res1) != len(res2):
                return False
        
                for row in res1:
                    if row not in res2:
                        return False
        except:
            return False
            
        return True
    
def get_test_names():
    return [ s.replace('tests.test_','') for s in active_testcases]

def printmsg(msg=None):
    if msg is not None:
        print(msg)
