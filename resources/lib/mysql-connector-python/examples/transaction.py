#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append('../')

import mysql.connector
from config import Config

"""

Example using MySQL Connector/Python showing:
* dropping and creating a table
* using warnings
* doing a transaction, rolling it back and committing one.

"""

if __name__ == '__main__':
    #
    # Configure MySQL login and database to use in config.py
    #
    db = mysql.connector.Connect(**Config.dbinfo())
    cursor = db.cursor()
    
    # Drop table if exists, and create it new
    stmt_drop = "DROP TABLE IF EXISTS names"
    cursor.execute(stmt_drop)
    
    stmt_create = """
    CREATE TABLE names (
        id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name VARCHAR(30) DEFAULT '' NOT NULL,
        cnt TINYINT UNSIGNED DEFAULT 0,
        PRIMARY KEY (id)
    ) ENGINE=InnoDB"""
    cursor.execute(stmt_create)
    
    if cursor.warnings:
        ids = [ i for l,i,m in cursor.warnings]
        print "Oh oh.. we got warnings.."
        if 1266L in ids:
            print """
            Table was created as MYISAM, no transaction support.
            
            Bailing out, no use to continue. Make sure InnoDB is available!
            """
            db.close()
            sys.exit(1)

    # Insert 3 records
    print "Inserting data"
    names = ( ('Geert',), ('Jan',), ('Michel',) )
    stmt_insert = "INSERT INTO names (name) VALUES (%s)"
    cursor.executemany(stmt_insert, names)
    
    # Roll back!!!!
    print "Rolling back transaction"
    db.rollback()

    # There should be no data!
    stmt_select = "SELECT id, name FROM names ORDER BY id"
    cursor.execute(stmt_select)
    rows = cursor.fetchall()
    
    if len(rows):
        print "Something is wrong, we have data although we rolled back!"
        print rows
    else:
        print "No data, all is fine."
    
    # Do the insert again.
    cursor.executemany(stmt_insert, names)

    # Data should be already there
    cursor.execute(stmt_select)
    print "Data before commit:"
    for row in cursor.fetchall():
        print "%d | %s" % (row[0], row[1])
    
    # Do a commit
    db.commit()
    
    cursor.execute(stmt_select)
    print "Data after commit:"
    for row in cursor.fetchall():
        print "%d | %s" % (row[0], row[1])
    	
    # Cleaning up, dropping the table again
    cursor.execute(stmt_drop)

    db.close()
