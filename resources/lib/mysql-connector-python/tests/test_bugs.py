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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""Unittests for bugs
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
        """lp:437972 TCP connection to Windows"""
        if os.name != 'nt':
            pass
        
        db = None
        try:
            db = mysql.MySQL(**tests.MYSQL_CONFIG)
        except errors.InterfaceError:
            self.fail()

        if db:
            db.close()

class Bug441430Tests(tests.MySQLConnectorTests):

    def test_execute_return(self):
        """lp:441430 cursor.execute*() should return the cursor.rowcount"""
        
        db = mysql.MySQL(**self.getMySQLConfig())
        c = db.cursor()
        tbl = "buglp44130"
        c.execute("DROP TABLE IF EXISTS %s" % tbl)
        c.execute("CREATE TABLE %s (id INT)" % tbl)
        res = c.execute("INSERT INTO %s VALUES (%%s),(%%s)" % tbl, (1,2,))
        self.assertEqual(2,res)
        stmt = "INSERT INTO %s VALUES (%%s)" % tbl
        res = c.executemany(stmt,[(3,),(4,),(5,),(6,),(7,),(8,)])
        self.assertEqual(6,res)
        res = c.execute("UPDATE %s SET id = id + %%s" % tbl , (10,))
        self.assertEqual(8,res)
        c.close()
        db.close()
        
class Bug454782(tests.MySQLConnectorTests):
    
    def test_fetch_retun_values(self):
        """lp:454782 fetchone() does not follow pep-0249"""
        
        db = mysql.MySQL(**self.getMySQLConfig())
        c = db.cursor()
        self.assertEqual(None,c.fetchone())
        self.assertEqual([],c.fetchmany())
        self.assertRaises(errors.InterfaceError,c.fetchall)
        c.close()
        db.close()

class Bug454790(tests.MySQLConnectorTests):
    
    def test_pyformat(self):
        """lp:454790 pyformat / other named parameters broken"""
        
        db = mysql.MySQL(**self.getMySQLConfig())
        c = db.cursor()
        
        data = {'name': 'Geert','year':1977}
        c.execute("SELECT %(name)s,%(year)s", data)
        self.assertEqual((u'Geert',1977L),c.fetchone())
        
        data = [{'name': 'Geert','year':1977},{'name':'Marta','year':1980}]
        self.assertEqual(2,c.executemany("SELECT %(name)s,%(year)s", data))
        c.close()
        db.close()

class Bug480360(tests.MySQLConnectorTests):
    
    def test_fetchall(self):
        """lp:480360: fetchall() should return [] when no result"""
        
        db = mysql.MySQL(**self.getMySQLConfig())
        c = db.cursor()
        
        # Trick to get empty result not needing any table
        c.execute("SELECT * FROM (SELECT 1) AS t WHERE 0 = 1")
        self.assertEqual([],c.fetchall())
        c.close()
        db.close()
        
class Bug380528(tests.MySQLConnectorTests):

    def test_old_password(self):
        """lp:380528: we do not support old passwords."""

        config = self.getMySQLConfig()
        db = mysql.MySQL(**config)
        c = db.cursor()

        if config['unix_socket']:
            user = "'myconnpy'@'localhost'"
        else:
            user = "'myconnpy'@'%s'" % (config['host'])
        
        try:
            c.execute("GRANT SELECT ON %s.* TO %s" % (config['database'],user))
            c.execute("SET PASSWORD FOR %s = OLD_PASSWORD('fubar')" % (user))
        except:
            self.fail("Failed executing grant.")
        c.close()
        db.close()
        
        # Test using the newly created user
        test_config = config.copy()
        test_config['user'] = 'myconnpy'
        test_config['password'] = 'fubar'
        
        self.assertRaises(errors.InterfaceError,mysql.MySQL,**test_config)
            
        db = mysql.MySQL(**config)
        c = db.cursor()
        try:
            c.execute("REVOKE SELECT ON %s.* FROM %s" % (config['database'],user))
            c.execute("DROP USER %s" % (user))
        except:
            self.fail("Failed cleaning up user %s." % (user))
        c.close()
        db.close()

