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
import time
import unittest

from mythbox.pool import PoolableFactory, Pool, EvictingPool
from mythbox.util import run_async

log = mythboxtest.getLogger('mythbox.unittest')

class Widget(object):
    
    def __init__(self, cnt):
        self.cnt = cnt
        
    def open(self):
        pass
    
    def close(self):
        pass


class WidgetFactory(PoolableFactory):
    
    def __init__(self):
        self.cnt = 1
        
    def create(self):
        widget = Widget(self.cnt)
        self.cnt+=1
        widget.open()
        return widget
    
    def destroy(self, widget):
        widget.close()
        del widget


class PoolTest(unittest.TestCase):
    
    def test_state_on_construction(self):
        p = Pool(WidgetFactory())
        self.assertEquals(0, p.size())
        self.assertEquals(0, p.available())
        
        p.shutdown()
        self.assertEquals(0, p.size())
        self.assertEquals(0, p.available())
    
    def test_checkin_checkout(self):
        p = Pool(WidgetFactory())
        w1 = p.checkout()
        log.debug(w1)
        
        self.assertEquals(1, p.size())
        self.assertEquals(0, p.available())
        
        p.checkin(w1)
        self.assertEquals(1, p.size())
        self.assertEquals(1, p.available())
        
        w2 = p.checkout()
        self.assertEquals(w1, w2)
        self.assertEquals(1, p.size())
        self.assertEquals(0, p.available())
        
    def test_checkin_after_shutdown_raises_exception(self):
        p = Pool(WidgetFactory())
        w1 = p.checkout()
        p.shutdown()
        
        try:
            p.checkin(w1)
        except Exception, e:
            pass  # Success
    
    def test_checkout_after_shutdown_raises_exception(self):
        p = Pool(WidgetFactory())
        p.shutdown()
        
        try:
            p.checkout()
        except Exception, e:
            pass  # Success

    @run_async
    def multiple_consumers_thread(self, c, p, max):
        log.debug('%sConsumer %d started' % ((' ' * c), c))
        try:
            for i in xrange(1000):
                self.assertTrue(p.size() <= max)
                r = p.checkout()
                #log.debug('Checked out widget %d' % r.cnt)
                #time.sleep(0.1)
                self.assertTrue(p.size() <= max)
                p.checkin(r)
                #log.debug('Checked in widget %d' % r.cnt)
                #time.sleep(0.1)
                self.assertTrue(p.size() <= max)
        except:
            log.exception('exercisePool')
        log.debug('%sConsumer %d done' % ((' ' * c), c))

    def test_multiple_consumers(self):
        p = Pool(WidgetFactory())
        numConsumers = 10
        consumers = []    
        for c in xrange(numConsumers):
            consumers.append(self.multiple_consumers_thread(c, p, numConsumers))
        for consumer in consumers:
            consumer.join()
        self.assertTrue(p.available() > 0)
        self.assertTrue(p.size() > 0)
        p.shutdown()
        
        
    def test_shrink_does_nothing_to_empty_pool(self):
        p = Pool(WidgetFactory())
        p.shrink()
        self.assertEquals(0, p.size())
        self.assertEquals(0, p.available())
        
    def test_shrink_does_nothing_to_pool_when_available_is_zero(self):
        p = Pool(WidgetFactory())
        p.checkout()
        p.shrink()
        self.assertEquals(1, p.size())
        self.assertEquals(0, p.available())

    def test_shrink_reclaims_unused_resources_with_no_checkouts(self):
        p = Pool(WidgetFactory())
        w1 = p.checkout()
        w2 = p.checkout()
        w3 = p.checkout()
        p.checkin(w1)
        p.checkin(w2)
        p.checkin(w3)
        p.shrink()
        self.assertEquals(0, p.size())
        self.assertEquals(0, p.available())

    def test_shrink_reclaims_unused_resources_with_existing_checkouts(self):
        p = Pool(WidgetFactory())
        w1 = p.checkout()
        w2 = p.checkout()
        w3 = p.checkout()
        p.checkin(w1)
        p.checkin(w2)
        p.shrink()
        self.assertEquals(1, p.size())
        self.assertEquals(0, p.available())

    def test_grow_does_nothing_when_requested_size_less_than_or_equal_to_current_size(self):
        p = Pool(WidgetFactory())
        for i in range(10):
            p.checkout()
        p.grow(5)
        self.assertEquals(10, p.size())
        self.assertEquals(0, p.available())
        
        p.grow(10)
        self.assertEquals(10, p.size())
        self.assertEquals(0, p.available())

    def test_grow_expands_resource_pool_when_requested_size_greater_than_current_size(self):
        p = Pool(WidgetFactory())
        p.grow(3)
        self.assertEquals(3, p.size())
        self.assertEquals(3, p.available())
        
        for i in range(5):
            p.checkout()
        p.grow(10)
        self.assertEquals(10, p.size())
        self.assertEquals(10-5, p.available())
        
    def test_grow_shrink_combos(self):
        p = Pool(WidgetFactory())
        p.grow(5)
        p.shrink()
        p.grow(20)
        p.checkout()
        p.shrink()
        p.checkout()
        p.grow(3)
        self.assertEquals(3, p.size())
        self.assertEquals(1, p.available())
        

class EvictingPoolTest(unittest.TestCase):
    
    def test_When_instantiated_and_no_interactions_Then_evictor_exits_gracefully(self):
        p = EvictingPool(WidgetFactory(), maxAgeSecs=60, reapEverySecs=2)
        time.sleep(1)
        self.assertTrue(p.evictorThread.isAlive())
        p.shutdown()
        time.sleep(2)
        self.assertFalse(p.evictorThread.isAlive())

    def test_When_lt_maxAge_Then_resource_not_evicted(self):
        p = EvictingPool(WidgetFactory(), maxAgeSecs=5, reapEverySecs=1)
        p.grow(1)
        time.sleep(3)
        self.assertEquals(1, p.available())
        p.shutdown()

    def test_When_gt_maxAge_Then_resource_evicted(self):
        p = EvictingPool(WidgetFactory(), maxAgeSecs=3, reapEverySecs=1)
        p.grow(1)
        self.assertEquals(1, p.available())
        time.sleep(4)  # induce eviction
        self.assertEquals(0, p.available())
        p.shutdown()
        
    def test_When_many_lt_maxAge_Then_none_evicted(self):
        try:
            p = EvictingPool(WidgetFactory(), maxAgeSecs=10, reapEverySecs=1)
            r1 = p.checkout()
            r2 = p.checkout()
            p.checkin(r1)
            time.sleep(1)
            p.checkin(r2)  
            self.assertEquals(2, p.available())
        finally:
            p.shutdown()

    def test_When_many_gt_maxAge_Then_all_evicted(self):
        try:
            max = 5
            p = EvictingPool(WidgetFactory(), maxAgeSecs=max, reapEverySecs=1)
            r1 = p.checkout()
            r2 = p.checkout()
            p.checkin(r1)
            time.sleep(1)
            p.checkin(r2)  
            self.assertEquals(2, p.available())
            time.sleep(max+1)  # induce eviction
            self.assertEquals(0, p.available())
        finally:
            p.shutdown()

    def test_When_one_lt_and_one_gt_maxAge_Then_evict_only_gt(self):
        try:
            max = 5
            p = EvictingPool(WidgetFactory(), maxAgeSecs=max, reapEverySecs=1)
            r1 = p.checkout()
            r2 = p.checkout()
            p.checkin(r1)
            time.sleep(max + 1)  # induce eviction  of r1
            p.checkin(r2)        # induce retention of r2
            self.assertEquals(1, p.available())
            time.sleep(max+1)    # induce eviction  of r2
            self.assertEquals(0, p.available())
        finally:
            p.shutdown()

    def test_When_stressed_Then_dont_blow_up(self):
        try:
            reap = 1
            max = 4
            num = 100
            rs = []
            p = EvictingPool(WidgetFactory(), maxAgeSecs=max, reapEverySecs=reap)

            for i in xrange(num):
                rs.append(p.checkout())
            for r in rs:
                p.checkin(r)
            
            cnt = 0
            while p.available() > 0:
                time.sleep(1)
                cnt += 1
                # TODO: Likes to fail on mac
                if cnt > 20:
                    self.fail('Failed: expected available to go down to zero. Available = %d' % p.available())
            self.assertEquals(0, p.size())
        finally:
            p.shutdown()
