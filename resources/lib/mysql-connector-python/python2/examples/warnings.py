#!/usr/bin/env python
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

import sys, os

import mysql.connector

"""

Example using MySQL Connector/Python showing:
* using warnings

"""

STMT = "SELECT 'abc'+1"

def main(config):
    output = []
    config['get_warnings'] = True
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    cursor.sql_mode = ''
    
    output.append("Executing '%s'" % STMT)
    cursor.execute(STMT)
    cursor.fetchall()
    
    warnings = cursor.fetchwarnings()
    if warnings:
        for w in warnings:
            output.append("%d: %s" % (w[1],w[2]))
    else:
        raise StandardError("Got no warnings")

    cursor.close()
    db.close()
    return output
    
if __name__ == '__main__':
    #
    # Configure MySQL login and database to use in config.py
    #
    from config import Config
    config = Config.dbinfo().copy()
    out = main(config)
    print '\n'.join(out)