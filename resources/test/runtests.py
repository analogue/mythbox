#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
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

import test_fanart
import test_filecache
import test_mythdb
import test_mythtv
import test_platform
import test_player
import test_pool
import test_threadlocal
import test_ui
import test_util
import test_upcoming
import test_updater
import unittest

def suite():
    mysuite = unittest.TestSuite()
    mysuite.addTest(unittest.findTestCases(test_platform))
    mysuite.addTest(unittest.findTestCases(test_util))
    mysuite.addTest(unittest.findTestCases(test_mythdb))
    mysuite.addTest(unittest.findTestCases(test_mythtv))
    import test_domain
    mysuite.addTest(unittest.findTestCases(test_domain))
    mysuite.addTest(unittest.findTestCases(test_player))
    mysuite.addTest(unittest.findTestCases(test_pool))
    mysuite.addTest(unittest.findTestCases(test_threadlocal))
    mysuite.addTest(unittest.findTestCases(test_updater))
    mysuite.addTest(unittest.findTestCases(test_filecache))
    mysuite.addTest(unittest.findTestCases(test_fanart))
    mysuite.addTest(unittest.findTestCases(test_ui))
    mysuite.addTest(unittest.findTestCases(test_upcoming))
    return mysuite

if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    testSuite = suite()
    rc = unittest.TextTestRunner(verbosity = 3).run(testSuite)
    print('runtests rc = %s' % rc.wasSuccessful())
    if not rc.wasSuccessful():
        import sys
        sys.exit(1)
