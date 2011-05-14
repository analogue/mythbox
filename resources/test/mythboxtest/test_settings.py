# -*- coding: utf-8 -*-
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
import os
import shutil
import tempfile
import unittest

from mockito import Mock, when, verify, any
from mythbox.settings import MythSettings, SettingsException
from mythbox.util import OnDemandConfig

log = mythboxtest.getLogger('mythbox.unittest')


class MythSettingsTest(unittest.TestCase):

    def setUp(self):
        self.translator = Mock()
        self.platform = Mock()
        self.bus = Mock()
        when(self.platform).getDefaultRecordingsDir().thenReturn('')
        self.sandbox = tempfile.mkdtemp(prefix='mythbox')
        
    def tearDown(self):
        shutil.rmtree(self.sandbox, ignore_errors=True)

    def test_When_setting_has_a_unicode_value_Then_saving_and_loading_should_still_work(self):
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        s = MythSettings(self.platform, self.translator)
        unicodeStr = u'Königreich der Himmel'
        s.put('recordings_selected_group', unicodeStr)
        s.save()
        
        s2 = MythSettings(self.platform, self.translator)
        actualStr = s2.get('recordings_selected_group')
        self.assertTrue(unicodeStr == actualStr)
        self.assertTrue(isinstance(unicodeStr, unicode))
            
    def test_toString(self):
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        s = MythSettings(self.platform, self.translator)
        log.debug('MythSettings = \n%s' % s)
        
    def test_constructor_NonExistentSettingsFilesLoadsDefaults(self):
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
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
        filepath = os.path.join(self.sandbox, filename)
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        self.assertFalse(os.path.exists(filepath))
        s = MythSettings(self.platform, self.translator)
        s.save()
        self.assertTrue(os.path.exists(filepath))
        
    def test_getRecordingDirs_SingleDirectory(self):
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        settings = MythSettings(self.platform, self.translator)
        settings.put('paths_recordedprefix', '/mnt/mythtv')
        log.debug("Recording prefix = %s" % settings.get('paths_recordedprefix'))
        dirs = settings.getRecordingDirs()
        self.assertEquals(1, len(dirs))
        self.assertEquals('/mnt/mythtv', dirs[0])

    def test_getRecordingDirs_ManyDirectories(self):
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        settings = MythSettings(self.platform, self.translator)
        settings.put('paths_recordedprefix', os.pathsep.join(['a','b', 'c']))
        log.debug("Recording prefix = %s" % settings.get('paths_recordedprefix'))
        dirs = settings.getRecordingDirs()
        self.assertEquals(3, len(dirs))
        self.assertEquals(['a','b','c'], dirs)

    def test_verifyMySQLConnectivity_OK(self):
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        settings = MythSettings(self.platform, self.translator)
        
        privateConfig = OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        settings.put('mysql_user', privateConfig.get('mysql_user'))
        settings.put('mysql_password', privateConfig.get('mysql_password'))
        settings.verifyMySQLConnectivity()

    def test_verifyMySQLConnectivity_InvalidUsernamePasswordThrowsSettingsException(self):
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
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
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        settings = MythSettings(self.platform, self.translator)
        privateConfig = OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        settings.put('mysql_user', privateConfig.get('mysql_user'))
        settings.put('mysql_password', privateConfig.get('mysql_password'))
        settings.verifyMythTVConnectivity()
        
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
        MythSettings.verifyRecordingDirs(self.sandbox)
        
    def test_verifyRecordingDirs_OKManyDirectories(self):
        MythSettings.verifyRecordingDirs(
            self.sandbox + os.pathsep + 
            os.getcwd() + os.pathsep + 
            self.sandbox + os.pathsep + 
            os.getcwd())
            
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
        when(self.platform).getScriptDataDir().thenReturn(self.sandbox)
        s = MythSettings(self.platform, self.translator, bus=self.bus)
        
        # Test
        s.get('mysql_host')
        s.put('mysql_host', 'foo')

        # Verify
        verify(self.bus, 1).publish(any(dict))
