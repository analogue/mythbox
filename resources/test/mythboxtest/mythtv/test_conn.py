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
import os
import tempfile
import unittest2 as unittest

from mockito import Mock
from mythbox.bus import EventBus
from mythbox.mythtv.enums import Upcoming
from mythbox.mythtv.conn import Connection, EventConnection, createChainId, ServerException, encodeLongLong, decodeLongLong
from mythbox.mythtv.db import MythDatabase
from mythbox.mythtv.protocol import ProtocolException
from mythbox.platform import getPlatform
from mythbox.settings import MythSettings
from mythbox.util import OnDemandConfig

log = logging.getLogger('mythbox.unittest')

class FunctionsTest(unittest.TestCase):
    
    def test_createChainId(self):
        chainId = createChainId()
        log.debug('Chain Id = %s' % chainId)
        self.assertTrue(chainId is not None) 

    def test_decodeLongLong(self):
        self.assertEquals(0, decodeLongLong(0, 0))
        self.assertEquals(1, decodeLongLong(1, 0))
        self.assertEquals(0xffffffff00000001, decodeLongLong(1, 0xffffffff))
        self.assertEquals(0x00000000ffffffff, decodeLongLong(0xffffffff, 0x0))
        self.assertEquals(0xffffffff00000000, decodeLongLong(0x0, 0xffffffff))
        self.assertEquals(0xffffffffffffffff, decodeLongLong(0xffffffff, 0xffffffff))
    
    def test_encodeLongLong(self):
        lowWord, highWord = encodeLongLong(0L)
        self.assertEquals(0, lowWord)
        self.assertEquals(0, highWord)

        lowWord, highWord = encodeLongLong(1L)
        self.assertEquals(1, lowWord)
        self.assertEquals(0, highWord)
        
        lowWord, highWord = encodeLongLong(0xffffffff00000001)
        self.assertEquals(1, lowWord)
        self.assertEquals(0xffffffff, highWord)

        lowWord, highWord = encodeLongLong(0x00000000ffffffff)
        self.assertEquals(0xffffffff, lowWord)
        self.assertEquals(0x0, highWord)

        lowWord, highWord = encodeLongLong(0xffffffffffffffff)
        self.assertEquals(0xffffffff, lowWord)
        self.assertEquals(0xffffffff, highWord)


class ConnectionTest(unittest.TestCase):

    def setUp(self):
        self.platform = getPlatform()
        self.translator = Mock()
        self.domainCache = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        self.settings.put('streaming_enabled', 'False')
        
        privateConfig = OnDemandConfig()
        self.settings.put('mysql_host', privateConfig.get('mysql_host'))
        self.settings.put('mysql_port', privateConfig.get('mysql_port'))
        self.settings.setMySqlDatabase(privateConfig.get('mysql_database'))
        self.settings.setMySqlUser(privateConfig.get('mysql_user'))  
        self.settings.put('mysql_password', privateConfig.get('mysql_password'))
        self.settings.put('paths_recordedprefix', privateConfig.get('paths_recordedprefix'))
        
        self.db = MythDatabase(self.settings, self.translator, self.domainCache)
        self.bus = EventBus()
        self.conn = Connection(self.settings, self.translator, self.platform, self.bus, self.db)

    def tearDown(self):
        self.conn.close()

    def test_getServerVersion(self):
        sock = self.conn.connect(announce=None)
        try:
            version = self.conn.getServerVersion()
            log.debug('Server Protcol = %s'%version)
            self.assertTrue(version > 0)
        finally:
            sock.close()

    def test_negotiateProtocol_RaisesProtocolException_When_ClientVersion_NotSupported_By_Server(self):
        sock = self.conn.connect(announce=None)
        try:
            try:
                self.conn.negotiateProtocol(sock, clientVersion=8, versionToken='')
                self.fail('Should have thrown ProtocolException')
            except ProtocolException, pe:
                log.debug('PASS: %s', pe)
        finally:
            sock.close()

    def test_getSetting(self):
        reply = self.conn.getSetting('mythfillstatus', 'none')
        log.debug('reply = %s' % reply)
        if reply[0] == "-1":
            pass # fail
        else:
            pass # success
        # TODO : Left off here!
        
    def test_getTunerStatus_Success(self):
        tuners = self.db.getTuners()
        if len(tuners) == 0:
            log.warn('SKIPPING: need tuners to run test')
            return 
        status = self.conn.getTunerStatus(tuners.pop())
        log.debug('Tuner status = %s' % status)
        self.assertFalse(status is None)

    def test_getDiskUsage(self):
        du = self.conn.getDiskUsage()
        log.debug('Disk usage = %s' % du)
        self.assertTrue(du['hostname'] is not None)
        self.assertTrue(du['dir'] is not None)
        self.assertTrue(du['total'] is not None)
        self.assertTrue(du['used'] is not None)
        self.assertTrue(du['free'] is not None)
        
    def test_getLoad(self):
        load = self.conn.getLoad()
        log.debug('CPU Load = %s' % load)
        self.assertEquals(3, len(load))
        self.assertTrue(load['1'])
        self.assertTrue(load['5'])
        self.assertTrue(load['15'])

    def test_getUptime(self):
        uptime = self.conn.getUptime()
        log.debug('Uptime = %s' % uptime)
        self.assertFalse(uptime is None)
        
    def test_getGuideDataStatus(self):
        guideStatus = self.conn.getGuideDataStatus()
        log.debug('Guide data status = %s' % guideStatus)
        self.assertFalse(guideStatus is None)

    def test_getAllRecordings(self):
        recordings = self.conn.getAllRecordings()
        log.debug('Num Recordings = %s' % len(recordings))
        self.assertTrue(len(recordings) > 0)

    def test_getRecordings_AllRecordingGroupsAndTitles(self):
        recordings = self.conn.getRecordings()
        log.debug('Num Recordings = %s' % len(recordings))
        for i, r in enumerate(recordings):
            log.debug('%d - %s' %(i+1, r))
        self.assertTrue(len(recordings) > 0)

    def test_getRecording_Found(self):
        expected = self.getRecordings().pop()
        actual = self.conn.getRecording(expected.getChannelId(), expected.recstarttime())
        self.assertEquals(expected, actual)
        
    def test_getRecording_NotFound(self):
        recording = self.getRecordings().pop()
        actual = self.conn.getRecording(32, recording.recstarttime())
        self.assertTrue(actual is None)
  
    def test_getUpcomingRecordings_When_no_args_Then_returns_only_programs_that_will_be_recorded(self):
        upcoming = self.conn.getUpcomingRecordings()
        log.debug('Num upcoming recordings = %d' % (len(upcoming)))
        for i,program in enumerate(upcoming):
            log.debug('%d: tuner=%s %s' % (i, program.getTunerId(), program))
            #program.dumpData()
            
        for program in upcoming:
            self.assertTrue(program.getRecordingStatus() in Upcoming.SCHEDULED)
            self.assertTrue(program.getTunerId() >= 0)
            
    def test_getUpcomingRecordings_When_filter_is_scheduled_Then_returns_only_program_that_will_be_recorded(self):
        upcoming = self.conn.getUpcomingRecordings(Upcoming.SCHEDULED)
        log.debug('Num upcoming recordings (filter = Upcoming.SCHEDULED) = %d' % (len(upcoming)))
        for program in upcoming:
            self.assertTrue(program.getRecordingStatus() in Upcoming.SCHEDULED)

    def test_getUpcomingRecordings_When_filter_is_conflict_Then_returns_only_program_that_will_not_be_recorded_because_of_a_conflict(self):
        upcoming = self.conn.getUpcomingRecordings(Upcoming.CONFLICTS)
        log.debug('Num upcoming recordings (filter = Upcoming.CONFLICTS) = %d' % (len(upcoming)))
        for program in upcoming:
            self.assertTrue(program.getRecordingStatus() in Upcoming.CONFLICTS)

    def test_getScheduledRecordings(self):
        scheduled = self.conn.getScheduledRecordings()
        log.debug('Num scheduled recordings = %d' % (len(scheduled)))
        for i,program in enumerate(scheduled):
            log.debug('%d: %s' % (i, program))
        self.assertFalse(scheduled is None)            

    def test_getTunerShowing_NoCardsAreWatchingOrRecordingThePassedInShow(self):
        tunerId = self.conn.getTunerShowing('bogusshow')
        self.assertEquals(-1, tunerId, 'Expected no encoder to be watching or recording a bogus tv show')

    def test_getTunerShowing_ReturnCardThatShowIsBeingWatchedOn(self):
        log.warn("TODO: Write unit test - mockito")

    def test_getTunerShowing_ReturnCardThatShowIsBeingWatchedAndRecordedOn(self):
        log.warn("TODO: Write unit test - mockito")

    def test_getFreeTuner(self):
        tunerId, hostname, port = self.conn.getFreeTuner()
        if tunerId == -1:
            log.debug('No free tuners available')
            self.assertEquals('', hostname)
            self.assertEquals(-1, port)
        else:
            log.debug('Free tuner = id: %d hostname: %s  port: %d'%(tunerId, hostname, port))
            self.assertTrue(tunerId >= 0)
            self.assertTrue(len(hostname) > 0)
            self.assertTrue(port > 0)
        
    def test_getNextFreeTuner(self):
        tunerId, hostname, port = self.conn.getNextFreeTuner(-1)
        if tunerId is None:
            pass
        else:
            log.debug('Next free tuner = id:%d hostname:%s port:%d'%(tunerId, hostname, port))
        # TODO: valid assertions when tuner free and not available
        
    def test_isOk_OKMessageReturnsTrue(self):
        self.assertTrue(self.conn._isOk(['OK']))

    def test_isOk_OKMessageWithAdditionPayloadReturnsTrue(self):
        self.assertTrue(self.conn._isOk(['OK','foo', 'bar', 'baz']))

    def test_isOk_NoneMessageReturnsFalse(self):
        self.assertFalse(self.conn._isOk(None))
        
    def test_isOk_EmptyMessageReturnsFalse(self):
        self.assertFalse(self.conn._isOk([]))

    def test_isOk_BadMessageReturnsFalse(self):
        self.assertFalse(self.conn._isOk(['Bad']))

    def test_isTunerRecording(self):
        for t in self.conn.getTuners():
            log.debug('isTunerRecording(%d) = %s' % (t.tunerId, self.conn.isTunerRecording(t)))
        
    def test_getBookmark_Success(self):
        # TODO: only check bookmarked recordings
        recording = self.getRecordings()[0]
        log.debug('Getting bookmark for %s' % recording)
        bookmark = self.conn.getBookmark(recording)
        log.debug('bookmark = %s seconds' % bookmark)
        self.assertTrue(bookmark >= 0)
    
    def test_setBookmark_Success(self):
        p = self.getRecordings().pop()
        log.debug('Setting bookmark for %s' % p)
        self.conn.setBookmark(p, 1000)
        self.assertEquals(1000, self.conn.getBookmark(p))

    def test_setBookmark_ChannelIdInvalid(self):
        p = self.getRecordings().pop()
        p.setChannelId(999)
        self.assertEquals(999, p.getChannelId())
        self.assertRaises(ServerException, self.conn.setBookmark, p, 500)
        
    def test_getCommercialBreaks(self):
        recordings = reversed(self.conn.getAllRecordings())
        foundRecordingWithCommBreaks = False
        for r in recordings:
            if r.hasCommercials():
                foundRecordingWithCommBreaks = True
                log.debug('Recording %s has comm breaks' % r)
                breaks = self.conn.getCommercialBreaks(r)
                for j, b in enumerate(breaks):
                    log.debug('    %d - comm break = %s' % (j+1, b))
                return
        if not foundRecordingWithCommBreaks:
            log.warn('Could not find any comm flagged recordings to run unit test against')
    
    def test_getNumFreeTuners(self):
        cnt = self.conn.getNumFreeTuners()
        log.debug('Num free tuners = %d' % cnt)
        self.assertTrue(cnt >= 0)
        
    def test_getTuners(self):
        tuners = self.conn.getTuners()
        for i,t in enumerate(tuners):
            log.debug('Tuner %d = %s' % (i, t.tunerType))
            self.assertTrue(t.conn != None)
       
    def test_generateThumbnail_ReturnsTrue(self):
        recording = self.getRecordings()[-1]
        log.debug('Generating thumbnail for program: %s' % recording)
        result = self.conn.generateThumbnail(recording, self.db.getMasterBackend().ipAddress)
        self.assertTrue(result)

    def test_generateThumbnail_WithSpecificSize(self):
        recording = self.getRecordings()[-1]
        log.debug('Generating thumbnail for program: %s' % recording.title())
        result = self.conn.generateThumbnail(recording, self.db.getMasterBackend().ipAddress, 1280/4, 720/4)
        log.debug(result)
        self.assertTrue(result)
         
    def test_getThumbnailCreationTime_ThumbnailExists(self):
        recording = self.getRecordings()[0]
        log.debug('Getting thumbnail creation time for: %s' % recording.title())
        dt = self.conn.getThumbnailCreationTime(recording, self.db.getMasterBackend().ipAddress)
        log.debug('datetime = %s' % dt)
        
    def test_getThumbNailCreationTime_ThumbnailDoesNotExist(self):
        # TODO
        pass
    
    def test_rescheduleNotify_Successful(self):
        schedules = self.db.getRecordingSchedules()
        self.conn.rescheduleNotify(schedules.pop())
        log.debug('reschedule notify OK')

    def test_rescheduleNotify_Does_Something_Else_When_ScheduleId_missing(self):
        """
        @todo: fixme
        """
        pass
    
    def test_transferFile_FileExistsOnBackend_Success(self):
        # Setup
        recording = self.getRecordings()[-1]
        
        if not self.conn.getThumbnailCreationTime(recording, recording.hostname()): # generate thumbnail if necessary
            log.debug('Generating thumbnail...')
            self.conn.generateThumbnail(recording, recording.hostname())
            recording = self.conn.getRecording(recording.getChannelId(), recording.recstarttime())
            
        backendPath = recording.getBareFilename()
        if self.conn.protocol.genPixMapPreviewFilename(recording) != '<EMPTY>':
            backendPath += '.640x360'
        backendPath += '.png'
        destPath = os.path.join(tempfile.gettempdir(), recording.getBareFilename() + ".png")
        
        # Test
        try:
            log.debug('Transferring file %s to %s' % (backendPath, destPath))
            result = self.conn.transferFile(backendPath, destPath, recording.hostname())
            
            # Verify
            self.assertTrue(result)
            self.assertTrue(os.path.exists(destPath))
            self.assertTrue(os.path.isfile(destPath))
            
        finally:
            try: os.remove(destPath); 
            except: pass
    
    def test_transferFile_When_file_does_not_exist_on_backend_Then_transfer_aborted(self):
        dest = tempfile.mktemp('bogusfile.mpg')
        backendPath = "myth://" + self.db.getMasterBackend().ipAddress + ":" + str(self.db.getMasterBackend().port) + "/bogusfile.mpg"
        result = self.conn.transferFile(backendPath, dest, self.db.getMasterBackend().ipAddress)
        self.assertFalse(os.path.exists(dest))
        self.assertFalse(result)

    def test_transferFile_When_partial_transfer_requested_Then_only_send_part_of_file(self):
        # Setup
        recording = self.getRecordings()[-1]
        dest = tempfile.mktemp('.mpg', 'test_partial_transfer_')
        print dest
        
        try:
            # Test
            result = self.conn.transferFile(recording.getFilename(), dest, recording.hostname(), 1024 * 1000)
            
            # Verify
            self.assertTrue(result)
            self.assertTrue(os.path.exists(dest))
            self.assertEquals(1024*1000, os.path.getsize(dest))
        finally:
            try: os.remove(dest)
            except: pass

    def getRecordings(self):
        recordings = self.conn.getRecordings()
        self.assertTrue(recordings, 'Recordings required to run this test')
        return recordings


class EventConnectionTest(unittest.TestCase):

    def setUp(self):
        self.platform = getPlatform()
        self.translator = Mock()
        self.domainCache = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        
        privateConfig = OnDemandConfig()
        self.settings.put('mysql_host', privateConfig.get('mysql_host'))
        self.settings.put('mysql_port', privateConfig.get('mysql_port'))
        self.settings.setMySqlDatabase(privateConfig.get('mysql_database'))
        self.settings.setMySqlUser(privateConfig.get('mysql_user'))  
        self.settings.put('mysql_password', privateConfig.get('mysql_password'))
        self.settings.put('paths_recordedprefix', privateConfig.get('paths_recordedprefix'))
        
        self.db = MythDatabase(self.settings, self.translator, self.domainCache)
        self.bus = EventBus()
        self.conn = EventConnection(self.settings, self.translator, self.platform, self.bus, self.db)

    def tearDown(self):
        self.conn.close()

    def test_read_a_system_event(self):
        x  = 1
        if 'MYTH_SNIFFER' in os.environ:
            x = 9999999
        for i in xrange(x):
            msg = self.conn.readEvent()
            print(msg)
            log.debug(msg)
            #self.assertEqual('BACKEND_MESSAGE', msg[0])
            #self.assertTrue(msg[1].startswith('SYSTEM_EVENT'))

            
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
