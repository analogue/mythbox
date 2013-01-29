# -*- coding: utf-8 -*-
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

"""Unittests for examples
"""

import sys
import logging

import mysql.connector
import tests

logger = logging.getLogger(tests.LOGGER_NAME)

class TestExamples(tests.MySQLConnectorTests):
    def setUp(self):
        config = self.getMySQLConfig()
        self.cnx = mysql.connector.connect(**config)
    
    def tearDown(self):
        self.cnx.close()
    
    def _exec_main(self, example):
        try:
            return example.main(self.getMySQLConfig())
        except StandardError, e:
            self.fail(e)
    
    def test_dates(self):
        """examples/dates.py"""
        try:
            import examples.dates as example
        except StandardError, e:
            self.fail(e)
        output = example.main(self.getMySQLConfig())
        exp = ['  1 | 1977-06-14 | 1977-06-14 21:10:00 | 21:10:00 |',
        '  2 |       None |                None |  0:00:00 |',
        '  3 |       None |                None |  0:00:00 |']
        self.assertEqual(output, exp)
        
        example.DATA.append(('0000-00-00',None,'00:00:00'),)
        self.assertRaises(mysql.connector.errors.IntegrityError,
            example.main, self.getMySQLConfig())
        
    def test_engines(self):
        """examples/engines.py"""
        try:
            import examples.engines as example
        except:
            self.fail()
        output = self._exec_main(example)
        
        # Can't check output as it might be different per MySQL instance
        # We check only if MyISAM is present
        found = False
        for s in output:
            if s.find('MyISAM') > -1:
                found = True
                break
        
        self.assertTrue(found,'MyISAM engine not found in output')
        
    def test_inserts(self):
        """examples/inserts.py"""
        try:
            import examples.inserts as example
        except StandardError, e:
            self.fail(e)
        output = self._exec_main(example)
        exp = [u'1 | Geert | 30\nInfo: c..\n',
            u'2 | Jan | 30\nInfo: c..\n', u'3 | Michel | 30\nInfo: c..\n']
        self.assertEqual(output,exp,'Output was not correct')
        
    def test_transactions(self):
        """examples/transactions.py"""
        db = mysql.connector.connect(**self.getMySQLConfig())
        r = self.haveEngine(db,'InnoDB')
        db.close()
        if not r:
            return
            
        try:
            import examples.transaction as example
        except StandardError, e:
            self.fail(e)
        output = self._exec_main(example)
        exp = ['Inserting data', 'Rolling back transaction',
            'No data, all is fine.', 'Data before commit:',
            u'4 | Geert', u'5 | Jan', u'6 | Michel', 'Data after commit:',
            u'4 | Geert', u'5 | Jan', u'6 | Michel']
        self.assertEqual(output,exp,'Output was not correct')
    
    def test_unicode(self):
        """examples/unicode.py"""
        try:
            import examples.unicode as example
        except StandardError, e:
            self.fail(e)
        output = self._exec_main(example)
        exp = ['Unicode string: \xc2\xbfHabla espa\xc3\xb1ol?',
            'Unicode string coming from db: \xc2\xbfHabla espa\xc3\xb1ol?']
        self.assertEqual(output,exp,'Output was not correct')
        
    def test_warnings(self):
        """examples/warnings.py"""
        try:
            import examples.warnings as example
        except StandardError, e:
            self.fail(e)
        output = self._exec_main(example)
        exp = ["Executing 'SELECT 'abc'+1'",
            u"1292: Truncated incorrect DOUBLE value: 'abc'"]
        self.assertEqual(output,exp,'Output was not correct')
        
        example.STMT = "SELECT 'abc'"
        self.assertRaises(StandardError, example.main, self.getMySQLConfig())
        
    def test_multi_resultsets(self):
        """examples/multi_resultsets.py"""
        try:
            import examples.multi_resultsets as example
        except StandardError, e:
            self.fail(e)
        output = self._exec_main(example)
        exp = ['Inserted 1 row', 'Number of rows: 1', 'Inserted 2 rows',
            u'Names in table: Geert Jan Michel']
        self.assertEqual(output,exp,'Output was not correct')

    def test_microseconds(self):
        """examples/microseconds.py"""
        try:
            import examples.microseconds as example
        except StandardError, e:
            self.fail(e)
        output = self._exec_main(example)
        
        if self.cnx.get_server_version() < (5,6,4):
            exp = "does not support fractional precision for timestamps."
            self.assertTrue(output[0].endswith(exp))
        else:
            exp = [
                ' 1 |  1 | 0:00:47.510000',
                ' 1 |  2 | 0:00:47.020000',
                ' 1 |  3 | 0:00:47.650000',
                ' 1 |  4 | 0:00:46.060000',
            ]
            self.assertEqual(output, exp, 'Output was not correct')

