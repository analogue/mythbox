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
import domain
import logging
import mythprotocol
import mythdb
import mythtv
import mythbox
import os
import tempfile
import time
import unittest
import util

from mockito import *
from mythtv import MythSettings
from util import SettingsException

log = logging.getLogger('mythtv.unittest')

# =============================================================================
class FunctionsTest(unittest.TestCase):
    
    def test_createChainID(self):
        id = mythtv.createChainID()
        log.debug('Chain ID = %s' % id)
        self.assertTrue(id is not None) 

# =============================================================================
class MythSettingsTest(unittest.TestCase):

    def setUp(self):
        self.translator = Mock()
        self.platform = Mock()
        when(self.platform).getDefaultRecordingsDir().thenReturn('')
        when(self.platform).getFFMpegPath().thenReturn('')

    def test_toString(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        s = MythSettings(self.platform, self.translator)
        log.debug('MythSettings = \n%s' % s)
        
    def test_constructor_NonExistentSettingsFilesLoadsDefaults(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        s = MythSettings(self.platform, self.translator)
        self.assertEquals('localhost', s.get('mysql_host'))
        self.assertEquals('3306', s.get('mysql_port'))
        self.assertEquals('mythconverg', s.get('mysql_database'))
        self.assertEquals('mythtv', s.get('mysql_user'))
        self.assertEquals('change_me', s.get('mysql_password'))

    def test_constructor_LoadExistingSettingsFile(self):
        # Setup
        settingsDir = os.path.join('resources', 'test')
        settingsFile = 'test_mythtv_settings.xml'
        when(self.platform).getScriptDataDir().thenReturn(settingsDir)
        
        # Test
        s = MythSettings(self.platform, self.translator, settingsFile)
        
        # Verify
        self.assertEquals('test_host', s.get('mysql_host'))
        self.assertEquals('9999', s.get('mysql_port'))
        self.assertEquals('test_database', s.get('mysql_database'))
        self.assertEquals('test_user', s.get('mysql_user'))
        self.assertEquals('test_password', s.get('mysql_password'))

    def test_saveSettings_LoadedDefaultsCreatesNewSettingsFile(self):
        filename = 'settings.xml'
        settingsPath = os.path.join(tempfile.gettempdir(), 'mythbox_settings_dir')
        filepath = os.path.join(settingsPath, filename)
        when(self.platform).getScriptDataDir().thenReturn(settingsPath)
        
        try:
            self.assertFalse(os.path.exists(filepath))
            s = MythSettings(self.platform, self.translator)
            s.save()
            self.assertTrue(os.path.exists(filepath))
        finally:
            try:
                os.remove(filepath)
                os.rmdir(settingsPath)
            except:
                pass
        
    def test_getRecordingDirs_SingleDirectory(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        settings.put('paths_recordedprefix', '/mnt/mythtv')
        log.debug("Recording prefix = %s" % settings.get('paths_recordedprefix'))
        dirs = settings.getRecordingDirs()
        self.assertEquals(1, len(dirs))
        self.assertEquals('/mnt/mythtv', dirs[0])

    def test_getRecordingDirs_ManyDirectories(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        settings.put('paths_recordedprefix', os.pathsep.join(['a','b', 'c']))
        log.debug("Recording prefix = %s" % settings.get('paths_recordedprefix'))
        dirs = settings.getRecordingDirs()
        self.assertEquals(3, len(dirs))
        self.assertEquals(['a','b','c'], dirs)
        
    def test_verifyMythTVHost_ValidHostname(self):
        MythSettings.verifyMythTVHost('localhost')

    def test_verifyMythTVHost_ValidIPAddress(self):
        MythSettings.verifyMythTVHost('127.0.0.1')

    def test_verifyMythTVHost_InvalidHostname(self):
        try:
            MythSettings.verifyMythTVHost('bogus host name')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyMythTVHost_InvalidIPAddress(self):
        try:
            MythSettings.verifyMythTVHost('324.23.12.23')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)
            
    def test_verifyMythTVHost_EmptyHostname(self):
        try:
            MythSettings.verifyMythTVHost('')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyMythTVHost_BlankHostname(self):
        try:
            MythSettings.verifyMythTVHost('      ')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('Error = %s' % se)
            
    def test_verifyMythTVPort_ValidPort(self):
        MythSettings.verifyMythTVPort('1001')
            
    def test_verifyMythTVPort_PortLessThanZeroRaisesSettingsException(self):
        try:
            MythSettings.verifyMythTVPort('-34')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)
            

    def test_verifyMythTVPort_PortGreaterThanMaxPortNumberRaisesSettingsException(self):
        try:
            MythSettings.verifyMythTVPort('101234')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyMythTVPort_NonNumericPortRaisesSettingsException(self):
        try:
            MythSettings.verifyMythTVPort('abc')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyMythTVPort_EmptyPortRaisesSettingsException(self):
        try:
            MythSettings.verifyMythTVPort('')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyMySQLConnectivity_OK(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        
        privateConfig = util.OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        settings.put('mysql_user', privateConfig.get('mysql_user'))
        settings.put('mysql_password', privateConfig.get('mysql_password'))
        settings.verifyMySQLConnectivity()

    def test_verifyMySQLConnectivity_InvalidUsernamePasswordThrowsSettingsException(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        privateConfig = util.OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        settings.put('mysql_user', 'bogususer')
        settings.put('mysql_password', 'boguspassword')
        try:
            settings.verifyMySQLConnectivity()
            self.fail('expected failure on invalid username and password')
        except SettingsException, se:
            log.debug('PASS: %s' % se)
        except:
            self.fail('expected SettingsException')
        
    def test_verifyMythTVConnectivity_OK(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        privateConfig = util.OnDemandConfig()
        settings.setMythTvHost(privateConfig.get('mythtv_host'))
        settings.setMythTvPort(int(privateConfig.get('mythtv_port')))
        settings.verifyMythTVConnectivity()

    def test_verifyMythTVConnectivity_InvalidPortThrowsSettingsException(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        privateConfig = util.OnDemandConfig()
        settings.setMythTvHost(privateConfig.get('mythtv_host'))
        settings.setMythTvPort(50000)
        try:
            settings.verifyMythTVConnectivity()
            self.fail('expected failure on invalid port')
        except SettingsException, se:
            log.debug("PASS: %s" % se)
        except Exception, ex:
            self.fail('Unexpected ex type: %s' % ex)
        
    def test_verifyRecordingDirs_EmptyStringThrowsSettingsException(self):
        try:
            MythSettings.verifyRecordingDirs('   ')
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyRecordingDirs_InvalidDirThrowsSettingsException(self):
        try:
            MythSettings.verifyRecordingDirs(os.path.join('someBogusDir', 'anotherBogusDir'))
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyRecordingDirs_OneInvalidOutOfManyOKThrowsSettingsException(self):
        try:
            MythSettings.verifyRecordingDirs(tempfile.gettempdir() + os.pathsep + 'someBogusDir' + os.pathsep + os.getcwd())
            self.fail('expected failure')
        except SettingsException, se:
            log.debug('PASS: %s' % se)

    def test_verifyRecordingDirs_OKSingleDirectory(self):
        MythSettings.verifyRecordingDirs(tempfile.gettempdir())
        
    def test_verifyRecordingDirs_OKManyDirectories(self):
        MythSettings.verifyRecordingDirs(
            tempfile.gettempdir() + os.pathsep + 
            os.getcwd() + os.pathsep + 
            tempfile.gettempdir() + os.pathsep + 
            os.getcwd())
        
    def test_verifyFFMpeg_OK(self):
        platform = mythbox.getPlatform()
        if (type(platform) == mythbox.UnixPlatform):
            try:
                MythSettings.verifyFFMpeg('/bin/true', platform)
            except SettingsException:
                self.fail("expected /bin/true to be a valid executable")
        else:
            log.warn('Test not supported on this platform: %s' % platform)

    def test_verifyFFMpeg_ThrowsExceptionOnNonExistentExecutable(self):
        platform = mythbox.getPlatform()
        if (type(platform) == mythbox.UnixPlatform):
            try:
                MythSettings.verifyFFMpeg('/bin/bogus_exe_name', platform)
                self.fail("expected failure on invalid exe name")
            except SettingsException, ex:
                log.debug('PASS: %s' % ex)
        else:
            log.warn('Test not supported on this platform: %s' % platform)
            
    def test_verifyMySQLUser_OK(self):
        MythSettings.verifyMySQLUser('someUser')
        
    def test_verifyMySQLUser_EmptyStringThrowsSettingsException(self):
        try:
            MythSettings.verifyMySQLUser('')
        except SettingsException, se:
            log.debug('PASS: %s' % se)
            
    def test_verifyBoolean_AllValuesThatShouldNotRaiseException(self):
        MythSettings.verifyBoolean('True', 'blah')
        MythSettings.verifyBoolean('False', 'blah')
        MythSettings.verifyBoolean('1', 'blah')
        MythSettings.verifyBoolean('0', 'blah')

    def test_verifyBoolean_AllValuesThatShouldRaiseException(self):
        badValues = ('true', 'false', '', '2', 'crap')
        for b in badValues:
            try:
                MythSettings.verifyBoolean(b, 'blah')
                self.fail('should have throws SettingsException')
            except SettingsException, se:
                log.debug('PASS: %s %s' % (b, se))
                
    def test_When_existing_setting_changed_to_different_value_Then_listeners_notified(self):
        # Setup
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        s = MythSettings(self.platform, self.translator)
        listener = Mock()
        s.addListener(listener)
        
        # Test
        s.setConfirmOnDelete(False)

        # Verify
        verify(listener, 1).settingChanged('confirm_on_delete', 'True', 'False')
    
    def test_When_existing_setting_changed_to_same_value_Then_listeners_not_notified(self):
        # Setup
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        s = MythSettings(self.platform, self.translator)
        listener = Mock()
        s.addListener(listener)
        
        # Test
        s.setConfirmOnDelete(True)

        # Verify
        verifyZeroInteractions(listener)
    
    def test_When_new_setting_created_Then_listeners_not_notified(self):
        # Setup
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        s = MythSettings(self.platform, self.translator)
        listener = Mock()
        s.addListener(listener)
        
        # Test
        s.put('foo', 'bar', True)

        # Verify
        verifyZeroInteractions(listener)
    
# =============================================================================
class ConnectionTest(unittest.TestCase):

    def setUp(self):
        self.platform = mythbox.getPlatform()
        self.translator = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        
        privateConfig = util.OnDemandConfig()
        self.settings.setMySqlHost(privateConfig.get('mysql_host'))
        self.settings.put('mysql_port', privateConfig.get('mysql_port'))
        self.settings.setMySqlDatabase(privateConfig.get('mysql_database'))
        self.settings.setMySqlUser(privateConfig.get('mysql_user'))  
        self.settings.put('mysql_password', privateConfig.get('mysql_password'))
        self.settings.setMythTvHost(privateConfig.get('mythtv_host'))
        self.settings.setMythTvPort(int(privateConfig.get('mythtv_port')))
        self.settings.put('paths_recordedprefix', privateConfig.get('paths_recordedprefix'))
        
        self.db = mythdb.MythDatabase(self.settings, self.translator)
        self.conn = mythtv.Connection(self.settings, self.db, self.translator, self.platform)

    def tearDown(self):
        self.conn.close()

    def test_negotiateProtocol_ReturnsServerProtocolVersion(self):
        sock = self.conn.connect(False, False)
        try:
            version = self.conn.negotiateProtocol(sock, mythprotocol.initVersion)
            log.debug('Server Protcol = %s'%version)
            self.assertTrue(version > 0)
        finally:
            sock.close()

    def test_negotiateProtocol_RaisesProtocolException_When_ClientVersion_NotSupported_By_Server(self):
        sock = self.conn.connect(False, False)
        try:
            try:
                self.conn.negotiateProtocol(sock, 100)
                self.fail('Should have thrown ProtocolException')
            except util.ProtocolException, pe:
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

    def test_getFreeSpace(self):
        freeSpace = self.conn.getFreeSpace()
        log.debug('Freespace = %s' % freeSpace)
        self.assertEquals(3, len(freeSpace))

    def test_getLoad(self):
        cpuLoads = self.conn.getLoad()
        log.debug('CPU Loads = %s' % cpuLoads)
        self.assertEquals(3, len(cpuLoads))

    def test_getUptime(self):
        uptime = self.conn.getUptime()
        log.debug('Uptime = %s' % uptime)
        self.assertFalse(uptime is None)
        
    def test_getMythFillStatus(self):
        fillStatus = self.conn.getMythFillStatus()
        log.debug('mythfillstatus = %s' % fillStatus)
        self.assertFalse(fillStatus is None)

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
        # Setup
        recordings = self.conn.getRecordings()
        if len(recordings) == 0:
            log.warn('SKIPPED: No recordings available to use as test data')
        expected = recordings.pop()
        
        # Test
        actual = self.conn.getRecording(expected.getChannelId(), expected.starttime())
        
        # Verify
        log.debug('recording = %s' % actual)
        self.assertEquals(expected, actual)
        
    def test_getRecording_NotFound(self):
        # Setup
        recordings = self.conn.getRecordings()
        if len(recordings) == 0:
            log.warn('SKIPPED: No recordings available to use as test data')
        expected = recordings.pop()
        
        # Test
        actual = self.conn.getRecording(32, expected.starttime())
        
        # Verify
        self.assertTrue(actual is None)
    
    def test_getUpcomingRecordings_When_no_args_Then_returns_only_programs_that_will_be_recorded(self):
        upcoming = self.conn.getUpcomingRecordings()
        log.debug('Num upcoming recordings = %d' % (len(upcoming)))
        for i,program in enumerate(upcoming):
            log.debug('%d: tuner=%s %s' % (i, program.getTunerId(), program))
            #program.dumpData()
            
        for program in upcoming:
            self.assertTrue(program.getRecordingStatus() in mythtv.Connection.UPCOMING_SCHEDULED)
            self.assertTrue(program.getTunerId() >= 0)
            
    def test_getUpcomingRecordings_When_filter_is_scheduled_Then_returns_only_program_that_will_be_recorded(self):
        upcoming = self.conn.getUpcomingRecordings(mythtv.Connection.UPCOMING_SCHEDULED)
        log.debug('Num upcoming recordings (filter = UPCOMING_SCHEDULED) = %d' % (len(upcoming)))
        for program in upcoming:
            self.assertTrue(program.getRecordingStatus() in mythtv.Connection.UPCOMING_SCHEDULED)

    def test_getUpcomingRecordings_When_filter_is_conflict_Then_returns_only_program_that_will_not_be_recorded_because_of_a_conflict(self):
        upcoming = self.conn.getUpcomingRecordings(mythtv.Connection.UPCOMING_CONFLICTS)
        log.debug('Num upcoming recordings (filter = UPCOMING_CONFLICTS) = %d' % (len(upcoming)))
        for program in upcoming:
            self.assertTrue(program.getRecordingStatus() in mythtv.Connection.UPCOMING_CONFLICTS)

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
        recorderID, hostname, port = self.conn.getFreeTuner()
        if recorderID == -1:
            log.debug('No free recorders available')
            self.assertEquals('', hostname)
            self.assertEquals(-1, port)
        else:
            log.debug('Free recorder = id: %d hostname: %s  port: %d'%(recorderID, hostname, port))
            self.assertTrue(recorderID >= 0)
            self.assertTrue(len(hostname) > 0)
            self.assertTrue(port > 0)
        
    def test_getNextFreeTuner(self):
        recorderID, hostname, port = self.conn.getNextFreeTuner(-1)
        if recorderID is None:
            pass
        else:
            log.debug('Next free recorder = id:%d hostname:%s port:%d'%(recorderID, hostname, port))
        #TODO: valid assertions when recorder free and not available
        
    def test_isAccept_MatchReturnsTrue(self):
        msg = ['ACCEPT', '40']
        self.assertTrue(self.conn._isAccept(msg, 40))
        
    def test_isAccept_ProtocolVersionDoesntMatchReturnsFalse(self):
        msg = ['ACCEPT', '41']
        self.assertFalse(self.conn._isAccept(msg, 40))

    def test_isAccept_ResponseDoesntMatchReturnsFalse(self):
        msg = ['FAIL', '41']
        self.assertFalse(self.conn._isAccept(msg, 41))
        
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

    def test_isTunerRecording_InvalidRecorderIDRaisesProtocolException(self):
        self.assertRaises(util.ProtocolException, self.conn.isTunerRecording, -1)
        
    def test_isTunerRecording_False(self):
        freeTunerID, hostname, port = self.conn.getFreeTuner()
        if freeTunerID != -1: 
            result = self.conn.isTunerRecording(freeTunerID)
            log.debug('isTunerRecording(%d) = %s' % (freeTunerID, result))
        else:
            log.warn('no free recorders available to test isTunerRecording()')
            
    def test_isTunerRecording_True(self):
        log.warn("TODO: Write unit test")
    
    def test_getBookmark_Success(self):
        # TODO: only check bookmarked recordings
        programs = self.conn.getRecordings()
        self.assertTrue(len(programs) > 0, 'Cannot run test because no programs returned')
        log.debug('Getting bookmark for %s' % programs[0])
        bookmark = self.conn.getBookmark(programs[0])
        log.debug('bookmark = %s seconds' % bookmark)
        self.assertTrue(bookmark >= 0)
    
    def test_setBookmark_Success(self):
        programs = self.conn.getRecordings()
        self.assertTrue(len(programs) > 0, 'Cannot run test because no programs returned')
        p = programs.pop()
        log.debug('Setting bookmark for %s' % p)
        self.conn.setBookmark(p, 1000)
        self.assertEquals(1000, self.conn.getBookmark(p))

    def test_setBookmark_ChannelIDInvalid(self):
        programs = self.conn.getRecordings()
        self.assertTrue(len(programs) > 0, 'Cannot run test because no programs returned')
        p = programs.pop()
        p.setChannelId(999)
        self.assertEquals(999, p.getChannelId())
        self.assertRaises(util.ServerException, self.conn.setBookmark, p, 500)
        
    def test_getCommercialBreaks(self):
        
        # TODO: Uses injected pojo so have to init pool. Fix later
        import pool
        import injected
        pool.pools['dbPool'] = pool.Pool(mythdb.MythDatabaseFactory(settings=self.settings, translator=self.translator))
        pool.pools['connPool'] = pool.Pool(injected.ConnectionFactory(settings=self.settings, translator=self.translator, platform=self.platform))
        
        recordings = self.conn.getRecordings()
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
        programs = self.conn.getRecordings()
        self.assertTrue(len(programs) > 0, 'Cannot run test; No programs in db to play with')
        log.debug('Generating thumbnail for program: %s' % programs[0])
        result = self.conn.generateThumbnail(programs[0], self.settings.getMythTvHost())
        self.assertTrue(result)
         
    def test_getThumbnailCreationTime_ThumbnailExists(self):
        programs = self.conn.getRecordings()
        self.assertTrue(len(programs) > 0, 'Cannot run test; No programs in db to play with')
        log.debug('Getting thumbnail creation time for: %s' % programs[0])
        dt = self.conn.getThumbnailCreationTime(programs[0], self.settings.getMythTvHost())
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
        recordings = self.conn.getRecordings()
        self.assertTrue(len(recordings) > 0, 'Recordings required to run this test')
        recording = recordings[-1]
        
        if not self.conn.getThumbnailCreationTime(recording, recording.hostname()): # generate thumbnail if necessary
            log.debug('Generating thumbnail...')
            self.conn.generateThumbnail(recording, recording.hostname())
            recording = self.conn.getRecording(recording.getChannelId(), recording.getStartTime())
            
        backendPath = recording.getRemoteThumbnailPath()
        destPath = os.path.join(tempfile.gettempdir(), recording.getBareFilename() + ".png")
        
        # Test
        try:
            log.debug('Transferring file %s to %s with size %s' % (backendPath, destPath, os.path.getsize(recording.getLocalThumbnailPath())))
            result = self.conn.transferFile(backendPath, destPath, recording.hostname())
            
            # Verify
            self.assertEquals(0, result)
            self.assertTrue(os.path.exists(destPath))
            self.assertTrue(os.path.isfile(destPath))
            self.assertEquals(os.path.getsize(recording.getLocalThumbnailPath()), os.path.getsize(destPath))
            
        finally:
            # Cleanup
            try: os.remove(destPath); 
            except: pass
    
    def test_transferFile_FileDoesNotExistOnBackend(self):
        
        # Setup
#        recordings = self.conn.getRecordings()
#        self.assertTrue(len(recordings) > 0, 'Recordings required to run this test')
#        recording = recordings[-1]
#        
#        if not self.conn.getThumbnailCreationTime(recording, recording.hostname()): # generate thumbnail if necessary
#            log.debug('Generating thumbnail...')
#            self.conn.generateThumbnail(recording, recording.hostname())
#            recording = self.conn.getRecording(recording.getChannelId(), recording.getStartTime())
#            
#        backendPath = recording.getRemoteThumbnailPath()
#        destPath = os.path.join(tempfile.gettempdir(), recording.getBareFilename() + ".png")
        
        # Test
        try:
            #log.debug('Transferring file %s to %s with size %s' % (backendPath, destPath, os.path.getsize(recording.getLocalThumbnailPath())))
            result = self.conn.transferFile(
                "myth://" + self.settings.getMythTvHost() + ":" + str(self.settings.getMythTvPort()) + "/bogusfile.mpg", 
                os.path.join(tempfile.mkdtemp(), 'bogusfile.mpg'), 
                self.settings.getMythTvHost())
            
            log.debug('Result = %s' % result)
            
            # Verify
#            self.assertEquals(0, result)
#            self.assertTrue(os.path.exists(destPath))
#            self.assertTrue(os.path.isfile(destPath))
#            self.assertEquals(os.path.getsize(recording.getLocalThumbnailPath()), os.path.getsize(destPath))
            
        finally:
            pass

# =============================================================================
class MythChannelIconResolverTest(unittest.TestCase):

    def setUp(self):
        self.platform = mythbox.getPlatform()
        self.translator = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        
        privateConfig = util.OnDemandConfig()
        self.settings.setMySqlHost(privateConfig.get('mysql_host'))
        self.settings.setMySqlPort(privateConfig.get('mysql_port'))
        self.settings.setMySqlDatabase(privateConfig.get('mysql_database'))
        self.settings.setMySqlUser(privateConfig.get('mysql_user'))  
        self.settings.setMySqlPassword(privateConfig.get('mysql_password'))
        self.settings.setMythTvHost(privateConfig.get('mythtv_host'))
        self.settings.setMythTvPort(int(privateConfig.get('mythtv_port')))
        self.settings.setRecordingDirs(privateConfig.get('paths_recordedprefix'))
        
        log.debug('%s' % self.settings)
        
        self.db = mythdb.MythDatabase(self.settings, self.translator)
        self.conn = mythtv.Connection(self.settings, self.db, self.translator, self.platform)

    def tearDown(self):
        self.conn.close()

    def test_store_When_channel_has_icon_Then_download_icon(self):
        # Setup
        channels = filter(lambda x: x.getIconPath(), self.conn.getChannels()) # filter out channels that don't have an icon
        self.assertTrue(len(channels) > 0, 'Channels with icon needed in db to run test')
        downloader = mythtv.MythChannelIconResolver(self.conn)
         
        # Test - download icons for first 5 channels
        for channel in channels[:min(5, len(channels))]:
            if channel.getIconPath():
                log.debug('%s' % channel)
                dest = os.path.sep.join([tempfile.gettempdir(), str(channel.getChannelId()) + channel.getCallSign() + str(time.time()) + ".png"])
                downloader.store(channel, dest)
        
                # Verify
                log.debug('Downloaded %s to %s' % (channel.getIconPath(), dest))
                self.assertTrue(os.path.exists(dest))
                self.assertTrue(os.path.isfile(dest))
                self.assertTrue(os.path.getsize(dest) > 0)
                
                # Cleanup
                os.remove(dest)        
    
    def test_store_When_channel_has_no_icon_Then_do_nothing(self):
        # Setup
        channel = domain.Channel({'name':'Bogus Channel', 'icon':None})
        conn = Mock()
        downloader = mythtv.MythChannelIconResolver(conn)
         
        # Test 
        downloader.store(channel, 'bogusDestDir')
    
        # Verify
        verifyZeroInteractions(conn)

    def test_store_When_channel_has_icon_but_icon_not_accessible_Then_do_nothing(self):
        pass
            
# =============================================================================    
if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
