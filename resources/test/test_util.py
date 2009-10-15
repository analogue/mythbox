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
import threading
import time
import unittest
import util
import mythbox
import mythtv

from mockito import *
from platform import *
from util import BoundedEvictingQueue, lirc_hack
from util import synchronized, timed

log = logging.getLogger('mythtv.unittest')

# =============================================================================
class RunAsyncDecoratorTest(unittest.TestCase):
    
    from util import run_async

    @run_async
    def print_somedata(self):
        print 'starting print_somedata'
        time.sleep(2)
        print 'print_somedata: 2 sec passed'
        time.sleep(2)
        print 'print_somedata: 2 sec passed'
        time.sleep(2)
        print 'finished print_somedata'

    def test_run_async(self):
        t1 = self.print_somedata()
        print 'back in main'
        t2 = self.print_somedata()
        print 'back in main'
        t3 = self.print_somedata()
        print 'back in main'
        
        t1.join()
        t2.join()
        t3.join()

# =============================================================================
class ModuleTest(unittest.TestCase):

#    def formatSize(sizeKB, gb=False):
#        size = float(sizeKB)
#        if size > 1024*1000 and gb:
#            value = str("%.2f %s"% (size/(1024.0*1000.0), "GB"))
#        elif size > 1024:
#            value = str("%.2f %s"% (size/(1000.0), 'MB')) 
#        else:
#            value = str("%.2f %s"% (size, 'KB')) 
#        return re.sub(r'(?<=\d)(?=(\d\d\d)+\.)', ',', value)

    def test_formatSize(self):
        self.assertEquals("1,024.00 KB", util.formatSize(1024, False))
        self.assertEquals("100.00 GB", util.formatSize(1024*1000*100, True))
        self.assertEquals("100,000.00 MB", util.formatSize(1024*1000*100, False))
        self.assertEquals("1,000.00 GB", util.formatSize(1024*1000*1000, True))
        self.assertEquals("4,000.00 GB", util.formatSize(1024*1000*1000*4, True))
        self.assertEquals("8,000.00 GB", util.formatSize(1024*1000*1000*8, True))
        self.assertEquals("10,000.00 GB", util.formatSize(1024*1000*1000*10, True))
        self.assertEquals("100,000.00 GB", util.formatSize(1024*1000*1000*100, True))


    def test_decodeLongLong(self):
        self.assertEquals(0, util.decodeLongLong(0, 0))
        self.assertEquals(1, util.decodeLongLong(1, 0))
        self.assertEquals(0xffffffff00000001, util.decodeLongLong(1, 0xffffffff))
        self.assertEquals(0x00000000ffffffff, util.decodeLongLong(0xffffffff, 0x0))
        self.assertEquals(0xffffffff00000000, util.decodeLongLong(0x0, 0xffffffff))
        self.assertEquals(0xffffffffffffffff, util.decodeLongLong(0xffffffff, 0xffffffff))
    
    def test_encodeLongLong(self):
        lowWord, highWord = util.encodeLongLong(0L)
        self.assertEquals(0, lowWord)
        self.assertEquals(0, highWord)

        lowWord, highWord = util.encodeLongLong(1L)
        self.assertEquals(1, lowWord)
        self.assertEquals(0, highWord)
        
        lowWord, highWord = util.encodeLongLong(0xffffffff00000001)
        self.assertEquals(1, lowWord)
        self.assertEquals(0xffffffff, highWord)

        lowWord, highWord = util.encodeLongLong(0x00000000ffffffff)
        self.assertEquals(0xffffffff, lowWord)
        self.assertEquals(0x0, highWord)

        lowWord, highWord = util.encodeLongLong(0xffffffffffffffff)
        self.assertEquals(0xffffffff, lowWord)
        self.assertEquals(0xffffffff, highWord)
        
    def test_frames2seconds(self):
        s = util.frames2seconds(1000, 29.97)
        log.debug('1000 frames @ 29.97fps = %s seconds' % s)
        self.assertEquals(33.37, s)
        
        s = util.frames2seconds(0, 29.97)
        log.debug('0 frames @ 29.97fps = %s seconds' % s)
        self.assertEquals(0.0, s)
        
        s = util.frames2seconds(99999999L, 29.97)
        log.debug('99999999L frames @ 29.97fps = %s seconds' % s)
        self.assertEquals(3336669.97, s)
    
    def test_seconds2frames(self):
        s = util.seconds2frames(33.37, 29.97)
        log.debug('33.37 seconds @ 29.97fps = %s frames' % s)
        self.assertEquals(1000L, s)

        s = util.seconds2frames(0, 29.97)
        log.debug('0 seconds @ 29.97fps = %s frames' % s)
        self.assertEquals(0L, s)
        
        s = util.seconds2frames(3336669.97, 29.97)
        log.debug('3336669.97 seconds @ 29.97fps = %s frames' % s)
        self.assertEquals(99999999L, s)
    
    def test_formatSeconds(self):
        self.assertEquals('0s', util.formatSeconds(0.00))
        self.assertEquals('1s', util.formatSeconds(1.99))
        self.assertEquals('5m', util.formatSeconds(60*5))
        self.assertEquals('5m 45s', util.formatSeconds(60*5+45))
        self.assertEquals('3h 5m 45s', util.formatSeconds(3*60*60 + 60*5 + 45))
        self.assertEquals('3h', util.formatSeconds(3*60*60))
        self.assertEquals('3h 59m', util.formatSeconds(3*60*60 + 60*59))
        self.assertEquals('3h 5s', util.formatSeconds(3*60*60 + 5))

    def test_which_ExecutableFound(self):
        platform = mythbox.getPlatform()
        if type(platform) == mythbox.WindowsPlatform:
            exe = "cmd.exe"
        elif type(platform) in (mythbox.UnixPlatform, mythbox.MacPlatform):
            exe = "true"
        else:
            log.warn("Skipping test. Platform not supported")
            return
        exepath = util.which(exe)
        log.debug('which found %s' % exepath)
        self.assertFalse(exepath is None)    

    def test_which_ExecutableNotFound(self):
        platform = mythbox.getPlatform()
        if type(platform) == mythbox.WindowsPlatform:
            exe = "bogus_executable_name.exe"
        elif type(platform) in (mythbox.UnixPlatform, mythbox.MacPlatform):
            exe = "bogus_executable_name"
        else:
            log.warn("Skipping test. Platform not supported")
            return
        exepath = util.which(exe)
        self.assertTrue(exepath is None)    

    def test_slice_When_items_empty_Then_returns_num_empty_lists(self):
        items = []
        queues = util.slice(items, 4)
        self.assertEquals(4, len(queues))
        for q in queues:
            self.assertTrue(len(q) == 0)
    
    def test_slice_When_items_lt_num_Then_returns_num_minus_items_empty_lists_at_end(self):
        items = [1,2]
        queues = util.slice(items, 4)
        self.assertEquals(4, len(queues))
        self.assertTrue(len(queues[0]) == 1 and queues[0][0] == 1)
        self.assertTrue(len(queues[1]) == 1 and queues[1][0] == 2)
        self.assertTrue(len(queues[2]) == 0 and len(queues[3]) == 0)
        
    def test_slice_When_items_eq_num_Then_returns_num_lists_with_each_item(self):
        items = [1,2]
        queues = util.slice(items, 2)
        self.assertEquals(2, len(queues))
        self.assertTrue(len(queues[0]) == 1 and queues[0][0] == 1)
        self.assertTrue(len(queues[1]) == 1 and queues[1][0] == 2)
        
    def test_slice_When_items_gt_num_Then_returns_num_lists_with_items_wrapping_around(self):
        items = [1,2,3,4]
        queues = util.slice(items, 2)
        self.assertEquals(2, len(queues))
        self.assertTrue(len(queues[0]) == 2 and queues[0][0] == 1 and queues[0][1] == 3)
        self.assertTrue(len(queues[1]) == 2 and queues[1][0] == 2 and queues[1][1] == 4)
        
# =============================================================================
class LircHackDecoratorTest(unittest.TestCase):

    def setUp(self):
        util._lircEvents = util.BoundedEvictingQueue(2)
        self.platform = MockPlatform()
        self.settings = Mock()
        
    @lirc_hack
    def onAction(self, action):
        return True

    @lirc_hack
    def onClick(self, controlId):
        return True
    
    class Action(object):
        
        def __init__(self, id): 
            self.id = id
            
        def getId(self): 
            return self.id
                
    def test_When_two_events_are_close_together_Then_the_second_event_gets_consumed(self):
        # Setup
        when(self.settings).getBoolean(any()).thenReturn(True)
        
        # Test
        import ui
        result1 = self.onAction(LircHackDecoratorTest.Action(ui.ACTION_PREVIOUS_MENU))
        time.sleep(0.1)
        result2 = self.onAction(LircHackDecoratorTest.Action(ui.ACTION_PREVIOUS_MENU))
        
        # Verify
        self.assertTrue(result1)
        self.assertTrue(result2 is None)
    
    def test_When_two_events_are_far_apart_Then_both_events_are_left_alone(self):
        # Setup
        when(self.settings).getBoolean(any()).thenReturn(True)
        
        # Test
        import ui
        result1 = self.onAction(LircHackDecoratorTest.Action(ui.ACTION_PREVIOUS_MENU))
        time.sleep(1.1)
        result2 = self.onAction(LircHackDecoratorTest.Action(ui.ACTION_PREVIOUS_MENU))
        
        # Verify
        self.assertTrue(result1)
        self.assertTrue(result2)
    
# =============================================================================
class TimedDecoratorTest(unittest.TestCase):
    
    def test_DecoratorPrintsOutWarningWhenExecutionTimeExceedsOneSecond(self):
        self.foo()
        # observe results
        
    @timed
    def foo(self):
        log.debug('waiting 1.2 seconds...')
        time.sleep(1.2)

# =============================================================================
class SynchronizedDecoratorTest(unittest.TestCase):

    @synchronized
    def foo(self):
        log.debug('enter %d' % self.i)
        self.assertEquals(100, self.i)
        self.i = self.i + 1
        time.sleep(0.25)
        self.i = self.i - 1
        self.assertEquals(100, self.i)
        log.debug('exit %d' % self.i)
        
    def runner(self):
        self.foo()
    
    def test_synhronized(self):
        self.i = 100
            
        threads = []
        
        for x in range(1,10):
            t = threading.Thread(name='%d'%x, target=self.runner)
            threads.append(t)
            t.start()
            log.debug('started thread %s' % t)
            
        for t in threads:
            t.join(timeout=999)
            log.debug('joined thread %s' % t)

# =============================================================================    
class NativeTranslatorTest(unittest.TestCase):

    def test_get_ByIntegerIdReturnsString(self):
        translator = util.NativeTranslator(os.getcwd())
        s = translator.get(0)
        log.debug('localized = %s' % s)
        self.assertEquals('TODO', s)
        
    def test_get_ByStringReturnsString(self):
        translator = util.NativeTranslator(os.getcwd())
        s = translator.get('MythBox')
        log.debug('localized = %s' % s)
        self.assertEquals('MythBox', s)
             
# =============================================================================
class BoundedEvictingQueueTest(unittest.TestCase):
    
    def test_put_FillingToCapacityPlusOneEvictsFirstItem(self):
        q = BoundedEvictingQueue(3)
        q.put(1)
        q.put(2)
        q.put(3)
        self.assertTrue(q.full())
        q.put(4)
        self.assertTrue(q.full())
        self.assertEquals(3, q.qsize())
        self.assertEquals(2, q.get())
        self.assertFalse(q.full())
        self.assertEquals(3, q.get())
        self.assertEquals(4, q.get())
        self.assertTrue(q.empty())
        
# =============================================================================
#
# Requires interactivity 
#        
#class OnDemandConfigTest(unittest.TestCase):
#            
#    def test_get_NonExistentKey(self):
#        config = util.OnDemandConfig('crap.ini')
#        value = config.get('blah')
#        log.debug('Value = %s' % value)
        
# =============================================================================
class MockPlatform(mythbox.Platform):
    """
    Mock platform impl that directs unit tests to load resources from the  
    ./resources/test/mock* directories 
    """
#    def getXbmcRoot(self):
#        return os.path.join(os.getcwd(), 'resources', 'test', 'test_util', 'xbmc')
#
#    def getXbmcUserSettingsRoot(self):
#        return os.path.join(os.getcwd(), 'resources', 'test', 'test_util', 'dotxbmc')
    
    def addLibsToSysPath(self):
        pass
    
    def getName(self):
        return "N/A"
    
    def getScriptDir(self):
        return os.path.join(os.getcwd(), 'resources', 'test', 'test_util', 'xbmc')

    def getScriptDataDir(self):
        return os.path.join(os.getcwd(), 'resources', 'test', 'test_util', 'dotxbmc')
    
    def getHostname(self):
        return 'hostname'
        
    def isUnix(self):
        return True
    
    def getPythonMySqlSharedObjectDir(self):
        pass
    
    def getPythonMySqlBindingsDir(self):
        pass

    def getFFMpegPath(self):
        return ''

    def getDefaultRecordingsDir(self):
        return ''
        
# =============================================================================
if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
