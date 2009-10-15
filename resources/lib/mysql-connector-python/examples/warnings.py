#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append('../')

import mysql.connector
from config import Config

"""

Example using MySQL Connector/Python showing:
* using warnings

"""

if __name__ == '__main__':
    #
    # Configure MySQL login and database to use in config.py
    #
    db = mysql.connector.Connect(**Config.dbinfo())
    cursor = db.cursor()
    
    stmt_select = "SELECT 'abc'+1"
    
    print "Remove all sql modes.."
    cursor.execute("SET sql_mode = ''") # Make sure we don't have strict on
    
    print "Execute '%s'" % stmt_select
    cursor.execute(stmt_select)
    
    if cursor.warnings:
        print cursor.warnings
    else:
        print "We should have got warnings."

    db.close()
