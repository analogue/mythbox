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
import os
import shutil
import tempfile
import time
import unittest2

from mockito import Mock, when, verify, any
from mythbox.settings import MythSettings
from mythbox.mythtv import protocol

from mythbox.mythtv.domain import ctime2MythTime, dbTime2MythTime, Backend, \
     Channel, CommercialBreak, Job, TVProgram, Program, RecordedProgram, \
     RecordingSchedule, Tuner, MythUrl, StatusException, frames2seconds, seconds2frames

from mythbox.mythtv.enums import CheckForDupesIn, CheckForDupesUsing, FlagMask, \
     EpisodeFilter, JobStatus, JobType, TVState

from mythbox.platform import Platform

log = logging.getLogger('mythbox.unittest')


class ModuleFunctionsTest(unittest2.TestCase):
    
    def test_ctime2MythTime_MinDateStringReturnsMinDate(self):
        t = ctime2MythTime('0')
        log.debug('MythTime = %s' % t)
        self.assertEqual('19691231180000', t)

    def test_ctime2MythTime_MinDateIntReturnsMinDate(self):
        t = ctime2MythTime(0)
        log.debug('MythTime = %s' % t)
        self.assertEqual('19691231180000', t)

    def test_ctime2MythTime_BadInputRaisesValueError(self):
        # PLATFORM ISSUE: Throws exception on windows but returns 19691231175959 on linux
        try:
            t = ctime2MythTime(-1)
            log.warn('Expected failure for time = -1 : %s' % t)
        except ValueError, ve:
            log.debug('Pass: %s' % ve)
            
    def test_dbTime2MythTime_ShouldConvertTimeDeltaToString(self):
        td = datetime.timedelta(seconds=1000) 
        mt = dbTime2MythTime(td)
        log.debug('MythTime = %s' % mt)
        self.assertEqual('001640', mt)

    def test_frames2seconds(self):
        s = frames2seconds(1000, 29.97)
        log.debug('1000 frames @ 29.97fps = %s seconds' % s)
        self.assertEquals(33.37, s)
        
        s = frames2seconds(0, 29.97)
        log.debug('0 frames @ 29.97fps = %s seconds' % s)
        self.assertEquals(0.0, s)
        
        s = frames2seconds(99999999L, 29.97)
        log.debug('99999999L frames @ 29.97fps = %s seconds' % s)
        self.assertEquals(3336669.97, s)
    
    def test_seconds2frames(self):
        s = seconds2frames(33.37, 29.97)
        log.debug('33.37 seconds @ 29.97fps = %s frames' % s)
        self.assertEquals(1000L, s)

        s = seconds2frames(0, 29.97)
        log.debug('0 seconds @ 29.97fps = %s frames' % s)
        self.assertEquals(0L, s)
        
        s = seconds2frames(3336669.97, 29.97)
        log.debug('3336669.97 seconds @ 29.97fps = %s frames' % s)
        self.assertEquals(99999999L, s)


class CheckForDupesUsingTest(unittest2.TestCase):
    
    def test_access_to_static_constants_works(self):
        self.assertEquals(145, CheckForDupesUsing.translations[CheckForDupesUsing.NONE])
        

class ProgramTest(unittest2.TestCase):

    def setUp(self):
        self.translator = Mock()

    def test_constructor(self):
        p = Program(self.translator)
        self.assertFalse(p is None)


class ChannelTest(unittest2.TestCase):
    
    def test_constructor(self):
        channel = Channel({'chanid':9, 'channum':'23_1', 'callsign':'WXYZ', 'name':'NBC9', 'icon':'nbc.jpg', 'cardid':4})
        log.debug(channel)
        self.assertTrue(channel)

    def test_constructor_IconMissing(self):
        channel = Channel({'chanid':9, 'channum':'23_1', 'callsign':'WXYZ', 'name':'NBC9', 'cardid':4})
        log.debug(channel)
        self.assertTrue(channel.getIconPath() is None)
        
    def test_getSortableChannelNumber_When_channel_number_is_already_sortable_Then_return_channel_number(self):
        channel = Channel({'chanid':9, 'channum':'23', 'callsign':'WXYZ', 'name':'NBC9', 'cardid':4})
        log.debug('Sortable channel number = %s' % channel.getSortableChannelNumber())
        self.assertEquals(23, channel.getSortableChannelNumber())

    def test_getSortableChannelNumber_When_channel_number_contains_underscore_Then_return_channel_number_as_float(self):
        number = Channel({'chanid':9, 'channum':'23_4', 'callsign':'WXYZ', 'name':'NBC9', 'cardid':4}).getSortableChannelNumber()
        log.debug('Sortable channel number = %s' % number)
        self.assertEquals(23.4, number)

    def test_getSortableChannelNumber_When_channel_number_contains_dot_Then_return_channel_number_as_float(self):
        number = Channel({'chanid':9, 'channum':'23.4', 'callsign':'WXYZ', 'name':'NBC9', 'cardid':4}).getSortableChannelNumber()
        log.debug('Sortable channel number = %s' % number)
        self.assertEquals(23.4, number)

    def test_getSortableChannelNumber_When_channel_number_doesnt_seem_like_a_number_Then_return_channel_id(self):
        number = Channel({'chanid':9, 'channum':'23/4', 'callsign':'WXYZ', 'name':'NBC9', 'cardid':4}).getSortableChannelNumber()
        log.debug('Sortable channel number = %s' % number)
        self.assertEquals(9, number)


class TVProgramTest(unittest2.TestCase):

    def setUp(self):
        self.data = { 
            'title'       : 'Bonanza', 
            'subtitle'    : 'The Shootout',
            'description' : 'Yee haw!',
            'starttime'   : datetime.datetime(2008, 11, 21, 14),
            'endtime'     : datetime.datetime(2008, 11, 21, 14),
            'channum'     : '23',
            'hdtv'        : True
        }
        self.translator = Mock() 
        self.platform = Platform()
        self.settings = MythSettings(self.platform, self.translator)

    def test_constructor(self):
        program = TVProgram(self.data, self.translator)
        self.assertTrue(program is not None)
        self.assertTrue(program.isHD())

    def test_starttimeAsTime(self):
        program = TVProgram(self.data, self.translator) 
        time = program.starttimeAsTime()
        log.debug('startTime = %s' % time)
        self.assertTrue(time)
        
    def test_starttime_TypeInDataDictIsADateTime(self):
        p = TVProgram({'starttime': datetime.datetime(2008, 11, 21, 14)}, self.translator)
        self.assertEquals('20081121140000', p.starttime())


class RecordedProgramTest(unittest2.TestCase):

    def setUp(self):
        self.conn = Mock()
        self.settings = Mock()
        self.translator = Mock()
        self.platform = Mock()
        self.protocol = protocol.Protocol40()
        self.data = ["0"] * self.protocol.recordSize()
            
    def test_hasBookmark_False(self):
        p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        p.setProgramFlags(FlagMask.FL_AUTOEXP)
        self.assertFalse(p.isBookmarked())
        self.assertTrue(p.isAutoExpire())
    
    def test_hasBookmark_True(self):
        p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        p.setProgramFlags(FlagMask.FL_BOOKMARK | FlagMask.FL_AUTOEXP)
        self.assertTrue(p.isBookmarked())
        self.assertTrue(p.isAutoExpire())
        
    def test_setBookmark(self):
        log.warn("TODO: Write unit test")
    
    def test_getBookmark(self):
        log.warn("TODO: Write unit test")
        
    def test_hasCommercials_True(self):
        self.data[29] = FlagMask.FL_COMMFLAG | FlagMask.FL_AUTOEXP
        p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        commBreaks = []
        commBreaks.append(CommercialBreak(120,180))
        when(self.conn).getCommercialBreaks(p).thenReturn(commBreaks)
        log.debug('comms = %s' % len(p.getCommercials()))
        self.assertTrue(p.hasCommercials())    
        #verify(self.conn).getCommercialBreaks(p)

    def test_hasCommercials_False(self):
        self.data[29] = FlagMask.FL_COMMFLAG | FlagMask.FL_AUTOEXP
        p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        commBreaks = []
        when(self.conn).getCommercialBreaks(p).thenReturn(commBreaks)
        log.debug('comms = %s' % len(p.getCommercials()))
        self.assertFalse(p.hasCommercials())    

    def test_getCommercials_ReturnsOneCommercial(self):
        self.data[29] = FlagMask.FL_COMMFLAG | FlagMask.FL_AUTOEXP
        p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        commBreaks = []
        commBreaks.append(CommercialBreak(120,180))
        when(self.conn).getCommercialBreaks(p).thenReturn(commBreaks)
        result = p.getCommercials()    
        log.debug('commercials = %s'%result)
        self.assertEquals(commBreaks, result)
        verify(self.conn).getCommercialBreaks(p)

    def test_getFrameRate_29point97(self):
        try:
            datadir = tempfile.mkdtemp()
            self.data[8] = "myth://192.168.1.11:6543/movie_29.97_fps.mpg" # filename 
            self.data[16] = "localhost" # hostname
            when(self.settings).getRecordingDirs().thenReturn([os.path.join(os.getcwd(), 'resources', 'test')])
            when(self.platform).getFFMpegPath().thenReturn('ffmpeg')
            when(self.platform).getScriptDataDir().thenReturn(datadir)
            
            # Should invoke ffmpeg
            p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
            self.assertEquals(29.97, p.getFrameRate())
            
            # TODO: Verify ffmpeg executable not invoked again (separate instance of a RecordedProgram)
            p2 = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
            self.assertEquals(29.97, p2.getFrameRate())            
        finally:
            shutil.rmtree(datadir, True)
        
    def test_eq_True_self(self):
        self.data[4]  = "99"
        self.data[11] = 999999 
        p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        self.assertEquals(p, p)

    def test_eq_True_same_channelId_and_startttime(self):
        self.data[4]  = "99"    # channelId
        self.data[11] = 999999  # starttime
        p1 = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        p2 = RecordedProgram(self.data[:], self.settings, self.translator, self.platform, self.protocol, self.conn) 
        self.assertEquals(p1, p2)
        self.assertEquals(p2, p1)

    def test_eq_False_different_channelId_and_startttime(self):
        self.data[4]  = "99"    # channelId
        self.data[11] = 999999  # starttime
        p1 = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        
        d2 = ["0"] * protocol.Protocol40().recordSize()
        d2[4] = "101"
        d2[11] = 777777
        p2 = RecordedProgram(d2, self.settings, self.translator, self.platform, self.protocol, self.conn) 
        self.assertNotEquals(p1, p2)
        self.assertNotEquals(p2, p1)

    def test_eq_False_different_channelId_same_startttime(self):
        self.data[4]  = "99"    # channelId
        self.data[11] = 999999  # starttime
        p1 = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        
        d2 = ["0"] * protocol.Protocol40().recordSize()
        d2[4] = "101"
        d2[11] = self.data[11]
        p2 = RecordedProgram(d2, self.settings, self.translator, self.platform, self.protocol, self.conn) 
        self.assertNotEquals(p1, p2)
        self.assertNotEquals(p2, p1)

    def test_formattedAirTime(self):
        self.data[11] = self.socketTime(21, 0, 0)   # 9:00pm
        self.data[12] = self.socketTime(21, 30, 0)  # 9:30pm
        p = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        self.assertEquals('9:00 - 9:30PM', p.formattedAirTime(short=False))
        self.assertEquals('9 - 9:30PM', p.formattedAirTime(short=True))
        self.assertEquals('9 - 9:30PM', p.formattedAirTime())
        
    def test_getDuration_When_duration_is_half_hour_Then_return_30mins(self):
        self.data[11] = self.socketTime(18, 30, 0)  # starttime = 6:30pm
        self.data[12] = self.socketTime(19, 0, 0)   # end time  = 7:00pm
        d = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn).getDuration()
        log.debug('Duration = %d' % d)
        self.assertEquals(30, d)

    def test_getDuration_When_2_hour_duration_spans_midnight_into_next_day_Then_return_120mins(self):
        self.data[11] = self.socketDateTime(2009, 10, 10, 23, 0, 0)  # starttime = 10/10/2009 11pm
        self.data[12] = self.socketDateTime(2009, 10, 11, 1, 0, 0)   # end time  = 10/11/2009 1am
        d = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn).getDuration()
        log.debug('Duration = %d' % d)
        self.assertEquals(120, d)
        
    def test_getDuration_When_start_and_end_times_same_Then_return_0mins(self):
        self.data[11] = self.socketTime(18, 30, 0)  # starttime = 6:30pm
        self.data[12] = self.socketTime(18, 30, 0)  # end time  = 6:30pm
        d = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn).getDuration()
        log.debug('Duration = %d' % d)
        self.assertEquals(0, d)

    def test_formattedStartTime_1pm(self):
        self.data[11] = self.socketTime(13, 0, 0)
        s = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn).formattedStartTime()
        log.debug('startime = %s' % s)
        self.assertEquals('1:00 PM', s)
        
    def test_formattedDuration(self):
        data = [
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(20, 30, 0), 'expected' : '2 hrs'},
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(19, 30, 0), 'expected' : '1 hr'},
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(18, 31, 0), 'expected' : '1 m'},
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(19, 0, 0),  'expected' : '30 m'},
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(20, 0, 0),  'expected' : '1 hr 30 m'},
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(21, 0, 0),  'expected' : '2 hrs 30 m'},
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(19, 31, 0), 'expected' : '1 hr 1 m'},
            {'start' : self.socketTime(18, 30, 0), 'end' : self.socketTime(20, 31, 0), 'expected' : '2 hrs 1 m'}]
        
        for d in data:
            self.data[11] = d['start']
            self.data[12] = d['end']
            s = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn).formattedDuration()
            log.debug('Duration = %s' % s)
            self.assertEquals(d['expected'], s)
      
    def test_originalAirDate_When_missing_Returns_None(self):
        self.data[38] = 0
        self.data[37] = ''
        rp = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        self.assertFalse(rp.hasOriginalAirDate())
        self.assertEquals('', rp.originalAirDate())
        
    def test_originalAirDate_When_available_Returns_date_as_string(self):
        self.data[38] = 1
        self.data[37] = '2008-10-10'
        rp = RecordedProgram(self.data, self.settings, self.translator, self.platform, self.protocol, self.conn)
        self.assertEquals('2008-10-10', rp.originalAirDate())
        self.assertTrue(rp.hasOriginalAirDate())
            
    def socketTime(self, h, m, s):
        # return raw value that myth passes over socket for today and passed in starttime/endtime (in local timezone)
        return time.mktime(datetime.datetime.combine(datetime.date.today(), datetime.time(h,m,s)).timetuple())

    def socketDateTime(self, year, month, day, h, m, s):
        return time.mktime(datetime.datetime.combine(datetime.date(year, month, day), datetime.time(h,m,s)).timetuple())
        

class TunerTest(unittest2.TestCase):

    def setUp(self):
        self.db = Mock()
        self.conn = Mock()
        self.translator = Mock()
        self.tuner = Tuner(4, 'mrbun', 1000, 6000, 'HDHOMERUN', self.conn, self.db, self.translator)
        
    def test_toString(self):
        log.debug('tuner = %s'%self.tuner)
        self.assertFalse(self.tuner is None)

    def test_isWatchingOrRecording_CardIdle(self):
        when(self.conn).getTunerShowing('Seinfeld').thenReturn(-1)
        self.assertFalse(self.tuner.isWatchingOrRecording('Seinfeld'))

    def test_isWatchingOrRecording_CardNotIdleButShowDoesntMatch(self):
        when(self.conn).getTunerShowing('Seinfeld').thenReturn(-1)
        self.assertFalse(self.tuner.isWatchingOrRecording('Seinfeld'))

    def test_isWatchingOrRecording_CardNotIdleAndShowMatches(self):
        when(self.conn).getTunerShowing('Seinfeld').thenReturn(self.tuner.tunerId)
        self.assertTrue(self.tuner.isWatchingOrRecording('Seinfeld'))
        
    def test_isRecording_True(self):
        when(self.conn).isTunerRecording(any()).thenReturn(True)
        result = self.tuner.isRecording()
        log.debug('isRecording_True = %s'%result)
        self.assertTrue(result)
        verify(self.conn).isTunerRecording(any())
    
    def test_isRecording_False(self):
        when(self.conn).isTunerRecording(any()).thenReturn(False)
        self.assertFalse(self.tuner.isRecording())
        verify(self.conn).isTunerRecording(any())

    def test_hasChannel_True(self):
        channels = []
        for x in range(0,5):
            channels.append(Channel(
                {'chanid':x, 'channum':'%d'%x, 'callsign':'WXYZ', 
                 'name':'NBC9', 'icon':'nbc.jpg', 'cardid':4}))
        when(self.conn).getChannels().thenReturn(channels)
        self.assertTrue(self.tuner.hasChannel(Channel(dict(channum='3'))))
    
    def test_hasChannel_False(self):
        channels = []
        for x in range(0,5):
            channels.append(Channel(
                {'chanid':x, 'channum':'%d'%x, 'callsign':'WXYZ', 
                 'name':'NBC9', 'icon':'nbc.jpg', 'cardid':4}))
        when(self.conn).getChannels().thenReturn(channels)
        self.assertFalse(self.tuner.hasChannel(Channel(dict(channum='6'))))
        
    def test_getChannels_CachingWorks(self):
        channels = []
        for x in range(0,5):
            channels.append(Channel(
                {'chanid':x, 'channum':'%d'%x, 'callsign':'WXYZ', 
                 'name':'NBC9', 'icon':'nbc.jpg', 'cardid':4}))
        when(self.conn).getChannels().thenReturn(channels)
        
        for x in range(10):
            channels = self.tuner.getChannels()
        
        verify(self.conn, 1).getChannels()

    def xxx_test_formattedTunerStatus_Success(self):
        # Setup
        self.conn.protocol = protocol.Protocol40()
        when(self.conn).getTunerStatus(any()).thenReturn(TVState.OK)
        rp = RecordedProgram()
        when(self.conn).getUpcomingRecordings(any()).thenReturn(rp)
        
        # Test
        status = self.tuner.formattedTunerStatus()
        
        # Verify
        log.debug('Formatted tuner status = %s' % status)
        self.assertFalse(status is None)
        
    def test_getNextScheduledRecording(self):
        pass # TODO
    
#    def test_getBackend_When_matches_by_hostname_Then_successful(self):
#        be = Backend('mrbun', '127.0.0.1', '6543', True)
#        when(self.db).getBackends().thenReturn([be])
#        self.assertEquals(be, self.tuner.getBackend())
#
#    def test_getBackend_When_matches_by_ipaddress_Then_successful(self):
#        self.tuner.hostname = '127.0.0.1'
#        be = Backend('not_mrbun', '127.0.0.1', '6543', True)
#        when(self.db).getBackends().thenReturn([be])
#        self.assertEquals(be, self.tuner.getBackend())
#
#    def test_getBackend_When_nomatch_by_hostname_Then_raise_exception(self):
#        be = Backend('not_mrbun', '127.0.0.1', '6543', True)
#        when(self.db).getBackends().thenReturn([be])
#        try:
#            self.tuner.getBackend()
#            self.fail('Expected error')
#        except Exception:
#            pass # SUCCESS
#
#    def test_getBackend_When_nomatch_by_ipaddress_Then_raise_exception(self):
#        self.tuner.hostname = '127.0.0.2'
#        be = Backend('mrbun', '127.0.0.1', '6543', True)
#        when(self.db).getBackends().thenReturn([be])
#        try:
#            self.tuner.getBackend()
#            self.fail('Expected error')
#        except Exception:
#            pass # SUCCESS


class CommercialBreakTest(unittest2.TestCase):
    
    def test_constructor(self):
        commercial = CommercialBreak(100, 200)
        self.assertTrue(commercial is not None)
        
    def test_constructor_StartAfterEndFailsAssertion(self):
        try:
            CommercialBreak(200, 100)
        except AssertionError, ae:
            log.debug('Error = %s' % ae)
            
    def test_isDuring_True(self):
        commercial = CommercialBreak(100, 200)
        self.assertTrue(commercial.isDuring(150))
    
    def test_isDuring_BeforeCommercialReturnsFalse(self):
        commercial = CommercialBreak(100, 200)
        self.assertFalse(commercial.isDuring(50))
    
    def test_isDuring_AfterCommercialReturnsFalse(self):
        commercial = CommercialBreak(100, 200)
        self.assertFalse(commercial.isDuring(350))


class RecordingScheduleTest(unittest2.TestCase):
    
    def test_starttime_DataFromNativeMySQL(self):
        data = {'starttime': datetime.timedelta(seconds=(1 * 60 * 60) + (2 * 60) + 3)}
        schedule = RecordingSchedule(data, Mock())
        self.assertEquals('010203', schedule.starttime())
        
    def test_endtime_DataFromNativeMySQL(self):
        data = {'endtime': datetime.timedelta(seconds=(1 * 60 * 60) + (2 * 60) + 3)}
        schedule = RecordingSchedule(data, Mock())
        self.assertEquals('010203', schedule.endtime())
        
    def test_startdate_DataFromNativeMySQL(self):
        data = {'startdate': datetime.date(2008, 11, 12)}
        schedule = RecordingSchedule(data, Mock())
        self.assertEquals('20081112', schedule.startdate())
        
    def test_enddate_DataFromNativeMySQL(self):
        data = {'enddate': datetime.date(2008, 11, 12)}
        schedule = RecordingSchedule(data, Mock())
        self.assertEquals('20081112', schedule.enddate())
        
    def test_episodeFilter_and_checkForDupesIn_read_from_and_written_to_dupin_field_correctly(self):
        data = {'dupin': CheckForDupesIn.ALL_RECORDINGS | EpisodeFilter.EXCLUDE_REPEATS_AND_GENERICS}
        schedule = RecordingSchedule(data, Mock())
        self.assertEquals(EpisodeFilter.EXCLUDE_REPEATS_AND_GENERICS, schedule.getEpisodeFilter())
        
        schedule.setEpisodeFilter(EpisodeFilter.NEW_EPISODES_ONLY)
        self.assertEquals(EpisodeFilter.NEW_EPISODES_ONLY, schedule.getEpisodeFilter())
        self.assertEquals(CheckForDupesIn.ALL_RECORDINGS, schedule.getCheckForDupesIn())
        
        schedule.setCheckForDupesIn(CheckForDupesIn.PREVIOUS_RECORDINGS)
        self.assertEquals(EpisodeFilter.NEW_EPISODES_ONLY, schedule.getEpisodeFilter())
        self.assertEquals(CheckForDupesIn.PREVIOUS_RECORDINGS, schedule.getCheckForDupesIn())
        
        schedule.setEpisodeFilter(EpisodeFilter.NONE)
        self.assertEquals(EpisodeFilter.NONE, schedule.getEpisodeFilter())
        self.assertEquals(CheckForDupesIn.PREVIOUS_RECORDINGS, schedule.getCheckForDupesIn())


class JobTest(unittest2.TestCase):

    def setUp(self):
        import util_mock
        p = Platform()
        langInfo = util_mock.XBMCLangInfo(p)
        self.translator = util_mock.Translator(p, langInfo)
        self.protocol = protocol.Protocol56()

    def test_moveToFrontOfQueue_Raises_Exeption_When_Job_Not_Queued(self):
        job = self.createJob(jobStatus=JobStatus.FINISHED)
        try:
            job.moveToFrontOfQueue()
        except StatusException, se:
            log.debug(se)
            self.assertTrue('queue' in str(se))

    def test_moveToFrontOfQueue_From_10_Of_10(self):
        # Setup
        db = Mock()
        conn = Mock()
        jobs = []
        for i in xrange(1, 11):
            job = self.createJob(conn=conn, db=db, id=i, jobStatus=JobStatus.QUEUED, jobType=JobType.COMMFLAG)
            job.scheduledRunTime = datetime.datetime.now().replace(year=(2000+i))
            jobs.append(job)
      
        when(db).getJobs(jobStatus=JobStatus.QUEUED).thenReturn(jobs)
        when(db).getJobs(jobType=JobType.COMMFLAG, jobStatus=JobStatus.QUEUED).thenReturn(jobs)

        import copy
        job = copy.copy(jobs[-1])
        
        # Test
        job.moveToFrontOfQueue()
        
        # Verify
        for i, j in enumerate(jobs[:-1]):
            log.debug('job %s = %s' % (i, j))
            self.assertTrue(2000 + (i+2), j.scheduledRunTime.year)
        log.debug('current job = %s' % job)
        self.assertTrue(2001, job.scheduledRunTime.year)

    def test_moveToFrontOfQueue_From_5_Of_10(self):
        # Setup
        jobPos = 4 # zero based index
        db = Mock()
        conn = Mock()
        jobs = []
        for i in xrange(1, 11):
            job = self.createJob(conn=conn, db=db, id=i, jobStatus=JobStatus.QUEUED, jobType=JobType.COMMFLAG)
            job.scheduledRunTime = datetime.datetime.now().replace(year=(2000+i))
            jobs.append(job)
            #log.debug('%s' % job)
      
        when(db).getJobs(jobStatus=JobStatus.QUEUED).thenReturn(jobs)
        when(db).getJobs(jobType=JobType.COMMFLAG, jobStatus=JobStatus.QUEUED).thenReturn(jobs)
        import copy
        job = copy.copy(jobs[jobPos])
        
        # Test
        job.moveToFrontOfQueue()
        
        # Verify
        # pushed back [1:4]
        for i, j in enumerate(jobs[:jobPos]):
            log.debug('job %s = %s' % (i, j))
            self.assertTrue(2000 + (i+2), j.scheduledRunTime.year)

        # moved to first in queue
        log.debug('current job = %s' % job)
        self.assertTrue(2001, job.scheduledRunTime.year)
        
        # unaffected jobs [5,10]
        for i, j in enumerate(jobs[jobPos+1:]):  
            log.debug('job %s = %s' % (i, j))
            self.assertTrue(2000 + (i+2), j.scheduledRunTime.year)

    def test_moveToFrontOfQueue_From_2_Of_2(self):
        # Setup
        db = Mock()
        conn = Mock()
        jobs = []
        for i in xrange(1, 3):
            job = self.createJob(conn=conn, db=db, id=i, jobStatus=JobStatus.QUEUED, jobType=JobType.COMMFLAG)
            job.scheduledRunTime = datetime.datetime.now().replace(year=(2000+i))
            jobs.append(job)
      
        when(db).getJobs(jobStatus=JobStatus.QUEUED).thenReturn(jobs)
        when(db).getJobs(jobType=JobType.COMMFLAG, jobStatus=JobStatus.QUEUED).thenReturn(jobs)
        
        import copy
        job = copy.copy(jobs[1])
        
        # Test
        job.moveToFrontOfQueue()
        
        # Verify
        for i, j in enumerate(jobs[:-1]):
            log.debug('job %s = %s' % (i, j))
            self.assertEquals(2000 + (i+2), j.scheduledRunTime.year)
        log.debug('current job = %s' % job)
        self.assertEquals(2001, job.scheduledRunTime.year)
           
    def test_getPositionInQueue_Position_Is_7_of_10(self):
        # Setup
        db = Mock()
        conn = Mock()
        jobs = []
        for i in xrange(1, 11):
            jobs.append(self.createJob(id=i, jobStatus=JobStatus.QUEUED, jobType=JobType.COMMFLAG))
            
        when(db).getJobs(jobStatus=JobStatus.QUEUED).thenReturn(jobs)
        when(db).getJobs(jobType=JobType.COMMFLAG, jobStatus=JobStatus.QUEUED).thenReturn(jobs)

        job = self.createJob(conn=conn, db=db, id=7, jobStatus=JobStatus.QUEUED, jobType=JobType.COMMFLAG)
        
        # Test
        pos, numJobs = job.getPositionInQueue()
        
        # Verify
        log.debug('Job is %d of %d' % (pos, numJobs))
        self.assertEquals(7, pos)
        self.assertEquals(10, numJobs)
    
    def test_getPositionInQueue_Position_Is_1_of_1(self):
        # Setup
        db = Mock()
        conn = Mock()
        
        job = self.createJob(conn=conn, db=db, jobStatus=JobStatus.QUEUED, jobType=JobType.COMMFLAG)
        when(db).getJobs(jobStatus=JobStatus.QUEUED).thenReturn([job])
        when(db).getJobs(jobType=JobType.COMMFLAG, jobStatus=JobStatus.QUEUED).thenReturn([job])
        
        # Test
        pos, numJobs = job.getPositionInQueue()
        
        # Verify
        log.debug('Job is %d of %d' % (pos, numJobs))
        self.assertEquals(1, pos)
        self.assertEquals(1, numJobs)
        
    def test_getPositionInQueue_RaisesException_JobStatus_Not_Queued(self):
        job = self.createJob(jobStatus=JobStatus.FINISHED)
        try:
            job.getPositionInQueue()
        except StatusException, se:
            log.debug(se)
            self.assertTrue('Finished' in str(se))
        
    def test_getPercentComplete_Finished_Job_Returns_100(self):
        job = self.createJob(jobStatus=JobStatus.FINISHED)
        self.assertEquals(100, job.getPercentComplete())
    
    def test_getPercentComplete_Pending_Job_Returns_0(self):
        job = self.createJob(jobStatus=JobStatus.PENDING)
        self.assertEquals(0, job.getPercentComplete())
    
    def test_getPercentComplete_Running_Job_Returns_57(self):
        job = self.createJob(jobStatus=JobStatus.RUNNING, jobType=JobType.COMMFLAG)
        job.comment = "76% Completed @ 13.9645 fps."
        self.assertEquals(76, job.getPercentComplete())

    def test_getPercentComplete_Raises_StatusException_WhenRunningButPercentCompletionNotAvailableYet(self):
        job = self.createJob(jobStatus=JobStatus.RUNNING, jobType=JobType.COMMFLAG)
        job.comment = "Logo detection"
        try:
            job.getPercentComplete()
        except StatusException, se:
            log.debug("%s" % se)
            
    def test_getCommFlagRate_Running_Job_Returns_FPS(self):
        job = self.createJob(jobStatus=JobStatus.RUNNING, jobType=JobType.COMMFLAG)
        job.comment = "76% Completed @ 13.9645 fps."
        rate = job.getCommFlagRate()
        log.debug('Comm flag rate = %s' % rate)
        self.assertAlmostEqual(13.9645, rate)
        
    def test_getCommFlagRate_Raises_StatusException_WhenRunningButCommFlagRateNotAvailableYet(self):
        job = self.createJob(jobStatus=JobStatus.RUNNING, jobType=JobType.COMMFLAG)
        job.comment = "Logo detection"
        try:
            job.getCommFlagRate()
        except StatusException, se:
            log.debug("%s" % se)
        
    def test_str_ShouldConvertToString(self):
        s = "%s"%self.createJob(jobStatus=JobStatus.QUEUED, jobType=JobType.SYSTEMJOB)
        log.debug('job = %s' % s)
        self.assertTrue('System' in s)
        self.assertTrue('Queued' in s)
        
    def test_isJobFor_ShouldReturnTrue(self):
        # Setup
        job = self.createJob()
        job.startTime = datetime.datetime(2009, 12, 5, 10, 20, 00)
        job.channelId = 1999
        
        data = [''] * self.protocol.recordSize()
        data[4]  = 1999
        data[11] = time.mktime(datetime.datetime(2009, 12, 5, 10, 20, 00).timetuple()) 
        program = RecordedProgram(data=data, settings=Mock(), translator=Mock(), platform=Mock(), protocol=self.protocol, conn=Mock())
        
        # Test & verify
        self.assertTrue(job.isJobFor(program))
        
    def test_isJobFor_ShouldReturnFalse_TimesDontMatch(self):
        # Setup
        job = self.createJob()
        job.startTime = datetime.datetime(2008, 11, 4, 23, 45, 00)
        job.channelId = 1999
        
        data = [''] * self.protocol.recordSize()
        data[4]  = 1999
        data[11] = time.mktime(datetime.datetime(2009, 12, 5, 10, 20, 00).timetuple()) 
        program = RecordedProgram(data=data, settings=Mock(), translator=Mock(), platform=Mock(), protocol=self.protocol, conn=Mock())
        
        # Test & verify
        self.assertFalse(job.isJobFor(program))

    def test_isJobFor_ShouldReturnFalse_ChannelIds_DontMatch(self):
        # Setup
        job = self.createJob()
        job.startTime = datetime.datetime(2008, 11, 4, 23, 45, 00)
        job.channelId = 200
        
        data = [''] * self.protocol.recordSize()
        data[4]  = 1999
        data[11] = time.mktime(datetime.datetime(2008, 11, 4, 23, 45, 00).timetuple()) 
        program = RecordedProgram(data=data, settings=Mock(), translator=Mock(), platform=Mock(), protocol=self.protocol, conn=Mock())
        
        # Test & verify
        self.assertFalse(job.isJobFor(program))
        
    def test_eq_TrueForSameObjectInstance(self):
        job = self.createJob()
        self.assertTrue(job == job)
    
    def test_eq_TrueForJobsWithTheSameId(self):
        job1 = self.createJob(id=99)
        job2 = self.createJob(id=99)
        self.assertTrue(job1 == job2)
    
    def test_eq_FalseForJobsWithDifferentIds(self):
        job1 = self.createJob(id=99)
        job2 = self.createJob(id=100)
        self.assertFalse(job1 == job2)
    
    def test_eq_FalseForInvalidType(self):
        job1 = self.createJob(id=99)
        job2 = "i am not of type Job"
        self.assertFalse(job1 == job2)
    
    def test_eq_FalseForNone(self):
        job1 = self.createJob(id=99)
        job2 = None
        self.assertFalse(job1 == job2)
        
    def createJob(self, conn=Mock(), db=Mock(), id=1, jobType=JobType.COMMFLAG, jobStatus=JobStatus.FINISHED):
        return Job(
            id=id,     
            channelId=2,     
            startTime=None,
            insertTime=None,
            jobType=jobType, 
            cmds=None, 
            flags=None, 
            jobStatus=jobStatus, 
            statusTime=None,
            hostname='localhost', 
            comment=None,
            scheduledRunTime=None, 
            translator=self.translator,
            conn=conn,
            db=db)        


class MythUrlTest(unittest2.TestCase):

    def test_When_url_has_hostname_Then_parse_successful(self):
        url = MythUrl('myth://twiggy:6543/var/lib/recordings/000_111222333444.mpg')
        self.assertEquals('twiggy', url.hostname())
        self.assertEquals('6543', url.port())
        self.assertEquals('/var/lib/recordings/000_111222333444.mpg', url.path())

    def test_When_url_has_ipaddress_Then_parse_successful(self):
        url = MythUrl('myth://192.168.233.212:6543/var/lib/recordings/000_111222333444.mpg')
        self.assertEquals('/var/lib/recordings/000_111222333444.mpg', url.path())
        self.assertEquals('6543', url.port())
        self.assertEquals('192.168.233.212', url.hostname())
        
    def test_When_url_invalid_Then_returns_None(self):
        url = MythUrl('myth:/192.168.233.212:6543/var/lib/recordings/000_111222333444.mpg')
        self.assertTrue(url.hostname() is None)
        self.assertTrue(url.path() is None)
        self.assertTrue(url.port() is None)

        
class BackendTest(unittest2.TestCase):

    def test_eq_True_by_reference(self):
        be = Backend('htpc', '127.0.0.1', '6543', True)
        self.assertTrue(be == be)
    
    def test_eq_by_value(self):
        bes = [Backend('htpc', '127.0.0.1', '6543', True),
               Backend('htpc', '127.0.0.1', '6543', False),
               Backend('htpc', '127.0.0.1', '8888', True),
               Backend('htpc', '127.0.0.2', '6543', True),
               Backend('slave', '127.0.0.1', '6543', True)]
        
        for i, be1 in enumerate(bes):
            for j, be2 in enumerate(bes):
                if i == j:
                    self.assertTrue(be1 == be2)
                else:
                    self.assertFalse(be1 == be2)
    
    def test_eq_False_by_type(self):
        self.assertFalse(Backend('slave', '127.0.0.1', '6543', True) == 'a string')
        self.assertFalse(Backend('slave', '127.0.0.1', '6543', True) == None)


if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest2.main()
