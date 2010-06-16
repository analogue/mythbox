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
import os
import tempfile
import unittest

from mockito import Mock, when, verify, any, verifyZeroInteractions
from mythbox.platform import getPlatform, UnixPlatform
from mythbox.settings import MythSettings, SettingsException
from mythbox.util import OnDemandConfig

log = logging.getLogger('mythbox.unittest')

# =============================================================================
class MythSettingsTest(unittest.TestCase):

    def setUp(self):
        self.translator = Mock()
        self.platform = Mock()
        self.bus = Mock()
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
        
        privateConfig = OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        settings.put('mysql_user', privateConfig.get('mysql_user'))
        settings.put('mysql_password', privateConfig.get('mysql_password'))
        settings.verifyMySQLConnectivity()

    def test_verifyMySQLConnectivity_InvalidUsernamePasswordThrowsSettingsException(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        privateConfig = OnDemandConfig()
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
        privateConfig = OnDemandConfig()
        settings.setMythTvHost(privateConfig.get('mythtv_host'))
        settings.setMythTvPort(int(privateConfig.get('mythtv_port')))
        settings.verifyMythTVConnectivity()

    def test_verifyMythTVConnectivity_InvalidPortThrowsSettingsException(self):
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        settings = MythSettings(self.platform, self.translator)
        privateConfig = OnDemandConfig()
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
        platform = getPlatform()
        if (type(platform) == UnixPlatform):
            try:
                MythSettings.verifyFFMpeg('/bin/true', platform)
            except SettingsException:
                self.fail("expected /bin/true to be a valid executable")
        else:
            log.warn('Test not supported on this platform: %s' % platform)

    def test_verifyFFMpeg_ThrowsExceptionOnNonExistentExecutable(self):
        platform = getPlatform()
        if (type(platform) == UnixPlatform):
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

    def test_When_existing_setting_changed_to_different_value_Then_event_published_to_bus(self):
        # Setup
        when(self.platform).getScriptDataDir().thenReturn(tempfile.gettempdir())
        s = MythSettings(self.platform, self.translator, bus=self.bus)
        
        # Test
        current = s.get('mysql_host')
        s.put('mysql_host', 'foo')

        # Verify
        verify(self.bus, 1).publish(any(dict))
        
# =============================================================================    
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
