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
import time
import unittest2 as unittest
import mythboxtest

#from mockito import Mock, when, any
from mythbox.util import *
from mythbox.platform import getPlatform, Platform, WindowsPlatform, MacPlatform, UnixPlatform

log = mythboxtest.getLogger('mythbox.unittest')


class RunAsyncDecoratorTest(unittest.TestCase):
    
    @run_async
    def print_somedata(self):
        log.debug('starting print_somedata')
        time.sleep(2)
        log.debug('print_somedata: 2 sec passed')
        time.sleep(2)
        log.debug('print_somedata: 2 sec passed')
        time.sleep(2)
        log.debug('finished print_somedata')

    def test_run_async(self):
        t1 = self.print_somedata()
        log.debug('back in main after t1 spawned')
        t2 = self.print_somedata()
        log.debug('back in main after t2 spawned')
        t3 = self.print_somedata()
        log.debug('back in main after t3 spawned')
        
        t1.join()
        t2.join()
        t3.join()
        # TODO: assertions

    def test_waitForWorkersToDie(self):
        # setup
        clearWorkers()
        t1 = self.print_somedata()
        log.debug('back in main after t1 spawned')
        t2 = self.print_somedata()
        log.debug('back in main after t2 spawned')
        t3 = self.print_somedata()
        log.debug('back in main after t3 spawned')
        
        # test
        waitForWorkersToDie()
        
        # verify
        self.assertFalse(t1.isAlive())
        self.assertFalse(t2.isAlive())
        self.assertFalse(t3.isAlive())


class CoalesceDecoratorTest(unittest.TestCase):
    
    def setUp(self):
        self.barTimes = 0
        self.fooTimes = 0
        self.bazTimes = 0
        
    @coalesce
    def foo(self, delay=0.5):
        self.fooTimes += 1
        time.sleep(delay)

    @run_async
    @coalesce
    def bar(self, delay=2):
        self.barTimes += 1
        time.sleep(delay)

    @run_async
    @coalesce
    def baz(self, delay=2):
        self.bazTimes += 1
        time.sleep(delay)
        
    def test_When_foo_coalesced_on_single_thread_Then_acts_like_plain_old_synchronous_method_call(self):
        self.foo()
        self.foo()
        self.foo()
        self.assertEquals(3, self.fooTimes)

    def test_When_foo_called_by_two_threads_Then_thread1_runs_foo_and_thread2_returns_immediately(self):
        t1 = self.bar(2)
        time.sleep(0.5)
        t2 = self.bar()
        t1.join()
        t2.join()
        self.assertEquals(1, self.barTimes)
        
    def test_When_bar_called_by_bunch_of_threads_Then_thread1_runs_bar_and_all_others_return_immediately(self):
        t = []
        for i in range(0,20):
            t.append(self.bar())
        
        for i in range(0,20):
            t[i].join()
        
        self.assertEquals(1, self.barTimes)
        
    def test_When_previous_calls_have_been_coalesced_and_completed_and_bar_is_called_Then_runs_bar_again(self):
        t1 = self.bar(2)
        time.sleep(0.5)
        t2 = self.bar()  # coalesced
        self.assertEquals(1, self.barTimes)

        time.sleep(2)  # expire 
        t3 = self.bar(1)
        t1.join()
        t2.join()
        t3.join()
        self.assertEquals(2, self.barTimes)

    def test_When_coalescing_bar_Then_should_have_no_affect_on_coalescing_baz(self):
        t1 = self.bar(2)
        t3 = self.bar()
        
        t2 = self.baz(2)
        t4 = self.baz()
        
        t1.join()
        t2.join()
        t3.join()
        t4.join()
        
        self.assertEquals(1, self.barTimes)
        self.assertEquals(1, self.bazTimes)


class ModuleTest(unittest.TestCase):

    def test_to_kwargs_When_args_not_empty_Then_returns_dict_with_args(self):

        class Boo(object):
            
            def __init__(self, *args, **kwargs):
                self.one = "1"
                self.two = "2"
                self.three = "3"

        obj = Boo()
        kwargs = to_kwargs(obj, ['three', 'two', 'one'])
        self.assertTrue(kwargs['one'] == obj.one)
        self.assertTrue(kwargs['two'] == obj.two)
        self.assertTrue(kwargs['three'] == obj.three)

    def test_my_understanding_of_mixing_kwargs_with_double_asterisk_on_method_invocation(self):

        def foo(a=1, b=2, c=3):
            self.assertTrue(a == 5)
            self.assertTrue(b == 6)
            self.assertTrue(c == 7)
            
        foo(a=5, **{'b':6, 'c':7})
        
    def test_formatSize(self):
        self.assertEquals("1,024.00 KB", formatSize(1024, False))
        self.assertEquals("100.00 GB", formatSize(1024*1000*100, True))
        self.assertEquals("100,000.00 MB", formatSize(1024*1000*100, False))
        self.assertEquals("1,000.00 GB", formatSize(1024*1000*1000, True))
        self.assertEquals("4,000.00 GB", formatSize(1024*1000*1000*4, True))
        self.assertEquals("8,000.00 GB", formatSize(1024*1000*1000*8, True))
        self.assertEquals("10,000.00 GB", formatSize(1024*1000*1000*10, True))
        self.assertEquals("100,000.00 GB", formatSize(1024*1000*1000*100, True))

    def test_formatSeconds(self):
        self.assertEquals('0s', formatSeconds(0.00))
        self.assertEquals('1s', formatSeconds(1.99))
        self.assertEquals('5m', formatSeconds(60*5))
        self.assertEquals('5m 45s', formatSeconds(60*5+45))
        self.assertEquals('3h 5m 45s', formatSeconds(3*60*60 + 60*5 + 45))
        self.assertEquals('3h', formatSeconds(3*60*60))
        self.assertEquals('3h 59m', formatSeconds(3*60*60 + 60*59))
        self.assertEquals('3h 5s', formatSeconds(3*60*60 + 5))

    def test_which_ExecutableFound(self):
        platform = getPlatform()
        if type(platform) == WindowsPlatform:
            exe = "cmd.exe"
        elif type(platform) in (UnixPlatform, MacPlatform):
            exe = "true"
        else:
            log.warn('Skipping test. Platform not supported')
            return
        exepath = which(exe)
        log.debug('which found %s' % exepath)
        self.assertFalse(exepath is None)    

    def test_which_ExecutableNotFound(self):
        platform = getPlatform()
        if type(platform) == WindowsPlatform:
            exe = "bogus_executable_name.exe"
        elif type(platform) in (UnixPlatform, MacPlatform):
            exe = "bogus_executable_name"
        else:
            log.warn("Skipping test. Platform not supported")
            return
        exepath = which(exe)
        self.assertTrue(exepath is None)    

    def test_slice_When_items_empty_Then_returns_num_empty_lists(self):
        items = []
        queues = slice(items, 4)
        self.assertEquals(4, len(queues))
        for q in queues:
            self.assertTrue(len(q) == 0)
    
    def test_slice_When_items_lt_num_Then_returns_num_minus_items_empty_lists_at_end(self):
        items = [1,2]
        queues = slice(items, 4)
        self.assertEquals(4, len(queues))
        self.assertTrue(len(queues[0]) == 1 and queues[0][0] == 1)
        self.assertTrue(len(queues[1]) == 1 and queues[1][0] == 2)
        self.assertTrue(len(queues[2]) == 0 and len(queues[3]) == 0)
        
    def test_slice_When_items_eq_num_Then_returns_num_lists_with_each_item(self):
        items = [1,2]
        queues = slice(items, 2)
        self.assertEquals(2, len(queues))
        self.assertTrue(len(queues[0]) == 1 and queues[0][0] == 1)
        self.assertTrue(len(queues[1]) == 1 and queues[1][0] == 2)
        
    def test_slice_When_items_gt_num_Then_returns_num_lists_with_items_wrapping_around(self):
        items = [1,2,3,4]
        queues = slice(items, 2)
        self.assertEquals(2, len(queues))
        self.assertTrue(len(queues[0]) == 2 and queues[0][0] == 1 and queues[0][1] == 3)
        self.assertTrue(len(queues[1]) == 2 and queues[1][0] == 2 and queues[1][1] == 4)
        

class TimedDecoratorTest(unittest.TestCase):
    
    def test_DecoratorPrintsOutWarningWhenExecutionTimeExceedsOneSecond(self):
        self.foo()
        # observe results
        
    @timed
    def foo(self):
        log.debug('waiting 1.2 seconds...')
        time.sleep(1.2)


class SynchronizedDecoratorTest(unittest.TestCase):

    def setUp(self):
        self.fooLock = 0
        self.barLock = 0
        self.bazLock = 0
        
    @synchronized
    def foo(self, delay=0.5):
        self.assertEquals(0, self.fooLock)
        self.fooLock += 1
        self.assertEquals(1, self.fooLock)
        
        time.sleep(delay)
        
        self.assertEquals(1, self.fooLock)
        self.fooLock -= 1
        self.assertEquals(0, self.fooLock)

    @run_async
    @synchronized
    def bar(self, delay=0.5):
        self.assertEquals(0, self.barLock)
        self.barLock += 1
        self.assertEquals(1, self.barLock)
        
        time.sleep(delay)
        
        self.assertEquals(1, self.barLock)
        self.barLock -= 1
        self.assertEquals(0, self.barLock)

    @run_async
    @synchronized
    def baz(self, delay=0.5):
        self.assertEquals(1, self.barLock)  # verify bar() is getting executed concurrently
        time.sleep(delay)
        self.assertEquals(1, self.barLock)  # verify bar() is getting executed concurrently        
    
    def test_When_foo_synchronized_on_single_thread_Then_acts_like_plain_old_synchronous_method_call(self):
        self.foo()
        self.foo()
        self.foo()
        
    def test_When_bar_called_from_multiple_threads_Then_access_is_synchronized(self):
        t1 = self.bar()
        t2 = self.bar()
        t3 = self.bar()
        t1.join()
        t2.join()
        t3.join()
        # assertions are internal to bar()
        
    def test_When_syncing_on_bar_Then_doesnt_affect_syncing_on_baz(self):
        t1 = self.bar(5)
        time.sleep(1)
        t4 = self.baz(1)
        t5 = self.baz(1)
        t6 = self.baz(1)
        
        t1.join()
        
        t4.join()
        t5.join()
        t6.join()
        # assertions are internal to baz()
        

class NativeTranslatorTest(unittest.TestCase):

    def test_get_ByIntegerIdReturnsString(self):
        translator = NativeTranslator(os.getcwd())
        s = translator.get(0)
        log.debug('localized = %s' % s)
        self.assertEquals('TODO', s)
        
    def test_get_ByStringReturnsString(self):
        translator = NativeTranslator(os.getcwd())
        s = translator.get('MythBox')
        log.debug('localized = %s' % s)
        self.assertEquals('MythBox', s)
        
    def test_get_ByUnicodeStringReturnsUnicodeString(self):
        translator = NativeTranslator(os.getcwd())
        s = translator.get(u'MythBox')
        #log.debug('localized = %s' % s)
        self.assertEquals(u'MythBox', s)
              

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
        

#
# Requires interactivity 
#        
#class OnDemandConfigTest(unittest.TestCase):
#            
#    def test_get_NonExistentKey(self):
#        config = util.OnDemandConfig('crap.ini')
#        value = config.get('blah')
#        log.debug('Value = %s' % value)
        

class MockPlatform(Platform):
    """
    Mock platform impl that directs unit tests to load resources from the  
    ./resources/test/mock* directories 
    """
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
    
    def getDefaultRecordingsDir(self):
        return ''


class BidiIteratorTest(unittest.TestCase):
    
    def test_When_list_empty_Then_raise_StopIteration(self):
        self.failUnlessRaises(StopIteration, BidiIterator([]).next)
        self.failUnlessRaises(StopIteration, BidiIterator([]).previous)
        self.failUnlessRaises(StopIteration, BidiIterator([]).current)
        self.assertTrue(BidiIterator([]).index() is None)
        
    def test_When_next_and_len_is_1_Then_return_1(self):
        bi = BidiIterator(['a'])
        self.assertEquals('a', bi.next())
        self.assertEquals('a', bi.current())
        self.assertEquals(0, bi.index())
    
    def test_When_previous_and_len_is_1_Then_raise_StopIteration(self):
        self.failUnlessRaises(StopIteration, BidiIterator(['a']).previous)

    def test_When_next_and_reach_end_of_list_Then_raise_StopIteration(self):
        bi = BidiIterator(['a'])
        self.assertEquals('a', bi.next())
        self.failUnlessRaises(StopIteration, bi.next)

    def test_When_many_next_and_reach_end_of_list_Then_raise_StopIteration(self):
        bi = BidiIterator(['a','b','c','d'])
        self.assertEquals('a', bi.next())
        self.assertEquals('b', bi.next())
        self.assertEquals('c', bi.next())
        self.assertEquals('d', bi.next())
        self.failUnlessRaises(StopIteration, bi.next)
        
    def test_next_previous_combo(self):
        bi = BidiIterator(['a','b','c','d'])
        self.assertEquals('a', bi.next())
        self.assertEquals('b', bi.next())
        self.assertEquals('a', bi.previous())
        self.assertEquals('b', bi.next())
        self.assertEquals('c', bi.next())
        self.assertEquals('d', bi.next())
        self.failUnlessRaises(StopIteration, bi.next)
        self.assertEquals('c', bi.previous())
        self.assertEquals('b', bi.previous())
        self.assertEquals('a', bi.previous())
        self.failUnlessRaises(StopIteration, bi.previous)
        
    def test_next_with_initial_position_specified(self):
        self.assertEquals('b', BidiIterator(['a','b','c','d'], 0).next())
        self.assertEquals('c', BidiIterator(['a','b','c','d'], 1).next())
        self.assertEquals('d', BidiIterator(['a','b','c','d'], 2).next())
        self.assertEquals(2, BidiIterator(['a','b','c','d'], 2).index())
        self.failUnlessRaises(StopIteration, BidiIterator(['a','b','c','d'], 3).next)

    def test_previous_with_initial_position_specified(self):
        self.failUnlessRaises(StopIteration, BidiIterator(['a','b','c','d'], 0).previous)
        self.assertEquals('a', BidiIterator(['a','b','c','d'], 1).previous())
        self.assertEquals('b', BidiIterator(['a','b','c','d'], 2).previous())
        self.assertEquals('c', BidiIterator(['a','b','c','d'], 3).previous())
                          
    def test_current_and_len_is_1_Then_raise_StopIteration(self):
        self.failUnlessRaises(StopIteration, BidiIterator(['a']).current)

    def test_current_after_next_and_len_is_1_Then_return_1(self):
        bi = BidiIterator(['a'])
        bi.next()
        self.assertEquals('a', bi.current())
        self.assertEquals(0, bi.index())

    def test_current_with_len_1_and_initial_pos_0_returns_1(self):
        bi = BidiIterator(['a'], 0)
        self.assertEquals('a', bi.current())
        

class CyclingBidiIteratorTest(unittest.TestCase):
    
    def test_When_list_empty_Then_raise_StopIteration(self):
        self.failUnlessRaises(StopIteration, CyclingBidiIterator([]).next)
        self.failUnlessRaises(StopIteration, CyclingBidiIterator([]).previous)
    
    def test_When_previous_and_len_is_1_Then_always_return_1(self):
        bi = CyclingBidiIterator(['a'])
        self.assertEquals('a', bi.previous())
        self.assertEquals('a', bi.previous())
        self.assertEquals('a', bi.previous())
    
    def test_When_previous_and_len_gt_1_Then_wrap_around(self):
        bi = CyclingBidiIterator(['a', 'b', 'c'])
        self.assertEquals('c', bi.previous())
        self.assertEquals('b', bi.previous())
        self.assertEquals('a', bi.previous())
        self.assertEquals('c', bi.previous())
        self.assertEquals('b', bi.previous())
        self.assertEquals('a', bi.previous())
        
    def test_When_next_and_len_is_1_Then_always_return_1(self):
        bi = CyclingBidiIterator(['a'])
        self.assertEquals('a', bi.next())
        self.assertEquals('a', bi.next())
        self.assertEquals('a', bi.next())

    def test_When_next_and_len_gt_1_Then_wrap_around(self):
        bi = CyclingBidiIterator(['a', 'b', 'c'])
        self.assertEquals('a', bi.next())
        self.assertEquals('b', bi.next())
        self.assertEquals('c', bi.next())
        self.assertEquals('a', bi.next())
        self.assertEquals('b', bi.next())
        self.assertEquals('c', bi.next())

    def test_next_previous_combo(self):
        bi = CyclingBidiIterator(['a','b','c','d'])
        self.assertEquals('a', bi.next())
        self.assertEquals('b', bi.next())
        self.assertEquals('a', bi.previous())
        self.assertEquals('b', bi.next())
        self.assertEquals('c', bi.next())
        self.assertEquals('d', bi.next())
        self.assertEquals('a', bi.next())
        self.assertEquals('d', bi.previous())
        self.assertEquals('c', bi.previous())
        self.assertEquals('b', bi.previous())
        self.assertEquals('a', bi.previous())
        self.assertEquals('d', bi.previous())

    def test_next_with_initial_position_specified(self):
        self.assertEquals('b', CyclingBidiIterator(['a','b','c','d'], 0).next())
        self.assertEquals('c', CyclingBidiIterator(['a','b','c','d'], 1).next())
        self.assertEquals('d', CyclingBidiIterator(['a','b','c','d'], 2).next())
        self.assertEquals('a', CyclingBidiIterator(['a','b','c','d'], 3).next())

    def test_previous_with_initial_position_specified(self):
        self.assertEquals('d', CyclingBidiIterator(['a','b','c','d'], 0).previous())
        self.assertEquals('a', CyclingBidiIterator(['a','b','c','d'], 1).previous())
        self.assertEquals('b', CyclingBidiIterator(['a','b','c','d'], 2).previous())
        self.assertEquals('c', CyclingBidiIterator(['a','b','c','d'], 3).previous())


class TimedCacheDecoratorTest(unittest.TestCase):
    
    @timed_cache(seconds=2)
    def foo(self):
        self.x += 1
        return self.x
    
    def test_timed_cache_works(self):
        self.x = 1
        self.assertTrue(2, self.foo())
        time.sleep(1)
        for i in xrange(100):
            self.assertTrue(2, self.foo())
        time.sleep(2)
        self.assertTrue(3, self.foo())


class MaxThreadsDecoratorTest(unittest.TestCase):
    
    @run_async
    @max_threads(3)
    def foo(self):
        self.count += 1
        self.assertTrue(self.count <= 3)
        time.sleep(0.2)
        self.assertTrue(self.count <= 3)
        self.count -= 1
    
    def test_max_threads_works(self):
        self.count = 0
        workers = []
        for i in xrange(20):
            workers.append(self.foo())
        for w in workers:
            w.join()    
