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

"""Unittests for mysql.connector.cursor
"""

import new
import itertools
from decimal import Decimal
import time
import datetime
import inspect

import tests
from mysql.connector import (connection, cursor, conversion, protocol, 
    utils, errors, constants)

class TestsCursor(tests.MySQLConnectorTests):
    
    def tearDown(self):
        if hasattr(self, 'c') and isinstance(self.c, cursor.MySQLCursor):
            self.c.close()
        if hasattr(self, 'connection') and\
            isinstance(self.connection, connection.MySQLConnection):
            self.connection.close()
    
    def _test_execute_setup(self,connection,
                            tbl="myconnpy_cursor", engine="MyISAM"):
        
        self._test_execute_cleanup(connection, tbl)
        stmt_create = """CREATE TABLE %s 
            (col1 INT, col2 VARCHAR(30), PRIMARY KEY (col1))
            ENGINE=%s""" % (tbl,engine)

        try:
            cursor = connection.cursor()
            cursor.execute(stmt_create)
        except (StandardError), e:
            self.fail("Failed setting up test table; %s" % e)
        cursor.close()
    
    def _test_execute_cleanup(self, connection, tbl="myconnpy_cursor"):
        
        stmt_drop = """DROP TABLE IF EXISTS %s""" % (tbl)
        
        try:
            cursor = connection.cursor()
            cursor.execute(stmt_drop)
        except (StandardError), e:
            self.fail("Failed cleaning up test table; %s" % e)
        cursor.close()

class CursorBaseTests(tests.MySQLConnectorTests):
    
    def setUp(self):
        self.c = cursor.CursorBase()
    
    def test___init__(self):
        exp = {
            '_description': None,
            '_rowcount': -1,
            '_last_insert_id' : None,
            'arraysize': 1,
            }
        
        for key, value in exp.items():
            self.assertEqual(value, getattr(self.c, key),
                             msg="Default for '%s' did not match." % key)

    def test_callproc(self):
        """CursorBase object callproc()-method"""
        self.checkMethod(self.c,'callproc')
        
        try:
            self.c.callproc('foo', args=(1,2,3))
        except (SyntaxError, TypeError):
            self.fail("Cursor callproc(): wrong arguments")
            
    def test_close(self):
        """CursorBase object close()-method"""
        self.checkMethod(self.c,'close')
        
    def test_execute(self):
        """CursorBase object execute()-method"""
        self.checkMethod(self.c,'execute')
            
        try:
            self.c.execute('select', params=(1,2,3))
        except (SyntaxError, TypeError):
            self.fail("Cursor execute(): wrong arguments")
            
    def test_executemany(self):
        """CursorBase object executemany()-method"""
        self.checkMethod(self.c,'executemany')
        
        try:
            self.c.executemany('select', [()])
        except (SyntaxError, TypeError):
            self.fail("Cursor executemany(): wrong arguments")

    def test_fetchone(self):
        """CursorBase object fetchone()-method"""
        self.checkMethod(self.c,'fetchone')
        
    def test_fetchmany(self):
        """CursorBase object fetchmany()-method"""
        self.checkMethod(self.c,'fetchmany')
        
        try:
            self.c.fetchmany(size=1)
        except (SyntaxError, TypeError):
            self.fail("Cursor fetchmany(): wrong arguments")
        
    def test_fetchall(self):
        """CursorBase object fetchall()-method"""
        self.checkMethod(self.c,'fetchall')
        
    def test_nextset(self):
        """CursorBase object nextset()-method"""
        self.checkMethod(self.c,'nextset')
        
    def test_setinputsizes(self):
        """CursorBase object setinputsizes()-method"""
        self.checkMethod(self.c,'setinputsizes')
            
        try:
            self.c.setinputsizes((1,))
        except (SyntaxError, TypeError):
            self.fail("CursorBase setinputsizes(): wrong arguments")
            
    def test_setoutputsize(self):
        """CursorBase object setoutputsize()-method"""
        self.checkMethod(self.c,'setoutputsize')

        try:
            self.c.setoutputsize(1,column=None)
        except (SyntaxError, TypeError):
            self.fail("CursorBase setoutputsize(): wrong arguments")

    def test_description(self):
        self.assertEqual(None, self.c.description)
        self.assertEqual(self.c._description, self.c.description)
        self.c._description = 'ham'
        self.assertEqual('ham', self.c.description)
        try:
            self.c.description = 'spam'
        except AttributeError:
            pass
        else:
            self.fail('CursorBase.description is not read-only')

    def test_rowcount(self):
        self.assertEqual(-1, self.c.rowcount)
        self.assertEqual(self.c._rowcount, self.c.rowcount)
        self.c._rowcount = 2
        self.assertEqual(2, self.c.rowcount)
        try:
            self.c.rowcount = 3
        except AttributeError:
            pass
        else:
            self.fail('CursorBase.rowcount is not read-only')

    def test_last_insert_id(self):
        self.assertEqual(None, self.c.lastrowid)
        self.assertEqual(self.c._last_insert_id, self.c.lastrowid)
        self.c._last_insert_id = 2
        self.assertEqual(2, self.c.lastrowid)
        try:
            self.c.lastrowid = 3
        except AttributeError:
            pass
        else:
            self.fail('CursorBase.lastrowid is not read-only')

class MySQLCursorTests(TestsCursor):
    
    def setUp(self):
        self.c = cursor.MySQLCursor(connection=None)
        self.connection = None
            
    def test_init(self):
        """MySQLCursor object init"""
        try:
            c = cursor.MySQLCursor(connection=None)
        except (SyntaxError, TypeError), e:
            self.fail("Failed initializing MySQLCursor; %s" % e)

        exp = {
            '_connection' : None,
            '_stored_results' : [],
            '_nextrow' : (None, None),
            '_warnings' : None,
            '_warning_count' : 0,
            '_executed' : None,
            '_executed_list' : [],
            }
        
        for key, value in exp.items():
            self.assertEqual(value, getattr(c, key),
                             msg="Default for '%s' did not match." % key)
        
        self.assertRaises(errors.InterfaceError, cursor.MySQLCursor,
                          connection='foo')
        
    def test__set_connection(self):
        """MySQLCursor object _set_connection()-method"""
        self.checkMethod(self.c, '_set_connection')
        
        self.assertRaises(errors.InterfaceError,
                          self.c._set_connection, 'foo')
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c._set_connection(self.connection)
        self.c.close()
        
    def test__reset_result(self):
        """MySQLCursor object _reset_result()-method"""
        self.checkMethod(self.c,'_reset_result')
        
        def reset(self):
            self._test = "Reset called"
        self.c.reset = new.instancemethod(reset, self.c, cursor.MySQLCursor)
        
        exp = {
            'rowcount': -1,
            '_stored_results' : [],
            '_nextrow' : (None, None),
            '_warnings' : None,
            '_warning_count' : 0,
            '_executed' : None,
            '_executed_list' : [],
            }
        
        self.c._reset_result()
        
        for key, value in exp.items():
            self.assertEqual(value, getattr(self.c, key),
                             msg="'%s' was not reset." % key)
        
        # MySQLCursor._reset_result() must call MySQLCursor.reset()
        self.assertEqual('Reset called', self.c._test)

    def test__have_unread_result(self):
        """MySQLCursor object _have_unread_result()-method"""
        self.checkMethod(self.c, '_have_unread_result')
        class FakeConnection(object):
            def __init__(self):
                self.unread_result = False
        
        self.c = cursor.MySQLCursor()
        self.c._connection = FakeConnection()
        
        self.c._connection.unread_result = True
        self.assertTrue(self.c._have_unread_result())
        self.c._connection.unread_result = False
        self.assertFalse(self.c._have_unread_result())

    def test_next(self):
        """MySQLCursor object next()-method"""
        self.checkMethod(self.c,'next')
        
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = cursor.MySQLCursor(self.connection)
        self.assertRaises(StopIteration,self.c.next)
        self.c.execute("SELECT SHA1('myconnpy')")
        exp = (u'c5e24647dbb63447682164d81b34fe493a83610b',)
        self.assertEqual(exp,self.c.next())
        self.c.close()
        
    def test_close(self):
        """MySQLCursor object close()-method"""
        self.checkMethod(self.c, 'close')

        self.assertEqual(False, self.c.close(),
                         "close() should return False with no connection")
        self.assertEqual(None, self.c._connection)
        
    def test__process_params(self):
        """MySQLCursor object _process_params()-method"""
        self.checkMethod(self.c,'_process_params')
        
        self.assertRaises(errors.ProgrammingError,self.c._process_params,'foo')
        self.assertRaises(errors.ProgrammingError,self.c._process_params,())

        st_now = time.localtime()
        data = (
            None,
            int(128),
            long(1281288),
            float(3.14),
            Decimal('3.14'),
            'back\slash',
            'newline\n',
            'return\r',
            "'single'",
            '"double"',
            'windows\032',
            str("Strings are sexy"),
            u'\u82b1',
            datetime.datetime(2008, 5, 7, 20, 01, 23),
            datetime.date(2008, 5, 7),
            datetime.time(20, 03, 23),
            st_now,
            datetime.timedelta(hours=40,minutes=30,seconds=12),
        )
        exp = (
            'NULL',
            '128',
            '1281288',
            '3.14',
            "'3.14'",
            "'back\\\\slash'",
            "'newline\\n'",
            "'return\\r'",
            "'\\'single\\''",
            '\'\\"double\\"\'',
            "'windows\\\x1a'",
            "'Strings are sexy'",
            "'\xe8\x8a\xb1'",
            "'2008-05-07 20:01:23'",
            "'2008-05-07'",
            "'20:03:23'",
            "'%s'" % time.strftime('%Y-%m-%d %H:%M:%S',st_now),
            "'40:30:12'",
        )
        
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = self.connection.cursor()
        self.assertEqual((),self.c._process_params(()),
            "_process_params() should return a tuple")
        res = self.c._process_params(data)
        for (i,v) in enumerate(exp):
            self.assertEqual(v,res[i])
        self.c.close()

    def test__process_params_dict(self):
        """MySQLCursor object _process_params_dict()-method"""
        self.checkMethod(self.c,'_process_params')

        self.assertRaises(errors.ProgrammingError,self.c._process_params,'foo')
        self.assertRaises(errors.ProgrammingError,self.c._process_params,())

        st_now = time.localtime()
        data = {
            'a' : None,
            'b' : int(128),
            'c' : long(1281288),
            'd' : float(3.14),
            'e' : Decimal('3.14'),
            'f' : 'back\slash',
            'g' : 'newline\n',
            'h' : 'return\r',
            'i' : "'single'",
            'j' : '"double"',
            'k' : 'windows\032',
            'l' : str("Strings are sexy"),
            'm' : u'\u82b1',
            'n' : datetime.datetime(2008, 5, 7, 20, 01, 23),
            'o' : datetime.date(2008, 5, 7),
            'p' : datetime.time(20, 03, 23),
            'q' : st_now,
            'r' : datetime.timedelta(hours=40,minutes=30,seconds=12),
        }
        exp = {
            'a' : 'NULL',
            'b' : '128',
            'c' : '1281288',
            'd' : '3.14',
            'e' : "'3.14'",
            'f' : "'back\\\\slash'",
            'g' : "'newline\\n'",
            'h' : "'return\\r'",
            'i' : "'\\'single\\''",
            'j' : '\'\\"double\\"\'',
            'k' : "'windows\\\x1a'",
            'l' : "'Strings are sexy'",
            'm' : "'\xe8\x8a\xb1'",
            'n' : "'2008-05-07 20:01:23'",
            'o' : "'2008-05-07'",
            'p' : "'20:03:23'",
            'q' : "'%s'" % time.strftime('%Y-%m-%d %H:%M:%S',st_now),
            'r' : "'40:30:12'",
        }
        
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = self.connection.cursor()
        self.assertEqual({},self.c._process_params_dict({}),
            "_process_params_dict() should return a dict")
        self.assertEqual(exp,self.c._process_params_dict(data))
        self.c.close()

    def test__fetch_warnings(self):
        """MySQLCursor object _fetch_warnings()-method"""
        self.checkMethod(self.c,'_fetch_warnings')

        self.assertRaises(errors.InterfaceError,self.c._fetch_warnings)
        
        config = self.getMySQLConfig()
        config['get_warnings'] = True
        self.connection = connection.MySQLConnection(**config)
        self.c = self.connection.cursor()
        self.c.execute("SELECT 'a' + 'b'")
        self.c.fetchone()
        exp = [
            (u'Warning', 1292L, u"Truncated incorrect DOUBLE value: 'a'"),
            (u'Warning', 1292L, u"Truncated incorrect DOUBLE value: 'b'")
            ]
        self.assertTrue(self.cmpResult(exp, self.c._fetch_warnings()))
        self.assertEqual(len(exp), self.c._warning_count)
    
    def test__handle_noresultset(self):
        """MySQLCursor object _handle_noresultset()-method"""
        self.checkMethod(self.c,'_handle_noresultset')
        
        self.assertRaises(errors.ProgrammingError,
                          self.c._handle_noresultset, None)
        data = {
            'affected_rows':1,
            'insert_id':10,
            'warning_count': 100,
            'server_status': 8,
            }
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = self.connection.cursor()
        self.c._handle_noresultset(data)
        self.assertEqual(data['affected_rows'],self.c.rowcount)
        self.assertEqual(data['insert_id'], self.c._last_insert_id)
        self.assertEqual(data['warning_count'],self.c._warning_count)
        
        self.c.close()
    
    def test__handle_result(self):
        """MySQLCursor object _handle_result()-method"""
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = self.connection.cursor()
        
        self.assertRaises(errors.InterfaceError, self.c._handle_result, None)
        self.assertRaises(errors.InterfaceError, self.c._handle_result,
                          'spam')
        self.assertRaises(errors.InterfaceError, self.c._handle_result,
                          { 'spam':5 })
        
        cases = [
            { 'affected_rows': 99999,
              'insert_id': 10,
              'warning_count': 100,
              'server_status': 8,
            },
            { 'eof': {'status_flag': 0, 'warning_count': 0}, 
              'columns': [('1', 8, None, None, None, None, 0, 129)]
            },
        ]
        self.c._handle_result(cases[0])
        self.assertEqual(cases[0]['affected_rows'], self.c.rowcount)
        self.assertFalse(self.c._connection.unread_result)
        self.assertFalse(self.c._have_unread_result())
        
        self.c._handle_result(cases[1])
        self.assertEqual(cases[1]['columns'], self.c.description)
        self.assertTrue(self.c._connection.unread_result)
        self.assertTrue(self.c._have_unread_result())
        
    def test_execute(self):
        """MySQLCursor object execute()-method"""
        self.checkMethod(self.c,'execute')
        
        self.assertEqual(None, self.c.execute(None, None))
        
        config = self.getMySQLConfig()
        config['get_warnings'] = True
        self.connection = connection.MySQLConnection(**config)
        self.c = self.connection.cursor()
        
        self.assertRaises(errors.ProgrammingError,self.c.execute,
            'SELECT %s,%s,%s', ('foo','bar',))
        self.assertRaises(errors.ProgrammingError,self.c.execute,
            'SELECT %s,%s', ('foo','bar','foobar'))
        
        self.c.execute("SELECT 'a' + 'b'")
        self.c.fetchone()
        exp = [
            (u'Warning', 1292L, u"Truncated incorrect DOUBLE value: 'a'"),
            (u'Warning', 1292L, u"Truncated incorrect DOUBLE value: 'b'")
            ]
        self.assertTrue(self.cmpResult(exp, self.c._warnings))
        
        self.c.execute("SELECT BINARY 'myconnpy'")
        exp = [(u'myconnpy',)]
        self.assertEqual(exp, self.c.fetchall())
        self.c.close()
        
        tbl = 'myconnpy_cursor'
        self._test_execute_setup(self.connection,tbl)
        stmt_insert = "INSERT INTO %s (col1,col2) VALUES (%%s,%%s)" % (tbl)
        
        self.c = self.connection.cursor()
        res = self.c.execute(stmt_insert, (1,100))
        self.assertEqual(None, res, "Return value of execute() is wrong.")
        stmt_select = "SELECT col1,col2 FROM %s ORDER BY col1" % (tbl)
        self.c.execute(stmt_select)
        self.assertEqual([(1L, u'100')],
            self.c.fetchall(),"Insert test failed")
            
        data = {'id': 2}
        stmt = "SELECT * FROM %s WHERE col1 <= %%(id)s" % tbl
        self.c.execute(stmt, data)
        self.assertEqual([(1L, u'100')],self.c.fetchall())
            
        self._test_execute_cleanup(self.connection,tbl)
        self.c.close()
    
    def test_executemany(self):
        """MySQLCursor object executemany()-method"""
        self.checkMethod(self.c,'executemany')
        
        self.assertEqual(None, self.c.executemany(None, []))
        
        config = self.getMySQLConfig()
        config['get_warnings'] = True
        self.connection = connection.MySQLConnection(**config)
        self.c = self.connection.cursor()
        self.assertRaises(errors.InterfaceError, self.c.executemany,
                          'foo', None)
        self.assertRaises(errors.ProgrammingError, self.c.executemany,
                          'foo', 'foo')
        self.assertEqual(None, self.c.executemany('foo', []))
        self.assertRaises(errors.ProgrammingError, self.c.executemany,
                          'foo', ['foo'])
        self.assertRaises(errors.ProgrammingError,self.c.executemany,
                          'SELECT %s', [('foo',), 'foo'])

        self.c.executemany("SELECT SHA1(%s)", [('foo',),('bar',)])
        self.assertEqual(None,self.c.fetchone())
        self.c.close()
        
        tbl = 'myconnpy_cursor'
        self._test_execute_setup(self.connection,tbl)
        stmt_insert = "INSERT INTO %s (col1,col2) VALUES (%%s,%%s)" % (tbl)
        stmt_select = "SELECT col1,col2 FROM %s ORDER BY col1" % (tbl)
        
        self.c = self.connection.cursor()

        self.c.executemany(stmt_insert,[(1,100),(2,200),(3,300)])
        self.assertEqual(3, self.c.rowcount)

        self.c.executemany("SELECT %s",[('f',),('o',),('o',)])
        self.assertEqual(3, self.c.rowcount)

        data = [{'id':2},{'id':3}]
        stmt = "SELECT * FROM %s WHERE col1 <= %%(id)s" % tbl
        self.c.executemany(stmt, data)
        self.assertEqual(5, self.c.rowcount)

        self.c.execute(stmt_select)
        self.assertEqual([(1L, u'100'), (2L, u'200'), (3L, u'300')],
                         self.c.fetchall(), "Multi insert test failed")
            
        data = [{'id':2},{'id':3}]
        stmt = "DELETE FROM %s WHERE col1 = %%(id)s" % tbl
        self.c.executemany(stmt,data)
        self.assertEqual(2,self.c.rowcount)
            
        self._test_execute_cleanup(self.connection, tbl)
        self.c.close()
    
    def test_fetchwarnings(self):
        """MySQLCursor object fetchwarnings()-method"""
        self.checkMethod(self.c,'fetchwarnings')
        
        self.assertEqual(None,self.c.fetchwarnings(),
            "There should be no warnings after initiating cursor.")
        
        exp = ['A warning']
        self.c._warnings = exp
        self.c._warning_count = len(self.c._warnings)
        self.assertEqual(exp,self.c.fetchwarnings())
        self.c.close()

    def test_stored_results(self):
        """MySQLCursor object stored_results()-method"""
        self.checkMethod(self.c, 'stored_results')

        self.assertEqual([], self.c._stored_results)
        self.assertTrue(hasattr(self.c.stored_results(), '__iter__'))
        self.c._stored_results.append('abc')
        self.assertEqual('abc', self.c.stored_results().next())
        try:
            result = self.c.stored_results().next()
        except StopIteration:
            pass
        except:
            self.fail("StopIteration not raised")

    def _test_callproc_setup(self, connection):

        self._test_callproc_cleanup(connection)
        stmt_create1 = """CREATE PROCEDURE myconnpy_sp_1
            (IN pFac1 INT, IN pFac2 INT, OUT pProd INT)
            BEGIN SET pProd := pFac1 * pFac2;
            END;"""

        stmt_create2 = """CREATE PROCEDURE myconnpy_sp_2
            (IN pFac1 INT, IN pFac2 INT, OUT pProd INT)
            BEGIN SELECT 'abc'; SELECT 'def'; SET pProd := pFac1 * pFac2;
            END;"""

        try:
            cursor = connection.cursor()
            cursor.execute(stmt_create1)
            cursor.execute(stmt_create2)
        except errors.Error, e:
            self.fail("Failed setting up test stored routine; %s" % e)
        cursor.close()

    def _test_callproc_cleanup(self, connection):

        sp_names = ('myconnpy_sp_1','myconnpy_sp_2')
        stmt_drop = "DROP PROCEDURE IF EXISTS %s"

        try:
            cursor = connection.cursor()
            for sp_name in sp_names:
                cursor.execute(stmt_drop % sp_name)
        except errors.Error, e:
            self.fail("Failed cleaning up test stored routine; %s" % e)
        cursor.close()

    def test_callproc(self):
        """MySQLCursor object callproc()-method"""
        self.checkMethod(self.c,'callproc')

        self.assertRaises(errors.ProgrammingError,
                          self.c.callproc, None, None)

        config = self.getMySQLConfig()
        config['get_warnings'] = True
        self.connection = connection.MySQLConnection(**config)
        self._test_callproc_setup(self.connection)
        self.c = self.connection.cursor()

        exp = ('5', '4', 20L)
        result = self.c.callproc('myconnpy_sp_1',(5,4,0))
        self.assertEqual([], self.c._stored_results)
        self.assertEqual(exp, result)

        exp = ('6', '5', 30L)
        result = self.c.callproc('myconnpy_sp_2',(6,5,0))
        self.assertTrue(isinstance(self.c._stored_results, list))
        self.assertEqual(exp, result)

        exp_results = [
            ('abc',),
            ('def',)
            ]
        for result, exp in itertools.izip(self.c.stored_results(),
                                          iter(exp_results)):
            self.assertEqual(exp, result.fetchone())

        self._test_callproc_cleanup(self.connection)
        self.c.close()
    
    def test_fetchone(self):
        """MySQLCursor object fetchone()-method"""
        self.checkMethod(self.c,'fetchone')
        
        self.assertEqual(None,self.c.fetchone())
        
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = self.connection.cursor()
        self.c.execute("SELECT SHA1('myconnpy')")
        exp = (u'c5e24647dbb63447682164d81b34fe493a83610b',)
        self.assertEqual(exp, self.c.fetchone())
        self.assertEqual(None,self.c.fetchone())
        self.c.close()
    
    def test_fetchmany(self):
        """MySQLCursor object fetchmany()-method"""
        self.checkMethod(self.c,'fetchmany')
        
        self.assertEqual([],self.c.fetchmany())
        
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        tbl = 'myconnpy_fetch'
        self._test_execute_setup(self.connection,tbl)
        stmt_insert = "INSERT INTO %s (col1,col2) VALUES (%%s,%%s)" % (tbl)
        stmt_select = "SELECT col1,col2 FROM %s ORDER BY col1 DESC" % (tbl)
        
        self.c = self.connection.cursor()
        nrRows = 10
        data = [ (i,"%s" % (i*100)) for i in range(0,nrRows)]
        self.c.executemany(stmt_insert,data)
        self.c.execute(stmt_select)
        exp = [(9L, u'900'), (8L, u'800'), (7L, u'700'), (6L, u'600')]
        rows = self.c.fetchmany(4)
        self.assertTrue(self.cmpResult(exp,rows),
            "Fetching first 4 rows test failed.")
        exp = [(5L, u'500'), (4L, u'400'), (3L, u'300')]
        rows = self.c.fetchmany(3)
        self.assertTrue(self.cmpResult(exp,rows),
            "Fetching next 3 rows test failed.")
        exp = [(2L, u'200'), (1L, u'100'), (0L, u'0')]
        rows = self.c.fetchmany(3)
        self.assertTrue(self.cmpResult(exp,rows),
            "Fetching next 3 rows test failed.")
        self.assertEqual([],self.c.fetchmany())
        self._test_execute_cleanup(self.connection,tbl)
        self.c.close()
    
    def test_fetchall(self):
        """MySQLCursor object fetchall()-method"""
        self.checkMethod(self.c,'fetchall')
        
        self.assertRaises(errors.InterfaceError,self.c.fetchall)
        
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        tbl = 'myconnpy_fetch'
        self._test_execute_setup(self.connection,tbl)
        stmt_insert = "INSERT INTO %s (col1,col2) VALUES (%%s,%%s)" % (tbl)
        stmt_select = "SELECT col1,col2 FROM %s ORDER BY col1 ASC" % (tbl)
        
        self.c = self.connection.cursor()
        self.c.execute("SELECT * FROM %s" % tbl)
        self.assertEqual([],self.c.fetchall(),
            "fetchall() with empty result should return []")
        nrRows = 10
        data = [ (i,"%s" % (i*100)) for i in range(0,nrRows) ]
        self.c.executemany(stmt_insert,data)
        self.c.execute(stmt_select)
        self.assertTrue(self.cmpResult(data,self.c.fetchall()),
            "Fetching all rows failed.")
        self.assertEqual(None,self.c.fetchone())
        self._test_execute_cleanup(self.connection,tbl)
        self.c.close()
    
    def test_raise_on_warning(self):
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.connection.raise_on_warnings = True
        self.c = self.connection.cursor()
        try:
            self.c.execute("SELECT 'a' + 'b'")
            self.c.fetchall()
        except errors.Error:
            pass
        else:
            self.fail("Did not get exception while raising warnings.")
    
    def test__unicode__(self):
        """MySQLCursor object __unicode__()-method"""
        self.assertEqual("MySQLCursor: (Nothing executed yet)",
            "%s" % self.c.__unicode__())
        
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = self.connection.cursor()
        self.c.execute("SELECT VERSION()")
        self.c.fetchone()
        self.assertEqual("MySQLCursor: SELECT VERSION()",
            "%s" % self.c.__unicode__())
        stmt= "SELECT VERSION(),USER(),CURRENT_TIME(),NOW(),SHA1('myconnpy')"
        self.c.execute(stmt)
        self.c.fetchone()
        self.assertEqual("MySQLCursor: %s.." % stmt[:30],
            "%s" % self.c.__unicode__())
        self.c.close()
    
    def test__str__(self):
        self.assertEqual("'MySQLCursor: (Nothing executed yet)'",
            "%s" % self.c.__str__())
    
    def test_column_names(self):
        self.connection = connection.MySQLConnection(**self.getMySQLConfig())
        self.c = self.connection.cursor()
        stmt = "SELECT NOW() as now, 'The time' as label, 123 FROM dual"
        exp = (u'now', u'label', u'123')
        self.c.execute(stmt)
        self.c.fetchone()
        self.assertEqual(exp, self.c.column_names)
        self.c.close()
    
    def test_statement(self):
        self.c = cursor.MySQLCursor()
        exp = 'SELECT * FROM ham'
        self.c._executed = exp
        self.assertEqual(exp, self.c.statement)
        self.c._executed = '  ' + exp + '    '
        self.assertEqual(exp, self.c.statement)
    
    def test_with_rows(self):
        self.c = cursor.MySQLCursor()
        self.assertFalse(self.c.with_rows)
        self.c._description = ('ham','spam')
        self.assertTrue(self.c.with_rows)

class MySQLCursorBufferedTests(TestsCursor):

    def setUp(self):
        self.c = cursor.MySQLCursorBuffered(connection=None)
        self.connection = None

    def test_init(self):
        """MySQLCursorBuffered object init"""
        try:
            c = cursor.MySQLCursorBuffered(connection=None)
        except (SyntaxError, TypeError), e:
            self.fail("Failed initializing MySQLCursorBuffered; %s" % e)
        
        self.assertRaises(errors.InterfaceError,cursor.MySQLCursorBuffered,
                          connection='foo')
        
    def test__next_row(self):
        """MySQLCursorBuffered object _next_row-attribute"""
        self.checkAttr(self.c,'_next_row',0)
    
    def test__rows(self):
        """MySQLCursorBuffered object _rows-attribute"""
        self.checkAttr(self.c,'_rows',None)

    def test_execute(self):
        """MySQLCursorBuffered object execute()-method
        """
        self.checkMethod(self.c,'execute')

        self.assertEqual(None, self.c.execute(None, None))

        config = self.getMySQLConfig()
        config['buffered'] = True
        config['get_warnings'] = True
        self.connection = connection.MySQLConnection(**config)
        self.c = self.connection.cursor()

        self.assertEqual(True,isinstance(self.c,cursor.MySQLCursorBuffered))
        
        self.c.execute("SELECT 1")
        self.assertEqual([('1',)], self.c._rows)

    def test_raise_on_warning(self):
        config = self.getMySQLConfig()
        config['buffered'] = True
        config['raise_on_warnings'] = True
        self.connection = connection.MySQLConnection(**config)
        self.c = self.connection.cursor()
        try:
            self.c.execute("SELECT 'a' + 'b'")
        except errors.Error:
            pass
        else:
            self.fail("Did not get exception while raising warnings.")

    def test_with_rows(self):
        c = cursor.MySQLCursorBuffered()
        self.assertFalse(c.with_rows)
        c._rows = [('ham',)]
        self.assertTrue(c.with_rows)

class MySQLCursorRawTests(TestsCursor):
    
    def setUp(self):
        config = self.getMySQLConfig()
        config['raw'] = True
        
        self.connection = connection.MySQLConnection(**config)
        self.c = self.connection.cursor()
    
    def tearDown(self):
        self.c.close()
        self.connection.close()
        
    def test_fetchone(self):
        self.checkMethod(self.c,'fetchone')
        
        self.assertEqual(None,self.c.fetchone())
        
        self.c.execute("SELECT 1, 'string', MAKEDATE(2010,365), 2.5")
        exp = ('1','string','2010-12-31', '2.5')
        self.assertEqual(exp,self.c.fetchone())
        
class MySQLCursorRawBufferedTests(TestsCursor):
    
    def setUp(self):
        config = self.getMySQLConfig()
        config['raw'] = True
        config['buffered'] = True
        
        self.connection = connection.MySQLConnection(**config)
        self.c = self.connection.cursor()
    
    def tearDown(self):
        self.c.close()
        self.connection.close()
    
    def test_fetchone(self):
        self.checkMethod(self.c,'fetchone')

        self.assertEqual(None,self.c.fetchone())

        self.c.execute("SELECT 1, 'string', MAKEDATE(2010,365), 2.5")
        exp = ('1','string','2010-12-31', '2.5')
        self.assertEqual(exp,self.c.fetchone())

    def test_fetchall(self):
        self.checkMethod(self.c,'fetchall')

        self.assertRaises(errors.InterfaceError,self.c.fetchall)

        self.c.execute("SELECT 1, 'string', MAKEDATE(2010,365), 2.5")
        exp = [('1','string','2010-12-31', '2.5')]
        self.assertEqual(exp,self.c.fetchall())


