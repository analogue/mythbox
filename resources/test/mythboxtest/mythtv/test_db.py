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
import mythbox.mythtv.protocol as protocol
import time
import unittest2 as unittest
import util_mock
import mythboxtest

from mockito import Mock
from mythbox.mythtv.db import MythDatabase
from mythbox.mythtv.domain import RecordedProgram
from mythbox.platform import Platform
from mythbox.settings import MythSettings
from mythbox.util import OnDemandConfig
from mockito.mockito import when

log = mythboxtest.getLogger('mythbox.unittest')


class MythDatabaseTest(unittest.TestCase):

    def setUp(self):
        self.platform = Platform()
        self.langInfo = util_mock.XBMCLangInfo(self.platform)
        self.translator = util_mock.Translator(self.platform, self.langInfo)
        self.settings = MythSettings(self.platform, self.translator)
        self.protocol = protocol.Protocol56()
        privateConfig = OnDemandConfig()
        self.settings.put('mysql_host', privateConfig.get('mysql_host'))
        self.settings.put('mysql_port', privateConfig.get('mysql_port'))
        self.settings.put('mysql_database', privateConfig.get('mysql_database'))
        self.settings.put('mysql_user', privateConfig.get('mysql_user'))  
        self.settings.put('mysql_password', privateConfig.get('mysql_password'))
        self.domainCache = Mock()
        self.db = MythDatabase(self.settings, self.translator, self.domainCache)

    def tearDown(self):
        try:
            self.db.close()
        except:
            pass
        
    def test_constructor(self):
        self.assertTrue(self.db)

    def test_toBackend(self):
        master = self.db.getMasterBackend()
        self.assertEqual(master, self.db.toBackend(master.hostname))
        self.assertEqual(master, self.db.toBackend(master.ipAddress))
        self.assertTrue(master,   self.db.toBackend('bogus'))
        self.assertEqual(master, self.db.toBackend(master.hostname.upper()))
        self.assertEqual(master, self.db.toBackend(master.hostname.lower()))
        
    def test_getBackends(self):
        bes = self.db.getBackends()
        self.assertTrue(len(bes) >= 1)
        
    def test_getMasterBackend(self):
        mbe = self.db.getMasterBackend()
        log.debug(mbe)        
        self.assertTrue(mbe.hostname)
        self.assertTrue(mbe.ipAddress)
        self.assertTrue(mbe.port)
        self.assertTrue(mbe.master)
        self.assertFalse(mbe.slave)
    
    def test_getSlaveBackends(self):
        slaves = self.db.getSlaveBackends()
        for slave in slaves:
            log.debug(slave)
            self.assertFalse(slave.master)
            self.assertTrue(slave.slave)
        
    def test_getChannels(self):
        channels = self.db.getChannels()
        for i, channel in enumerate(channels):
            log.debug("%d - %s"%(i+1, channel))
            self.assertTrue('Expected int but was %s' % type(channel.getChannelId()), isinstance(channel.getChannelId(), int))
            self.assertTrue('Expected str but was %s' % type(channel.getChannelNumber()), isinstance(channel.getChannelNumber(), str))
            self.assertTrue('Expected str but was %s' % type(channel.getCallSign()), isinstance(channel.getCallSign(), str))
            self.assertTrue('Expected str but was %s' % type(channel.getChannelName()), isinstance(channel.getChannelName(), str))
            self.assertTrue('Expected str but was %s' % type(channel.getIconPath()), isinstance(channel.getIconPath(), str))
            self.assertTrue('Expected int but was %s' % type(channel.getTunerId()), isinstance(channel.getTunerId(), int))

    def test_getRecordingProfileNames(self):
        self.assertTrue(self.db.getRecordingProfileNames())
                
    def test_getRecordingGroups(self):
        groups = self.db.getRecordingGroups()
        self.assertTrue('Default' in groups)

    def test_getRecordingTitles_InAllGroups(self):
        titles = self.db.getRecordingTitles('All Groups')
        self.assertTrue(len(titles) > 0)
        total = titles[0][1]
        for i, title in enumerate(titles):
            titleName = title[0]
            titleCount = title[1]
            log.debug('%d - %s x %s' %(i+1, titleCount, titleName))

    def test_getRecordingTitles_ForNonExistantRecordingGroupReturnsAllShowsWithCountOfZero(self):
        titles = self.db.getRecordingTitles('bogus group')
        self.assertEquals(1, len(titles))
        self.assertEquals('All Shows', titles[0][0])
        self.assertEquals(0, titles[0][1])

    def test_getRecordingTitles_ForDeletedRecordingsGroup(self):
        deleted = self.db.getRecordingTitles('Deleted')
        for i, title in enumerate(deleted):
            titleName = title[0]
            titleCount = title[1]
            log.debug('%d - Deleted recording %s recorded %s times' % (i+1, titleName, titleCount))
        self.assertTrue(len(deleted) > 0)

    def test_getTuners(self):
        tuners = self.db.getTuners()
        self.assertTrue(len(tuners) > 0, 'No tuners found')
        for i, tuner in enumerate(tuners):
            log.debug('%d - %s' %(i+1, tuner))
            self.assertIsNotNone(tuner.tunerId)
            self.assertIsNotNone(tuner.hostname)
            self.assertIsNotNone(tuner.signalTimeout)
            self.assertIsNotNone(tuner.channelTimeout)
            self.assertIsNotNone(tuner.domainCache)
            
    def test_getMythSetting_KeyOnly_Found(self):
        s = self.db.getMythSetting('mythfilldatabaseLastRunStatus')
        log.debug('mythfillstatus = %s' % s)
        self.assertFalse(s is None)

    def test_getMythSetting_KeyOnly_NotFound(self):
        s = self.db.getMythSetting('blahblah')
        self.assertTrue(s is None)

    def test_getMythSetting_KeyWithHostname_Found(self):
        # TODO
        pass

    def test_getMythSetting_KeyWithHostname_NotFound(self):
        s = self.db.getMythSetting('blahblah', 'foobar')
        self.assertTrue(s is None)
    
    def test_getRecordingSchedules_All(self):
        schedules = self.db.getRecordingSchedules()
        for i, s in enumerate(schedules):
            log.debug('%d - %s' % (i+1, s))
        self.assertTrue(schedules)
        
    def test_getRecordingSchedules_By_Channel(self):
        # TODO
        pass
    
    def test_getRecordingSchedules_By_ScheduleId(self):
        # Setup
        schedules = self.db.getRecordingSchedules()
        if len(schedules) == 0:
            self.fail('Need schedules to run test')
        expectedSchedule = schedules.pop()
        
        # Test
        actualSchedules = self.db.getRecordingSchedules(scheduleId=expectedSchedule.getScheduleId())
        
        # Verify
        self.assertEquals(1, len(actualSchedules))
        self.assertEquals(expectedSchedule.getScheduleId(), actualSchedules.pop().getScheduleId())

    def test_getJobs_All(self):
        when(self.domainCache).getUserJobs().thenReturn(self.db.getUserJobs())
        jobs = self.db.getJobs()
        self.assertTrue(jobs is not None)
        for index, job in enumerate(jobs):
            log.debug('job %d = %s' % (index, job))
            
    def test_getJobs_ForProgram(self):
        # Setup
        when(self.domainCache).getUserJobs().thenReturn(self.db.getUserJobs())
        jobs = self.db.getJobs()
        if len(jobs) == 0:
            log.warn('No jobs in database to test with. Test skipped...')
            return 
        job = jobs[-1]  # last job
        data = [''] * self.protocol.recordSize()
        data[4]  = job.channelId
        data[11] = time.mktime(job.startTime.timetuple()) 
        program = RecordedProgram(data=data, settings=Mock(), translator=Mock(), platform=Mock(), protocol=self.protocol, conn=Mock())
    
        # Test
        jobs = self.db.getJobs(program=program)
    
        # Verify
        self.assertTrue(len(jobs) > 0)
        for index, actual in enumerate(jobs):
            log.debug('job %d = %s' % (index, actual))
            self.assertEquals(job.channelId, actual.channelId)
            self.assertEquals(job.startTime, actual.startTime)

    def test_getJobs_ByJobType(self):
        # Setup
        when(self.domainCache).getUserJobs().thenReturn(self.db.getUserJobs())
        jobs = self.db.getJobs()
        if len(jobs) == 0:
            log.warn('No jobs in database to test with. Test skipped...')
            return
        job = jobs[0]
    
        # Test
        jobs = self.db.getJobs(jobType=job.jobType)
    
        # Verify
        self.assertTrue(len(jobs) > 0)
        for index, j2 in enumerate(jobs):
            log.debug('job %d = %s' % (index, j2))
            self.assertEquals(job.jobType, j2.jobType)
        
    def test_getJobs_ForProgram_ByJobType(self):
        # Setup
        when(self.domainCache).getUserJobs().thenReturn(self.db.getUserJobs())
        jobs = self.db.getJobs()
        if len(jobs) == 0:
            log.warn('No jobs in database to test with. Test skipped...')
            return 
        job = jobs[-1] # last job
        data = [''] * self.protocol.recordSize()
        data[4]  = job.channelId
        data[11] = time.mktime(job.startTime.timetuple()) 
        program = RecordedProgram(data=data, settings=Mock(), translator=Mock(), platform=Mock(), protocol=self.protocol, conn=Mock())
    
        # Test
        jobs = self.db.getJobs(program=program, jobType=job.jobType)
    
        # Verify
        self.assertTrue(len(jobs) > 0)
        for index, actual in enumerate(jobs):
            log.debug('job %d = %s' % (index, actual))
            self.assertEquals(job.channelId, actual.channelId)
            self.assertEquals(job.startTime, actual.startTime)
            self.assertEquals(job.jobType, actual.jobType)
            
    def test_getUserJobs(self):
        userJobs = self.db.getUserJobs()
        for j in userJobs:
            log.debug(j)
        self.assertEqual(4, len(userJobs))

    def test_getTVGuideDataFlattened(self):
        # TODO: Convert to mocks w/ assertions
        channels = self.db.getChannels()[:2]
        programs = self.db.getTVGuideDataFlattened(
            datetime.datetime.now(), 
            datetime.datetime.now() + datetime.timedelta(hours=4), 
            channels)
        
        for p in programs:
            log.debug(p)
            
    def test_getFramerate(self):
        from mythbox.mythtv.conn import Connection
        from mythbox.util import safe_str
        from mythbox.mythtv.enums import RecordingStatus
        
        conn = Connection(settings=self.settings, translator=Mock(), platform=Mock(), bus=Mock(), db=self.db)
        try:
            recordings = conn.getAllRecordings()[-10:]
            for r in recordings:
                if r.isCommFlagged() and r.getRecordingStatus() == RecordingStatus.RECORDED:
                    fps  = self.db.getFramerate(r)
                    log.debug('%s - %s - %s %d' % (safe_str(r.title()), safe_str(r.subtitle()), fps, r.getRecordingStatus()))
                    self.assertGreaterEqual(fps, 0.0, fps)
        finally:
            conn.close()
            