#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import unittest
import tests

from optparse import OptionParser

def get_test_names():
    return [ s.replace('tests.test_','') for s in tests.active_testcases]

def add_options(p):
    p.add_option('-H','--host', dest='hostname', metavar='NAME',
        help='Connect to MySQL running on host.')
    p.add_option('-S','--socket', dest='unix_socket', metavar='FILE',
        help='Socket file to use for connecting to MySQL.'
        )
    p.add_option('-u','--user', dest='username', metavar='NAME',
        help='User for login if not current user.')
    p.add_option('-p','--password', dest='password', metavar='PASSWORD',
        help='Password to use when connecting to server.')
    p.add_option('-D','--database', dest='database', metavar='NAME',
        help='Database to use.')
    
    p.add_option('-t','--test', dest='testcase', metavar='NAME',
        help='Tests to execute, one of %s' % get_test_names())

def set_config(options):
    if options.hostname:
        tests.MYSQL_CONFIG['host'] = options.hostname
    if options.unix_socket:
        tests.MYSQL_CONFIG['unix_socket'] = options.unix_socket
    if options.username:
        tests.MYSQL_CONFIG['user'] = options.username
    if options.password:
        tests.MYSQL_CONFIG['password'] = options.password
    if options.database:
        tests.MYSQL_CONFIG['database'] = options.database
    
if __name__ == '__main__':
    usage = 'usage: %prog [options]'
    parser = OptionParser()
    add_options(parser)
    
    (options, args) = parser.parse_args()
    set_config(options)
    
    if options.testcase is not None:
        if options.testcase in get_test_names():
            testcases = [ 'tests.test_%s' % options.testcase ]
        else:
            print "Test case is not one of %s" % get_test_names()
            parser.print_help()
            sys.exit(1)
    else:
        testcases = tests.active_testcases
        
    suite = unittest.TestLoader().loadTestsFromNames(testcases)
    unittest.TextTestRunner(verbosity=2).run(suite)

