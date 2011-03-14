import unittest2 as unittest
from mythbox.util import run_async
import time
import random
import threading

class Foo(object):
    lock = threading.RLock()
    gold = None
    cnt = 0
    
    @classmethod
    def doWorkSerially(cls, i):
        Foo.lock.acquire()
        Foo.cnt +=1
        print('doWorkSerially %s %s' % (i, Foo.cnt))
        time.sleep(random.randint(1,5))
        Foo.cnt -=1
        Foo.lock.release()
        
    def doWork(self, i):
        print('doWork %s' % i)
        Foo.doWorkSerially(i)
        
    @run_async
    def doWorkAsync(self, i):
        print('doWorkAsync %s' % i)
        self.doWork(i)
        
        
class StaticTest(unittest.TestCase):
    
    def test_sometihng(self):
        f = Foo()
        f.doWork(1)

    def test_multiple_threads(self):
        foos = [Foo() for i in xrange(10)]
        threads = [f.doWorkAsync(i) for i,f in enumerate(foos)]
        [t.join() for t in threads]
        