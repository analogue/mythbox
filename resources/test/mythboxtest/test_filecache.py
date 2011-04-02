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
import os
import random
import shutil
import string
import tempfile
import time
import unittest2 as unittest

from mythbox.filecache import FileResolver, FileSystemResolver, FileCache
from mythbox.util import run_async

log = mythboxtest.getLogger('mythbox.unittest')

class FileResolverTest(unittest.TestCase):
    
    def randomString(self):
        return ''.join(random.Random().sample(string.letters+string.digits, 20))
    
    def test_hash_performance(self):
        r = FileResolver()
        samples = []
        for i in xrange(1000):
            samples.append(self.randomString())
        
        for s in samples:
            r.hash(s)
        
        
class DelayedFileResolver(FileSystemResolver):

    def __init__(self):
        self.timesCalled = 0
        
    def store(self, fileUrl, dest):
        self.timesCalled += 1
        # add delay so other threads pile up while we're busy...
        time.sleep(1)
        return super(DelayedFileResolver, self).store(fileUrl, dest)


class FileCacheTest(unittest.TestCase):
    
    def setUp(self):
        self.cacheRootDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.cacheRootDir, ignore_errors=True)
        
    def test_init_When_rootDir_does_not_exist_Then_rootDir_is_created(self):
        # Setup
        shutil.rmtree(self.cacheRootDir)
        self.assertFalse(os.path.exists(self.cacheRootDir))
        
        # Test
        FileCache(self.cacheRootDir, FileSystemResolver())
            
        # Verify
        self.assertTrue(os.path.exists(self.cacheRootDir))
        self.assertTrue(os.path.isdir(self.cacheRootDir))
        
    def test_init_When_rootDir_exists_as_file_Then_raise_error(self):
        # Setup
        shutil.rmtree(self.cacheRootDir)
        dummyFile = open(self.cacheRootDir, "w")
        dummyFile.write('i am a file blocking the creation of the root cache dir')
        dummyFile.close()
        self.assertTrue(os.path.isfile(self.cacheRootDir))
        
        try:
            try:
                # Test
                FileCache(self.cacheRootDir, FileSystemResolver())
                # Verify
                self.fail('Should have failed because rootCacheDir exists as a file')
            except Exception:
                log.debug('SUCCESS: Error thrown when file already exists as root cache dir')
        finally:
            os.remove(self.cacheRootDir)
    
    def test_get_When_file_in_cache_Then_return_filepath(self):
        # Setup - create file and place in cache
        fileUrl = self.createSomeFile()
        resolver = FileSystemResolver()
        digest = resolver.hash(fileUrl)
        resolver.store(fileUrl, os.path.join(self.cacheRootDir, digest))
        cache = FileCache(self.cacheRootDir, resolver)

        try:
            # Test
            filePath = cache.get(fileUrl)
            
            # Verify - request for cached file should not pass through to resolver
            self.assertEquals(os.path.join(self.cacheRootDir, digest), filePath)
        finally:
            os.remove(fileUrl)
    
    def test_get_When_file_not_in_cache_Then_retrieve_and_return_filepath(self):
        pass


    def test_clear_When_cache_cleared_Then_file_no_longer_in_cache(self):
        # Setup - create file and place in cache
        fileUrl = self.createSomeFile()
        cache = FileCache(self.cacheRootDir, FileSystemResolver())
        cache.get(fileUrl)
        self.assertTrue(cache.contains(fileUrl))
        
        try:
            # Test
            cache.clear()
            
            # Verify
            self.assertFalse(cache.contains(fileUrl))
        finally:
            os.remove(fileUrl)

    def test_get_When_multiple_threads_want_the_same_resource_Then_first_thread_stores_resource_and_the_remaining_threads_block_and_return_cached_resource(self):
        fileToCache = self.createSomeFile()
        resolver = DelayedFileResolver()
        cache = FileCache(self.cacheRootDir, resolver)
        numThreads = 50
        results = [None] * numThreads
        threads = [None] * numThreads
        
        @run_async
        def getFromCache(url, slot):
            results[slot] = cache.get(url)

        for i in range(numThreads):
            results[i] = None
            threads[i] = getFromCache(fileToCache, i)

        for t in threads:
            t.join()
         
        for r in results:
            self.assertFalse(r is None)
            
        self.assertEquals(1, resolver.timesCalled)

    def createSomeFile(self):
        fileUrl = os.path.join(tempfile.gettempdir(), 'fileToCache_%s' % random.randint(1, 999999))
        fd = open(fileUrl, 'w')
        fd.write('sample file contents')
        fd.close()
        return fileUrl
