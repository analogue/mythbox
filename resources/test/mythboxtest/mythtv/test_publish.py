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
import logging
import time
import unittest

from mockito import Mock
from mythbox.bus import EventBus
from mythbox.mythtv.conn import ConnectionFactory
from mythbox.mythtv.db import MythDatabaseFactory
from mythbox.settings import MythSettings
from mythbox.util import OnDemandConfig
from mythbox.platform import getPlatform
from mythbox.mythtv.publish import MythEventPublisher
from mythbox.pool import pools, Pool

log = logging.getLogger('mythbox.unittest')


class MythEventPublisherTest(unittest.TestCase):

    def setUp(self):
        self.platform = getPlatform()
        self.translator = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        
        privateConfig = OnDemandConfig()
        self.settings.put('mysql_host', privateConfig.get('mysql_host'))
        self.settings.put('mysql_port', privateConfig.get('mysql_port'))
        self.settings.setMySqlDatabase(privateConfig.get('mysql_database'))
        self.settings.setMySqlUser(privateConfig.get('mysql_user'))  
        self.settings.put('mysql_password', privateConfig.get('mysql_password'))
        self.settings.put('paths_recordedprefix', privateConfig.get('paths_recordedprefix'))
        self.bus = EventBus()
        self.domainCache = Mock()
        pools['dbPool']   = Pool(MythDatabaseFactory(settings=self.settings, translator=self.translator, domainCache=self.domainCache))
        pools['connPool'] = Pool(ConnectionFactory(settings=self.settings, translator=self.translator, platform=self.platform, bus=self.bus))
        
    def tearDown(self):
        pools['connPool'].shutdown()
        pools['dbPool'].shutdown()

    def test_event_publisher(self):
        publisher = MythEventPublisher(settings=self.settings, translator=self.translator, platform=self.platform, bus=self.bus)
        publisher.startup()
        time.sleep(5)
        publisher.shutdown()
        
        
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
