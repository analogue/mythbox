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
# Check Python version 2.3 or higher
import sys
if not hasattr(sys, "version_info") or sys.version_info < (2,3):
    raise RuntimeError("MySQL Connector/Python requires Python 2.3 or higher.")
del sys

# Python Db API v2
apilevel = '2.0'
threadsafety = 1
paramstyle = 'pyformat'

# Read the version from an generated file
import _version
__version__ = _version.version

from mysql import MySQL
from errors import *
from constants import FieldFlag, FieldType, CharacterSet, RefreshOption
from dbapi import *

def Connect(*args, **kwargs):
    """Shortcut for creating a mysql.MySQL object."""
    return MySQL(*args, **kwargs)
connect = Connect

__all__ = [
    'MySQL', 'Connect',
    
    # Some useful constants
    'FieldType','FieldFlag','CharacterSet','RefreshOption',

    # Error handling
    'Error','Warning',
    'InterfaceError','DatabaseError',
    'NotSupportedError','DataError','IntegrityError','ProgrammingError',
    'OperationalError','InternalError',
    
    # DBAPI PEP 249 required exports
    'connect','apilevel','threadsafety','paramstyle',
    'Date', 'Time', 'Timestamp', 'Binary',
    'DateFromTicks', 'DateFromTicks', 'TimestampFromTicks',
    'STRING', 'BINARY', 'NUMBER',
    'DATETIME', 'ROWID',
    ]
