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
import datetime
import logging
import unittest
import mythboxtest
import util_mock
import unittest2 as unittest

from mockito import Mock
from mythbox.mythtv.db import MythDatabase
from mythbox.mythtv.domain import RecordingSchedule, Job
from mythbox.platform import Platform
from mythbox.settings import MythSettings
from mythbox.util import OnDemandConfig
from mythbox.mythtv.conn import Connection
from mythbox.mythtv.enums import JobType

log = mythboxtest.getLogger('mythbox.unittest')

class MythDatabaseTest(unittest.TestCase):

    def setUp(self):
        self.platform = Platform()

        #self.translator = Mock()
        self.langInfo = util_mock.XBMCLangInfo(self.platform)
        self.translator = util_mock.Translator(self.platform, self.langInfo)

        self.bus = Mock()
        self.domainCache = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        
        privateConfig = OnDemandConfig()
        self.settings.put('mysql_host', privateConfig.get('mysql_host'))
        self.settings.put('mysql_database', privateConfig.get('mysql_database'))
        self.settings.put('mysql_password', privateConfig.get('mysql_password'))
        
        self.db = MythDatabase(self.settings, self.translator, self.domainCache)
        self.conn = Connection(self.settings, self.translator, self.platform, self.bus, self.db)
    
    def tearDown(self):
        #self.db.close()
        self.conn.close()
        
    def test_saveSchedule_NewSchedule(self):
        now = datetime.datetime.now()
        programs = self.db.getTVGuideDataFlattened(now, now, self.db.getChannels())
        if len(programs) == 0:
            log.warn('Cannot run unit tests without program listings in the database')
            return
            
        schedule = RecordingSchedule.fromProgram(programs[0], self.translator)
        log.debug('Test schedule = %s' % schedule)
        result = self.db.saveSchedule(schedule)
        log.debug('Save schedule result = %s' % result)
        
    def test_addJob_UserJob1(self):
        recordings = self.conn.getAllRecordings()
        if not recordings:
            log.warn('Cannot run unit tests without program listings in the database')
            return

        job = Job.fromProgram(recordings[-1], JobType.USERJOB & JobType.USERJOB1)
        log.debug(job)

        self.assertIsNone(job.id)
        self.db.addJob(job)
        log.debug(job)
        self.assertIsNotNone(job.id)
        
if __name__ == '__main__':
    unittest.main()        