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

"""Unittests for mysql.connector.errors
"""

import sys
import tests
from mysql.connector import errors

class ErrorsTests(tests.MySQLConnectorTests):
    def test_custom_error_exception(self):
        customfunc = errors.custom_error_exception
        self.assertRaises(ValueError, customfunc, 'spam')
        self.assertRaises(ValueError, customfunc, 1)
        self.assertRaises(ValueError, customfunc, 1, 'spam')

        case = (1,errors.InterfaceError)
        exp = { 1: errors.InterfaceError }
        self.assertEqual(exp, customfunc(*case))

        exp = case = { 1: errors.InterfaceError, 2: errors.ProgrammingError }
        self.assertEqual(exp, customfunc(case))

        case = { 1: errors.InterfaceError, 2: None }
        self.assertRaises(ValueError, customfunc, case)
        case = { 1: errors.InterfaceError, 2: str() }
        self.assertRaises(ValueError, customfunc, case)
        case = { '1': errors.InterfaceError }
        self.assertRaises(ValueError, customfunc, case)

        self.assertEqual({}, customfunc({}))
        self.assertEqual({}, errors._CUSTOM_ERROR_EXCEPTIONS)

    def test_get_mysql_exception(self):
        tests = {
            errors.ProgrammingError: (
                '24', '25', '26', '27', '28', '2A', '2C',
                '34', '35', '37', '3C', '3D', '3F', '42'),
            errors.DataError: ('02', '21', '22'),
            errors.NotSupportedError: ('0A',),
            errors.IntegrityError: ('23', 'XA'),
            errors.InternalError: ('40', '44'),
            errors.OperationalError: ('08', 'HZ', '0K'),
            errors.DatabaseError: ('07', '2B', '2D', '2E', '33', 'ZZ', 'HY'),
        }
        
        msg = 'Ham'
        for exp, errlist in tests.items():
            for sqlstate in errlist:
                errno = 1000
                res = errors.get_mysql_exception(errno, msg, sqlstate)
                self.assertTrue(isinstance(res, exp),
                                "SQLState %s should be %s" % (
                                    sqlstate, exp.__name__))
                self.assertEqual(sqlstate, res.sqlstate)
                self.assertEqual("%d (%s): %s" % (errno, sqlstate, msg),
                                 res.msg)
        
        errno = 1064
        sqlstate = "42000"
        msg = "You have an error in your SQL syntax"
        exp = "1064 (42000): You have an error in your SQL syntax"
        err = errors.get_mysql_exception(errno, msg, sqlstate)
        self.assertEqual(exp, str(err))

        # Custom exceptions
        errors._CUSTOM_ERROR_EXCEPTIONS[1064] = errors.DatabaseError
        self.assertTrue(
            isinstance(errors.get_mysql_exception(1064, None, None),
                       errors.DatabaseError))
        errors._CUSTOM_ERROR_EXCEPTIONS = {}

    def test_get_exception(self):
        ok_packet = '\x07\x00\x00\x01\x00\x01\x00\x00\x00\x01\x00'
        err_packet = '\x47\x00\x00\x02\xff\x15\x04\x23\x32\x38\x30\x30\x30'\
                     '\x41\x63\x63\x65\x73\x73\x20\x64\x65\x6e\x69\x65\x64'\
                     '\x20\x66\x6f\x72\x20\x75\x73\x65\x72\x20\x27\x68\x61'\
                     '\x6d\x27\x40\x27\x6c\x6f\x63\x61\x6c\x68\x6f\x73\x74'\
                     '\x27\x20\x28\x75\x73\x69\x6e\x67\x20\x70\x61\x73\x73'\
                     '\x77\x6f\x72\x64\x3a\x20\x59\x45\x53\x29'
        self.assertTrue(isinstance(errors.get_exception(err_packet),
                                   errors.ProgrammingError))

        self.assertRaises(ValueError,
                          errors.get_exception, ok_packet)
        
        res = errors.get_exception('\x47\x00\x00\x02\xff\x15')
        self.assertTrue(isinstance(res, errors.InterfaceError))


class ErrorTest(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.Error, StandardError))
        
        err = errors.Error(None)
        self.assertEqual(-1, err.errno)
        self.assertEqual('Unknown error', err.msg)

        err = errors.Error('Ham', errno=1)
        self.assertEqual(1, err.errno)
        self.assertEqual('1: Ham', err.msg)
        
        err = errors.Error('Ham', errno=1, sqlstate="SPAM")
        self.assertEqual(1, err.errno)
        self.assertEqual('1 (SPAM): Ham', err.msg)

        err = errors.Error(errno=2000)
        self.assertEqual('2000: Unknown MySQL error', err.msg)
        
        err = errors.Error(errno=2003, values=('/path/to/ham', 2))
        self.assertEqual(
            u"2003: Can't connect to MySQL server on '/path/to/ham' (2)",
            err.msg)

        err = errors.Error(errno=2001, values=('ham',))
        if '(Warning:' in str(err):
            self.fail('Found %d in error message.')

        err = errors.Error(errno=2003, values=('ham',))
        self.assertEqual(
            u"2003: Can't connect to MySQL server on '%-.100s' (%s) "
            u"(Warning: not enough arguments for format string)",
            err.msg)
    
    def test___str__(self):
        exp = "Spam"
        self.assertEqual(exp, str(errors.Error(exp)))

class WarningTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.Warning, StandardError))

class InterfaceErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.InterfaceError, errors.Error))

class DatabaseErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.DatabaseError, errors.Error))

class InternalErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.InternalError,
                        errors.DatabaseError))

class OperationalErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.OperationalError,
                        errors.DatabaseError))

class ProgrammingErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.ProgrammingError,
                        errors.DatabaseError))

class IntegrityErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.IntegrityError,
                        errors.DatabaseError))

class DataErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.DataError,
                        errors.DatabaseError))

class NotSupportedErrorTests(tests.MySQLConnectorTests):
    def test___init__(self):
        self.assertTrue(issubclass(errors.NotSupportedError,
                        errors.DatabaseError))

