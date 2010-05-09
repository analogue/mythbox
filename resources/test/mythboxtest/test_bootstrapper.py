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

from mythbox.bootstrapper import LogSettingsListener

log = logging.getLogger('mythbox.unittest')

# =============================================================================
class LogSettingsListenerTest(unittest.TestCase):

    def test_settingChanged(self):
        listener = LogSettingsListener()
        
        listener.settingChanged('logging_enabled', 'True', 'False')
        log.debug('I should not see this log message')
        self.assertEquals(logging.WARN, logging.getLogger('mythbox.perf').getEffectiveLevel())
        
        listener.settingChanged('logging_enabled', 'False', 'True')
        log.debug('I should see this log message')
        self.assertEquals(logging.DEBUG, logging.getLogger('mythbox.perf').getEffectiveLevel())
        
# =============================================================================
if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
