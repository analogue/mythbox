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
import time
import unittest2 as unittest

from mockito import Mock, when, verify, any, times
from mythbox.mythtv.domain import CommercialBreak
from mythbox.ui.player import PositionTracker, TrackerSample, \
    TrackingCommercialSkipper, SLEEP_MILLIS

log = logging.getLogger('mythbox.unittest')


class PositionTrackerTest(unittest.TestCase):

    def test_constructor(self):
        player = Mock()
        tracker = PositionTracker(player)
        self.assertEqual(0.0, tracker.getLastPosition())
        self.assertEqual(0, len(tracker.getHistory(2)))

    def test_getHistory_howFarBack_bounds(self):
        player = Mock()
        tracker = PositionTracker(player)
        self.assertEqual(0, len(tracker.getHistory(2)))
        self.assertEqual(0, len(tracker.getHistory(0)))
        self.assertEqual(0, len(tracker.getHistory(999)))
        
    def test_functional(self):
        # Setup
        playDuration = 5
        p = MockPlayer(playDuration)
        
        # Test
        tracker = PositionTracker(p)
        tracker.onPlayBackStarted()
        time.sleep(playDuration)
        tracker.onPlayBackStopped()
        
        # HACK: Python thread wackyness..maybe upgrade to 2.5 will fix it. 
        #       Waiting for thread to exit
        time.sleep(0.5)
        
        # Verify
        self.assertLessEqual(tracker.getLastPosition(), playDuration)
        self.assertLess(playDuration - 1, tracker.getLastPosition())
        for i in range(1, PositionTracker.HISTORY_SECS):
            self.assertLessEqual(i * (1000/SLEEP_MILLIS), len(tracker.getHistory(i)))


class MockPlayer(object):
    
    def __init__(self, duration):
        self.timestamp = time.time()
        self.duration = duration
        
    def isPlaying(self):
        if time.time() < self.timestamp + self.duration:
            return True
        else:
            return False
        
    def getTime(self):
        return time.time() - self.timestamp


class TrackingCommercialSkipperTest(unittest.TestCase):
    
    def setUp(self):
        self.tracker = Mock()
        
        self.translator = Mock()
        when(self.translator).get(any()).thenReturn('some %s string')
        
        self.player = Mock()
        self.player.tracker = self.tracker
        
        self.program = Mock()
        when(self.program).title().thenReturn('movie.mpg')
        
    def test_RecordingWithNoCommBreaksDoesNothing(self):
        # Setup
        when(self.player).isPlaying().thenReturn(True)
        when(self.program).getCommercials().thenReturn([])
        when(self.player).getTime().thenReturn(500)
        
        # Test
        skipper = TrackingCommercialSkipper(self.player, self.program, self.translator)
        skipper.onPlayBackStarted()
        time.sleep(1)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(0)).seekTime(any())

    def test_PlayerNeverEntersAnyCommBreaks(self):
        # Setup
        when(self.player).isPlaying().thenReturn(True)
        when(self.program).getCommercials().thenReturn([CommercialBreak(100, 200), CommercialBreak(600, 700)])
        when(self.player).getTime().thenReturn(500)
        
        # Test
        skipper = TrackingCommercialSkipper(self.player, self.program, self.translator)
        skipper.onPlayBackStarted()
        time.sleep(2)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(0)).seekTime(any())

    def test_PlayerEntersCommBreakCloseToBeginningSkipsCommercial(self):
        # Setup
        when(self.player).isPlaying().thenReturn(True)
        when(self.program).getCommercials().thenReturn([CommercialBreak(500, 2500)])
        
        # close to beginning = within 2 secs from start of commercial
        when(self.player).getTime().thenReturn(501).thenReturn(2501)
        
        # mock a valid tracker history
        trackerHistory = []
        for x in range(490, 501):
            trackerHistory.append(TrackerSample(time.time() + x, x))
        when(self.tracker).getHistory(any()).thenReturn(trackerHistory)
        
        # Test
        skipper = TrackingCommercialSkipper(self.player, self.program, self.translator)
        skipper.onPlayBackStarted()
        time.sleep(1)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(1)).seekTime(any())

    def test_PlayerSkippingAroundWhenEntersCommBreakDoesntSkipCommercial(self):
        # Setup
        when(self.player).isPlaying().thenReturn(True)
        when(self.program).getCommercials().thenReturn([CommercialBreak(500, 600)])
        
        # close to beginning = within 2 secs from start of commercial
        when(self.player).getTime().thenReturn(501).thenReturn(502).thenReturn(504).thenReturn(505)
        
        # mock a valid tracker history
        trackerHistory = []
        for x in range(499, 500):
            trackerHistory.append(TrackerSample(time.time() + (x - 499), x))
        when(self.tracker).getHistory(any()).thenReturn(trackerHistory)
        
        # Test
        skipper = TrackingCommercialSkipper(self.player, self.program, self.translator)
        skipper.onPlayBackStarted()
        time.sleep(1)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(0)).seekTime(any())        


if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
