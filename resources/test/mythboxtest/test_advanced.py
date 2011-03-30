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

import os
import shutil
import tempfile
import unittest2 as unittest
import mythboxtest

from mockito import Mock, when
from mythbox.advanced import AdvancedSettings

log = mythboxtest.getLogger('mythbox.unittest')

class AdvancedSettingsTest(unittest.TestCase):

    def test_constructor_When_seeded_with_xml_as_string(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        xml = """<advancedsettings><loglevel>0</loglevel></advancedsettings>"""
        advanced = AdvancedSettings(platform=p, init_with=xml)
        self.assertTrue(advanced.hasSetting('loglevel'))
            
    def test_str_When_advancedsettings_file_does_not_exists_Then_constructor_will_initialize_a_new_dom(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        advanced = AdvancedSettings(platform=p)
        s = '%s' % advanced
        log.debug(s)
        self.assertTrue("<advancedsettings />" in s)

    def test_save_When_advancedsettings_file_does_not_exist_Then_backup_is_not_created(self):
        sandbox = tempfile.mkdtemp(suffix='mythbox')
        try:
            p = Mock()
            when(p).getUserDataDir().thenReturn(sandbox)
            advanced = AdvancedSettings(platform=p)
            advanced.save()
            self.assertTrue(os.path.exists(os.path.join(sandbox, 'advancedsettings.xml')))
            self.assertFalse(os.path.exists(os.path.join(sandbox, 'advancedsettings.xml.mythbox')))
        finally:
            shutil.rmtree(sandbox)

    def test_save_When_advancedsettings_file_does_exist_and_no_backup_exists_Then_backup_created(self):
        sandbox = tempfile.mkdtemp(suffix='mythbox')
        f = open(os.path.join(sandbox, 'advancedsettings.xml'), 'w')
        f.write('<advancedsettings><loglevel>0</loglevel></advancedsettings>')
        f.close()
        self.assertTrue(os.path.exists(os.path.join(sandbox, 'advancedsettings.xml')))
        
        try:
            p = Mock()
            when(p).getUserDataDir().thenReturn(sandbox)
            advanced = AdvancedSettings(platform=p)
            advanced.save()
            self.assertTrue(os.path.exists(os.path.join(sandbox, 'advancedsettings.xml.mythbox')))
        finally:
            shutil.rmtree(sandbox)

    # hasSetting
    
    def test_hasSetting_When_setting_does_not_exist_Then_returns_false(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        advanced = AdvancedSettings(platform=p)
        self.assertFalse(advanced.hasSetting('loglevel'))

    def test_hasSetting_When_setting_exists_at_depth_eq_1_Then_returns_true(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        advanced = AdvancedSettings(platform=p, init_with="""<advancedsettings><loglevel>0</loglevel></advancedsettings>""")
        self.assertTrue(advanced.hasSetting('loglevel'))

    def test_hasSetting_When_setting_exists_at_depth_gt_1_Then_returns_true(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        xml = """
        <advancedsettings>
            <loglevel>0</loglevel>
            <video>
                <usetimeseeking>true</usetimeseeking>
            </video>
        </advancedsettings>
        """
        s = AdvancedSettings(platform=p, init_with=xml)
        self.assertTrue(s.hasSetting('video/usetimeseeking'))
        self.assertFalse(s.hasSetting('video/usetimeseeking/crapola'))
        self.assertTrue(s.hasSetting('loglevel'))
        self.assertFalse(s.hasSetting('loglevel/crapola'))
        self.assertTrue(s.hasSetting('video'))

    # getSetting
    
    def test_getSetting_When_non_empty_setting_Then_return_as_str(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p, init_with='<advancedsettings><loglevel>0</loglevel></advancedsettings>')
        self.assertEqual('0', s.getSetting('loglevel'))

    def test_getSetting_When_non_empty_nested_setting_Then_return_as_str(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        xml = """
        <advancedsettings>
            <loglevel>0</loglevel>
            <video>
                <usetimeseeking>true</usetimeseeking>
            </video>
        </advancedsettings>
        """
        s = AdvancedSettings(platform=p, init_with=xml)
        self.assertEqual('0', s.getSetting('loglevel'))
        self.assertEqual('true', s.getSetting('video/usetimeseeking'))
        self.assertIsNone(s.getSetting('loglevel/foo'))

    def test_getSetting_When_empty_setting_but_setting_exists_Then_return_as_empty_str(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p, init_with='<advancedsettings><loglevel></loglevel></advancedsettings>')
        self.assertEqual('', s.getSetting('loglevel'))

    def test_getSetting_When_setting_does_not_exist_Then_return_none(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p, init_with='<advancedsettings><loglevel></loglevel></advancedsettings>')
        self.assertIsNone(s.getSetting('foo'))

    # setSetting
    
    def test_setSetting_When_setting_does_not_exist_Then_create_it(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p, init_with='<advancedsettings><loglevel>0</loglevel></advancedsettings>')
        s.setSetting('displayremotecodes', 'true')
        xml = s.__str__()
        log.debug(xml)
        [self.assertTrue(s in xml) for s in ('<displayremotecodes>','true','</displayremotecodes>')]

    def test_setSetting_When_setting_exists_Then_update_it(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p, init_with='<advancedsettings><loglevel>3</loglevel></advancedsettings>')
        s.setSetting('loglevel', '2')
        xml = s.__str__()
        log.debug(xml)
        self.assertTrue('<loglevel>' in xml)
        self.assertTrue('2' in xml)
        self.assertTrue('</loglevel>' in xml)
        self.assertFalse('3' in xml)

    def test_setSetting_When_nested_setting_does_not_exist_Then_create_it(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p)
        s.setSetting('video/displayremotecodes', 'true')
        xml = s.__str__()
        log.debug(xml)
        [self.assertTrue(s in xml) for s in ('<video>','<displayremotecodes>','true','</displayremotecodes>','</video>')]

    def test_setSetting_When_nested_setting_does_not_exist_but_part_of_its_xml_path_does_Then_create_it(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p, init_with='<advancedsettings><video></video></advancedsettings>')
        s.setSetting('video/displayremotecodes', 'true')
        xml = s.__str__()
        log.debug(xml)
        [self.assertTrue(s in xml) for s in ('<video>','<displayremotecodes>','true','</displayremotecodes>','</video>')]
        
    def test_setSetting_Works_for_many_settings(self):
        p = Mock()
        when(p).getUserDataDir().thenReturn('')
        s = AdvancedSettings(platform=p)
        s.setSetting('loglevel', '2')
        s.setSetting('displayremotecodes', 'true')
        xml = s.__str__()
        log.debug(xml)
        self.assertTrue('<loglevel>' in xml)
        self.assertTrue('2' in xml)
        self.assertTrue('</loglevel>' in xml)
        self.assertTrue('<displayremotecodes>' in xml)
        self.assertTrue('true' in xml)
        self.assertTrue('</displayremotecodes>' in xml)
