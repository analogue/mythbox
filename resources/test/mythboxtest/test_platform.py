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
import logging
import unittest

from mythbox.platform import getPlatform

log = logging.getLogger('mythtv.unittest')

# =============================================================================
class PlatformTest(unittest.TestCase):

    def test_getScriptDirNotNull(self):
        platform = getPlatform()
        self.assertTrue(platform.getScriptDir() is not None)
        
    def test_getScriptDataDirNotNull(self):
        platform = getPlatform()
        self.assertTrue(platform.getScriptDataDir() is not None)
        
    def test_getHostname(self):
        platform = getPlatform()
        hostname = platform.getHostname()
        self.assertTrue(hostname is not None)

    def test__str__NotNull(self):
        platform = getPlatform()
        s = "%s" % platform
        log.debug('\n%s' % platform)
        self.assertTrue(s is not None)
        
    def test_getPlatform(self):
        platform = getPlatform()
        log.debug('Platform type = %s' % type(platform))
        self.assertTrue(platform is not None)

    def test_getPlatform_SameInstance(self):
        platform1 = getPlatform()
        platform2 = getPlatform()
        self.assertTrue(platform1 == platform2)
        
# =============================================================================
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
