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
import os
import player
import tempfile
import time
import unittest

from mockito import *
from domain import CommercialBreak
from player import EdlCommercialSkipper
from player import PositionTracker
from player import TrackerSample
from player import TrackingCommercialSkipper

log = logging.getLogger('mythtv.unittest')

# =============================================================================
class PositionTrackerTest(unittest.TestCase):

    def test_constructor(self):
        player = Mock()
        tracker = PositionTracker(player)
        self.assertEquals(0.0, tracker.getLastPosition())
        self.assertTrue(len(tracker.getHistory(2)) == 0)

    def test_getHistory_howFarBack_bounds(self):
        player = Mock()
        tracker = PositionTracker(player)
        self.assertTrue(len(tracker.getHistory(2)) == 0)
        self.assertTrue(len(tracker.getHistory(0)) == 0)
        self.assertTrue(len(tracker.getHistory(999)) == 0)
        
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
        self.assertTrue(tracker.getLastPosition() <= playDuration)
        self.assertTrue((playDuration - 1) < tracker.getLastPosition())
        for i in range(1, PositionTracker.HISTORY_SECS):
            self.assertTrue(i * (1000/player.SLEEP_MILLIS) <= len(tracker.getHistory(i)))

# =============================================================================        
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

# =============================================================================
class MythPlayerTest(unittest.TestCase):
    
    def test_playRecording(self):
        pass
    
#        # Setup
#        player = MythPlayer()
#        program = Mock()
#        conn = Mock()
#        
#        when(program).title().thenReturn('vangelis')
#        when(program).hasCommercials().thenReturn(False)
#        #commBreaks = [domain.CommercialBreak(100, 200)]
#        #when(program).getCommercials().thenReturn(commBreaks)
#        when(program).fullTitle().thenReturn('the return')
#        when(program).getBookmark().thenReturn(0)
#        when(program).getLocalPath().thenReturn('/usr/movie.mpg')
#        
#        self.assertEquals(0, program.getBookmark())
#        self.assertEquals('the return', program.fullTitle())
#    
#        # Test
#        player.playRecording(program)
#        
#        # Verify
            
# =============================================================================
class EdlCommercialSkipperTest(unittest.TestCase):
    
    def test_constructor_SkipFileCreatedForRecordingWithCommercials(self):
        # Setup
        player = Mock()
        program = Mock()
        commBreaks = [domain.CommercialBreak(100,200), 
                      domain.CommercialBreak(1000.23,1100.99), 
                      domain.CommercialBreak(5000.123, 6000.456)]
        when(program).getCommercials().thenReturn(commBreaks)
        when(program).getLocalPath().thenReturn(os.path.join(tempfile.gettempdir(), 'movie.mpg'))

        # Test
        EdlCommercialSkipper(player, program)
        
        # Verify
        edlFile = os.path.join(tempfile.gettempdir(), 'movie.edl')
        self.assertTrue(os.path.isfile(edlFile))
        f = open(edlFile, 'r')
        self.assertEquals('100.00 200.00 0', f.readline().strip())
        self.assertEquals('1000.23 1100.99 0', f.readline().strip())
        self.assertEquals('5000.12 6000.46 0', f.readline().strip())
        f.close()
        os.remove(edlFile)

    def test_constructor_SkipFileNotCreatedForRecordingWithNoCommercials(self):
        # Setup
        player = Mock()
        program = Mock()
        when(program).getCommercials().thenReturn([])
        when(program).getLocalPath().thenReturn(os.path.join(tempfile.gettempdir(), 'movie2.mpg'))

        # Test
        EdlCommercialSkipper(player, program)
        
        # Verify
        edlFile = os.path.join(tempfile.gettempdir(), 'movie2.edl')
        self.assertFalse(os.path.isfile(edlFile))

# =============================================================================
class BookmarkerTest(unittest.TestCase):
    
    def test_constructor(self):
        # TODO
        pass
    
# =============================================================================
class TrackingCommercialSkipperTest(unittest.TestCase):
    
    def setUp(self):
        self.tracker = Mock()
        
        self.player = Mock()
        when(self.player).getTracker().thenReturn(self.tracker)
        
        self.program = Mock()
        when(self.program).title().thenReturn('movie.mpg')
        
    def test_RecordingWithNoCommBreaksDoesNothing(self):
        # Setup
        log.debug('Running no comm breaks test...')
        when(self.player).isPlaying().thenReturn(True)
        when(self.program).getCommercials().thenReturn([])
        when(self.player).getTime().thenReturn(500)
        
        # Test
        skipper = TrackingCommercialSkipper(self.player, self.program)
        skipper.onPlayBackStarted()
        time.sleep(1)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(0)).seekTime(any())

    def test_PlayerNeverEntersAnyCommBreaks(self):
        # Setup
        log.debug('Running never enters comm breaks test...')
        when(self.player).isPlaying().thenReturn(True)
        when(self.program).getCommercials().thenReturn([CommercialBreak(100, 200), CommercialBreak(600, 700)])
        when(self.player).getTime().thenReturn(500)
        
        # Test
        skipper = TrackingCommercialSkipper(self.player, self.program)
        skipper.onPlayBackStarted()
        time.sleep(2)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(0)).seekTime(any())

    def test_PlayerEntersCommBreakCloseToBeginningSkipsCommercial(self):
        # Setup
        log.debug('Running enters comm break test...')
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
        skipper = TrackingCommercialSkipper(self.player, self.program)
        skipper.onPlayBackStarted()
        time.sleep(1)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(1)).seekTime(any())

    def test_PlayerEntersMidPointInCommBreakDoesntSkipCommercial(self):
        # Setup
        log.debug('Running enters midpoint comm break test...')
        when(self.player).isPlaying().thenReturn(True)
        when(self.program).getCommercials().thenReturn([CommercialBreak(1000, 2000)])
        
        # player in middle of commercial
        when(self.player).getTime().thenReturn(1500)
        
        # mock a valid tracker history
        trackerHistory = []
        for x in range(1490, 1500):
            trackerHistory.append(TrackerSample(time.time() + (x-1490), x))
        when(self.tracker).getHistory(any()).thenReturn(trackerHistory)
        
        # Test
        skipper = TrackingCommercialSkipper(self.player, self.program)
        skipper.onPlayBackStarted()
        time.sleep(1)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(0)).seekTime(any())
        
    def test_PlayerSkippingAroundWhenEntersCommBreakDoesntSkipCommercial(self):
        # Setup
        log.debug('Running enters comm break and user not skipping around test...')
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
        skipper = TrackingCommercialSkipper(self.player, self.program)
        skipper.onPlayBackStarted()
        time.sleep(1)
        when(self.player).isPlaying().thenReturn(False)
        skipper.onPlayBackStopped()
        
        # Verify
        verify(self.player, times(0)).seekTime(any())        

# =============================================================================    
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
