import unittest
import time
import os
from shove.cache.file import FileCache


class TestFileCache(unittest.TestCase):

    initstring = 'file://test'
    cacheclass = FileCache

    def setUp(self): 
        self.cache = self.cacheclass(self.initstring)

    def tearDown(self): 
        self.cache = None
        for x in os.listdir('test'): os.remove(os.path.join('test', x))
        os.rmdir('test')
    
    def test_getitem(self):
        self.cache['test'] = 'test'
        self.assertEqual(self.cache['test'], 'test')

    def test_setitem(self):
        self.cache['test'] = 'test'
        self.assertEqual(self.cache['test'], 'test')

    def test_delitem(self):
        self.cache['test'] = 'test'
        del self.cache['test']
        self.assertEqual('test' in self.cache, False)

    def test_get(self):
        self.assertEqual(self.cache.get('min'), None)        

    def test_timeout(self):      
        cache = self.cacheclass(self.initstring, timeout=1)
        cache['test'] = 'test'
        time.sleep(2)
        def tmp(): cache['test']            
        self.assertRaises(KeyError, tmp)

    def test_cull(self):      
        cache = self.cacheclass(self.initstring, max_entries=1)
        cache['test'] = 'test'
        cache['test2'] = 'test'
        num = len(cache)
        self.assertEquals(num, 1)        
        

if __name__ == '__main__':
    unittest.main()        