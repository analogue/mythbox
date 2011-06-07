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
import mockito
import time
import unittest

from mythbox.mythtv.conn import Connection
from mythbox.mythtv.db import MythDatabase
from mythbox.settings import MythSettings
from mythbox.ui.livetv import FileLiveTvBrain
from mythbox.util import OnDemandConfig

log = logging.getLogger('mythbox.unittest')

# =============================================================================    
class LiveTVBrainTest(unittest.TestCase):

    def setUp(self):
        translator = mockito.Mock()
        platform = mockito.Mock()
        bus = mockito.Mock()
        settings = MythSettings(platform, translator)
        privateConfig = OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_password', privateConfig.get('mysql_password'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        self.db = MythDatabase(settings, translator)
        self.conn = Connection(settings, translator, platform, bus, self.db)
        self.brain = FileLiveTvBrain(self.conn, self.db)
    
    def tearDown(self):
        self.conn.close()
        
    def test_watchLiveTV(self):
        
#        tuners = self.conn.getTuners()
#        for t in tuners:
#            if t.tunerId == 5 and t.isRecording():
#                t.stopLiveTV()
        
        channel = self.db.getChannels()[1]
        log.debug('Attempting to watch %s' % channel)
        tuner = self.brain.watchLiveTV(channel)
        log.debug("Assuming we're watching some tv...")
        
        for x in range(20):
            time.sleep(1)
            log.debug(self.brain.getLiveTVStatus())
            
        log.debug('Stopping live tv...')
        self.brain.onPlayBackStopped()
        log.debug('all done')
        
    def xxxtest_stopAllTuners(self):
        tuners = self.conn.getTuners()
        for t in tuners:
            if t.tunerId == 5:
                t.stopLiveTV()

# =============================================================================
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()