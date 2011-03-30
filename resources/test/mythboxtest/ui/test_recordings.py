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
import datetime
import logging
import unittest2 as unittest
import mythboxtest

from mockito import Mock, when, any
from mythbox.ui.recordings2 import RecordingsWindow, Group, GROUP_SORT_BY, TITLE_SORT_BY
from mockito.mockito import verifyZeroInteractions
from mythbox.mythtv.domain import RecordedProgram


log = mythboxtest.getLogger('mythbox.unittest')


class RecordingsWindowTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_When_group_title_contains_unicode_chars_Then_group_sorting_doesnt_break(self):
        u1 = u'Königreich der Himmel'
        u2 = u'Avocats et associés'
        u3 = u'All Recordings'
        
        g1 = Group(u1)
        g2 = Group(u2)
        g3 = Group(u3)
        
        c = [g1,g2, g3]
        
        c.sort(key=GROUP_SORT_BY['Title']['sorter'], reverse=GROUP_SORT_BY['Title']['reverse'])

        self.assertTrue(c[0].title == u3)
        self.assertTrue(c[1].title == u2)
        self.assertTrue(c[2].title == u1)
    
#    def test_When_program_title_contains_unicode_chars_Then_title_sorting_doesnt_break(self):
#        u1 = u'Königreich der Himmel'
#        u2 = u'Avocats et associés'
#        u3 = u'All Recordings'
#        
#        p1 = RecordedProgram(data, settings, translator, platform, protocol, conn)
#        
#        g1 = Group(u1)
#        g2 = Group(u2)
#        g3 = Group(u3)
#        
#        c = [g1,g2, g3]
#        
#        c.sort(key=TITLE_SORT_BY['Title']['sorter'], reverse=TITLE_SORT_BY['Title']['reverse'])
#
#        self.assertTrue(c[0].title == u3)
#        self.assertTrue(c[1].title == u2)
#        self.assertTrue(c[2].title == u1)
