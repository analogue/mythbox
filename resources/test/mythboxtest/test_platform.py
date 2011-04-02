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
import mythboxtest
import unittest2 as unittest

from mythbox.platform import getPlatform

log = mythboxtest.getLogger('mythbox.unittest')

class PlatformTest(unittest.TestCase):

    def test_getScriptDirNotNull(self):
        platform = getPlatform()
        self.assertIsNotNone(platform.getScriptDir())
        
    def test_getScriptDataDirNotNull(self):
        platform = getPlatform()
        self.assertIsNotNone(platform.getScriptDataDir())
        
    def test_getHostname(self):
        platform = getPlatform()
        hostname = platform.getHostname()
        self.assertIsNotNone(hostname)

    def test__str__NotNull(self):
        platform = getPlatform()
        s = "%s" % platform
        log.debug('\n%s' % platform)
        self.assertIsNotNone(s)
        
    def test_getPlatform(self):
        platform = getPlatform()
        log.debug('Platform type = %s' % type(platform))
        self.assertIsNotNone(platform)

    def test_getPlatform_SameInstance(self):
        platform1 = getPlatform()
        platform2 = getPlatform()
        self.assertTrue(platform1 == platform2)

    def test_getUserDataDir(self):
        self.assertIsNotNone(getPlatform().getUserDataDir())
