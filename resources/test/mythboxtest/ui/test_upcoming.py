#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2010 analogue@yahoo.com
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
import unittest2

from mockito import Mock, when, any
from mythbox.ui.upcoming import UpcomingRecordingsWindow
from mockito.mockito import verifyZeroInteractions

log = logging.getLogger('mythbox.unittest')


class UpcomingRecordingsWindowTest(unittest2.TestCase):
    
    def setUp(self):
        self.current = Mock()
        self.previous = Mock()
        
        self.today = datetime.datetime.now()
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.tenDaysFromNow = self.today + datetime.timedelta(days=10)
        
        self.translator = Mock()
        kwargs = {'settings':Mock(), 'translator':self.translator, 'platform': Mock(), 'fanArt':Mock(), 'cachesByName': {'mythThumbnailCache':Mock(), 'mythChannelIconCache':Mock()}}
        self.urw = UpcomingRecordingsWindow(**kwargs)

    def test_formattedAirDate_When_previous_program_is_none_and_current_program_airs_today_Then_return_today(self):
        when(self.current).starttimeAsTime().thenReturn(self.today)
        when(self.translator).get(any(int)).thenReturn('Today')
        airDate = self.urw.formattedAirDate(previous=None, current=self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEqual('Today', airDate)

    def test_formattedAirDate_When_previous_program_is_none_and_current_program_airs_tomorrow_Then_return_tomorrow(self):
        when(self.current).starttimeAsTime().thenReturn(self.tomorrow)
        when(self.translator).get(any(int)).thenReturn('Tomorrow')
        airDate = self.urw.formattedAirDate(previous=None, current=self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEqual('Tomorrow', airDate)

    def test_formattedAirDate_When_previous_program_is_none_and_current_program_airs_two_or_more_days_out_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        airDate = self.urw.formattedAirDate(previous=None, current=self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))
        verifyZeroInteractions(self.translator)
        
    def test_formattedAirDate_When_previous_program_and_current_program_on_same_day_Then_return_empty_string(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        when(self.previous).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        airDate = self.urw.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEqual('', airDate)

    def test_formattedAirDate_When_previous_program_today_and_current_program_tomorrow_Then_return_tomorrow(self):
        when(self.current).starttimeAsTime().thenReturn(self.tomorrow)
        when(self.previous).starttimeAsTime().thenReturn(self.today)
        when(self.translator).get(any(int)).thenReturn('Tomorrow')
        airDate = self.urw.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEqual('Tomorrow', airDate)

    def test_formattedAirDate_When_previous_program_today_and_current_program_two_or_more_days_out_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        when(self.previous).starttimeAsTime().thenReturn(self.today)
        airDate = self.urw.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))
        
    def test_formattedAirDate_When_previous_program_tomorrow_and_current_two_or_more_days_out_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        when(self.previous).starttimeAsTime().thenReturn(self.tomorrow)
        airDate = self.urw.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))

    def test_formattedAirDate_When_previous_and_current_two_or_more_days_out_and_not_same_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow + datetime.timedelta(days=2)) # 12 days out
        when(self.previous).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        airDate = self.urw.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))
    

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest2.main()
