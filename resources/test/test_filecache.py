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
import filecache
import logging
import os
import random
import shutil
import tempfile
import unittest

log = logging.getLogger('mythtv.unittest')

# =============================================================================
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
        filecache.FileCache(self.cacheRootDir, filecache.FileSystemResolver())
            
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
                filecache.FileCache(self.cacheRootDir, filecache.FileSystemResolver())
                # Verify
                self.fail('Should have failed because rootCacheDir exists as a file')
            except Exception:
                log.debug('SUCCESS: Error thrown when file already exists as root cache dir')
        finally:
            os.remove(self.cacheRootDir)
    
    def test_get_When_file_in_cache_Then_return_filepath(self):
        # Setup - create file and place in cache
        fileUrl = self.createSomeFile()
        resolver = filecache.FileSystemResolver()
        digest = resolver.hash(fileUrl)
        resolver.store(fileUrl, os.path.join(self.cacheRootDir, digest))
        cache = filecache.FileCache(self.cacheRootDir, resolver)

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
        cache = filecache.FileCache(self.cacheRootDir, filecache.FileSystemResolver())
        cache.get(fileUrl)
        self.assertTrue(cache.contains(fileUrl))
        
        try:
            # Test
            cache.clear()
            
            # Verify
            self.assertFalse(cache.contains(fileUrl))
        finally:
            os.remove(fileUrl)

    def createSomeFile(self):
        fileUrl = os.path.join(tempfile.gettempdir(), 'fileToCache_%s' % random.randint(1, 999999))
        fd = open(fileUrl, 'w')
        fd.write('sample file contents')
        fd.close()
        return fileUrl

# =============================================================================
if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
