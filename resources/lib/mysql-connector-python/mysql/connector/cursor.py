# -*- coding: utf-8 -*-
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

import exceptions

import protocol
import errors
import utils

class CursorBase(object):
    """
    Base for defining MySQLCursor. This class is a skeleton and defines
    methods and members as required for the Python Database API
    Specification v2.0.
    
    It's better to inherite from MySQLCursor.
    """
    
    description = None
    rowcount = -1
    arraysize = 1
    lastrowid = None
    warnings = None
    
    def __init__(self):
        pass
    
    def __del__(self):
        self.close()
    
    def callproc(self, procname, args=()):
        pass
    
    def close(self):
        pass
    
    def execute(self, operation, params=()):
        pass
    
    def executemany(self, operation, seqparams):
        pass
    
    def fetchone(self):
        pass
    
    def fetchmany(self, size=1):
        pass
    
    def fetchall(self):
        pass
    
    def nextset(self):
        pass
    
    def setinputsizes(self, sizes):
        pass
    
    def setoutputsize(self, size, column=None):
        pass
        
class MySQLCursor(CursorBase):
    """
    Default cursor which fetches all rows and stores it for later
    usage. It uses the converter set for the MySQLConnection to map
    MySQL types to Python types automatically.
    
    This class should be inherited whenever other functionallity is
    required. An example would to change the fetch* member functions
    to return dictionaries instead of lists of values.
    
    Implements the Python Database API Specification v2.0.
    
    Possible parameters are:
    
    db
        A MySQLConnection instance.
    """
    
    db = None
    result = []
    nextrow = 0
    _warning_count = 0

    def __init__(self, db):
        self.db = db # Keep in touch with the database
        self.fields = ()
        self.nrflds = 0
        
        self.protocol = db.conn.protocol
    
    def __iter__(self):
        """
        Iteration over the result set which calls self.fetchone()
        and returns the next row.
        """
        return iter(self.fetchone, None)
    
    def _reset_result(self):
        self.result = []
        self.nextrow = 0
        self._warning_count = 0
        
    def next(self):
        """
        Used for iterating over the result set. Calles self.fetchone()
        to get the next row.
        """
        row = self.fetchone()
        if not row:
            raise StopIteration
        return row
    
    def _get_db(self):
        """
        Get the MySQLConnection object.
        """
        if not self.db:
            raise errors.ProgrammingError, 'Cursor closed.'
        return self.db

    def close(self):
        """
        Close the cursor, disconnecting it from the MySQLConnection object.
        """
        try:
            if self.db is None:
                return

            self.db.remove_cursor(self)
            self.db = None
        except exceptions.ReferenceError:
            pass
    
    def _process_params(self, params):
        """
        Process the parameters which were given when self.execute() was
        called. It does following using the MySQLConnection converter:
        * Convert Python types to MySQL types
        * Escapes characters required for MySQL.
        * Quote values when needed.
        
        Returns a list.
        """
        db = self._get_db()
        res = params
        res = [ db.converter.to_mysql(v) for v in res ]
        res = tuple([ db.converter.escape(v) for v in res ])
        res = tuple([ db.converter.quote(v) for v in res ]) 
        return res
    
    def _get_description(self, res):
        """
        Gets the description of the fields out of a result we got from
        the MySQL Server.
        
        Returns a list.
        """
        desc = [fld.get_description() for fld in res[1]]
        return desc

    def _make_result(self, rows, desc=None):
        """
        Gets data from all rows. The rows parameter should be a list
        of protocol.RowDataPacket objects.

        Returns a list.
        """
        db = self._get_db()
        if not desc:
            desc = self.description
        result = []
        for row in rows:
            crow = ()
            for idx,v in enumerate(row.values):
                flddsc = desc[idx]
                crow += (db.converter.to_python(flddsc, v),)             
            result.append(crow)
        return result

    def _fetch_warnings(self):
        """
        Fetch warnings doing a SHOW WARNINGS. Can be called anytime, but is
        really only used when there are actually warnings and db.get_warnings
        is set to true.

        Returns a result set or None there were no warnings.
        """
        res = None
        db = self._get_db()
        try:
            res = self.protocol.cmd_query("SHOW WARNINGS")
            desc = self._get_description(res)
            (rows, eof) = self.protocol.result_get_rows()
            if len(rows):
                res = self._make_result(rows, desc)
        except:
            raise
        return res
    
    def _handle_noresultset(self, res):
        """Handles result of execute() when there is no result set."""
        self.rowcount = res.affected_rows
        self.lastrowid = res.insert_id
        self._warning_count = res.warning_count
    
    def _handle_resultset(self, res):
        """Handles result of execute() when there is a result set."""
        self.lastrowid = None
        self.description = self._get_description(res)
        (rows, eof) = self.protocol.result_get_rows()
        self._warning_count = eof.warning_count
        if len(rows):
            self.result = self._make_result(rows)
            self.rowcount = len(self.result)
        
    def execute(self, operation, params=None):
        """
        Executes the given operation. The parameters given through params
        are used to substitute %%s in the operation string.
        For example, getting all rows where id is 5:
          cursor.execute("SELECT * FROM t1 WHERE id = %s", (5,))
        
        If warnings where generated, and db.get_warnings is True, then
        self.warnings will be a list containing these warnings.
        
        Raises exceptions when any error happens.
        """
        if params is not None and not isinstance(params, (list,tuple)):
            raise errors.ProgrammingError, 'Parameters must be given as a sequence.'
            
        db = self._get_db()
        self._warning_count, self.warnings = (0,None)
        
        self._reset_result()
        try:
            # Make sure we send the query in correct character set
            if isinstance(operation, unicode):
                operation.encode(db.charset_name)
            if params is not None:
                operation = operation % self._process_params(params)
            res = self.protocol.cmd_query(operation)
            
            if isinstance(res, protocol.OKResultPacket):
                self._handle_noresultset(res)
            else:
                self._handle_resultset(res)
            
            # We get the warnings when we're done with the actual query.
            if db.get_warnings and self._warning_count > 0:
                self.warnings = self._fetch_warnings()
        except:
            raise
        else:
            self.nextrow = 0
    
    def executemany(self, operation, seq_params):
        """Loops over seq_params and calls excute()"""
        if seq_params is not None and not isinstance(seq_params, (list,tuple)):
            raise errors.ProgrammingError, 'Parameters must be given as a sequence of sequences.'
        
        for params in seq_params:
            try:
                self.execute(operation, params)
            except:
                raise
    
    def callproc(self, procname, args=()):
        """Calls a stored procedue with the given arguments
        
        The arguments will be set during this session, meaning
        they will be called like  _<procname>__arg<nr> where
        <nr> is an enumeration (+1) of the arguments.
        
        Example:
          CREATE PROCEDURE multiply(IN pfac1, IN pfac2, OUT pprod)
          BEGIN
            SELECT (pfac1 * pfac2) INTO pprod;
          END
          
          args = (5,5,0) # 0 is to hold pprod
          cursor.callproc(multiply, args)
          
          for row in cursor:
              print row

        Doesn't return anything, but a result set will be
        available when the call was succesful.
        Raises exceptions when something is wrong.
        """
        argfmt = "@_%s_arg%d"
        procargs = self._process_params(args)
        argnames = []
        
        for idx,arg in enumerate(procargs):
            argname = argfmt % (procname, idx+1)
            argnames.append(argname)
            setquery = "SET %s=%%s" % argname
            self.execute(setquery, (arg,))
        
        call = "CALL %s(%s)" % (procname,','.join(argnames))
        try:
            res = self.protocol.cmd_query(call)
        except:
            raise
            
        select = "SELECT %s" % ','.join(argnames)
        self.execute(select)
        
    def fetchone(self):
        if len(self.result) == 0:
            return None
        if self.nextrow >= self.rowcount:
            return None
        
        res = self.result[self.nextrow]
        self.nextrow += 1
        return res          
    
    def fetchmany(self, size=None):
        if len(self.result) == 0:
            return []
        res = self.result[(self.nextrow):(size or self.arraysize)]
        self.nextrow += size - 1
        return res
        
    def fetchall(self):
        return self.result
