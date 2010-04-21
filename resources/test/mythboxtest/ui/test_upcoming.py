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
import datetime
import logging
import unittest

from mockito import Mock, when
from mythbox.ui.upcoming import UpcomingRecordingsWindow

log = logging.getLogger('mythtv.unittest')

# =============================================================================
class UpcomingRecordingsWindowTest(unittest.TestCase):
    
    def setUp(self):
        self.current = Mock()
        self.previous = Mock()
        
        self.today = datetime.datetime.now()
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.tenDaysFromNow = self.today + datetime.timedelta(days=10)
        
    def test_formattedAirDate_When_previous_program_is_none_and_current_program_airs_today_Then_return_today(self):
        when(self.current).starttimeAsTime().thenReturn(self.today)
        airDate = UpcomingRecordingsWindow.formattedAirDate(previous=None, current=self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEquals('Today', airDate)

    def test_formattedAirDate_When_previous_program_is_none_and_current_program_airs_tomorrow_Then_return_tomorrow(self):
        when(self.current).starttimeAsTime().thenReturn(self.tomorrow)
        airDate = UpcomingRecordingsWindow.formattedAirDate(previous=None, current=self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEquals('Tomorrow', airDate)

    def test_formattedAirDate_When_previous_program_is_none_and_current_program_airs_two_or_more_days_out_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        airDate = UpcomingRecordingsWindow.formattedAirDate(previous=None, current=self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))

    def test_formattedAirDate_When_previous_program_and_current_program_on_same_day_Then_return_empty_string(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        when(self.previous).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        airDate = UpcomingRecordingsWindow.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEquals('', airDate)

    def test_formattedAirDate_When_previous_program_today_and_current_program_tomorrow_Then_return_tomorrow(self):
        when(self.current).starttimeAsTime().thenReturn(self.tomorrow)
        when(self.previous).starttimeAsTime().thenReturn(self.today)
        airDate = UpcomingRecordingsWindow.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertEquals('Tomorrow', airDate)

    def test_formattedAirDate_When_previous_program_today_and_current_program_two_or_more_days_out_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        when(self.previous).starttimeAsTime().thenReturn(self.today)
        airDate = UpcomingRecordingsWindow.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))
        
    def test_formattedAirDate_When_previous_program_tomorrow_and_current_two_or_more_days_out_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        when(self.previous).starttimeAsTime().thenReturn(self.tomorrow)
        airDate = UpcomingRecordingsWindow.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))

    def test_formattedAirDate_When_previous_and_current_two_or_more_days_out_and_not_same_Then_return_airdate(self):
        when(self.current).starttimeAsTime().thenReturn(self.tenDaysFromNow + datetime.timedelta(days=2)) # 12 days out
        when(self.previous).starttimeAsTime().thenReturn(self.tenDaysFromNow)
        airDate = UpcomingRecordingsWindow.formattedAirDate(self.previous, self.current)
        log.debug('Air date: %s' % airDate)
        self.assertTrue(airDate and not airDate in ('Tomorrow', 'Today', ''))
    
# =============================================================================
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
