#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2011 analogue@yahoo.com
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import unittest

import mythboxtest.test_platform
import mythboxtest.test_util
import mythboxtest.test_log
import mythboxtest.mythtv.test_db
import mythboxtest.mythtv.test_conn
import mythboxtest.mythtv.test_inject_conn
import mythboxtest.mythtv.test_domain
import mythboxtest.mythtv.test_publish
import mythboxtest.ui.test_player
import mythboxtest.test_pool
import mythboxtest.test_threadlocal
import mythboxtest.test_updater
import mythboxtest.test_filecache
import mythboxtest.test_fanart
import mythboxtest.ui.test_toolkit
import mythboxtest.ui.test_upcoming
import mythboxtest.ui.test_tvguide
import mythboxtest.ui.test_recordings
import mythboxtest.test_bootstrapper
import mythboxtest.test_feeds
import mythboxtest.test_settings
import mythboxtest.test_advanced
import mythboxtest.mythtv.test_resolver

def suite():
    mysuite = unittest.TestSuite()
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_platform))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_util))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_log))
    mysuite.addTest(unittest.findTestCases(mythboxtest.mythtv.test_db))
    mysuite.addTest(unittest.findTestCases(mythboxtest.mythtv.test_conn))
    mysuite.addTest(unittest.findTestCases(mythboxtest.mythtv.test_inject_conn))
    mysuite.addTest(unittest.findTestCases(mythboxtest.mythtv.test_publish))
    #import test_domain
    mysuite.addTest(unittest.findTestCases(mythboxtest.mythtv.test_domain))
    mysuite.addTest(unittest.findTestCases(mythboxtest.ui.test_player))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_pool))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_threadlocal))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_updater))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_filecache))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_fanart))
    mysuite.addTest(unittest.findTestCases(mythboxtest.ui.test_toolkit))
    mysuite.addTest(unittest.findTestCases(mythboxtest.ui.test_upcoming))
    mysuite.addTest(unittest.findTestCases(mythboxtest.ui.test_tvguide))
    mysuite.addTest(unittest.findTestCases(mythboxtest.ui.test_recordings))    
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_bootstrapper))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_feeds))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_settings))
    mysuite.addTest(unittest.findTestCases(mythboxtest.test_advanced))
    mysuite.addTest(unittest.findTestCases(mythboxtest.mythtv.test_resolver))
    return mysuite

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    testSuite = suite()

    #rc = unittest.TextTestRunner(verbosity = 3).run(testSuite)
    
    import HTMLTestRunner 
    fp = file('mythbox_report.html', 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp, verbosity=3, title='MythBox Unit Test Results')
    rc = runner.run(testSuite)
    
    print('runtests rc = %s' % rc.wasSuccessful())
    import sys
    sys.exit(not rc.wasSuccessful())
    