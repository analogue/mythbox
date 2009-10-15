#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append('../')

import mysql.connector
from config import Config

"""

Example using MySQL Connector/Python showing:
* that show engines works..

"""

if __name__ == '__main__':
    #
    # Configure MySQL login and database to use in config.py
    #
    db = mysql.connector.Connect(**Config.dbinfo())
    cursor = db.cursor()
    
    # Select it again and show it
    stmt_select = "SHOW ENGINES"
    cursor.execute(stmt_select)
    rows = cursor.fetchall()

    for row in rows:
        print row

    db.close()
