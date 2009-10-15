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
import md5
import os
import shutil
import urllib

log = logging.getLogger('mythbox.cache')

# =============================================================================
class FileResolver(object):
    
    def store(self, fileUrl, dest):
        raise Exception, 'AbstractMethod'
    
    def hash(self, fileUrl):
        return md5.new(fileUrl).hexdigest()
    
# =============================================================================    
class FileSystemResolver(FileResolver):
    """Resolves files accessible via the local filesystem"""
    
    def store(self, fileUrl, dest):
        shutil.copyfile(fileUrl, dest)

# =============================================================================
class HttpResolver(FileResolver):
    """Resolves files accessible via a http:// url"""
    
    def store(self, fileUrl, dest):
        filename, headers = urllib.urlretrieve(fileUrl, dest)
    
# =============================================================================
class FileCache(object):
    """File cache which uses a FileResolver to populate the cache on-demand"""
    
    def __init__(self, rootDir, resolver):
        """
        @type rootDir: str
        @param rootDir: root directory of the cache. will be created if it does not exist.
        @type resolver: FileResolver
        @param resolver: Pluggable component to retrieve (resolve) files.
        """
        self.rootDir = rootDir
        self.resolver = resolver
        
        if not os.path.exists(rootDir):
            os.makedirs(rootDir)
            log.debug('Created cache root dir %s' % rootDir)
        if not os.path.isdir(rootDir):
            raise Exception, 'File cache root dir already exists as a file: %s' % rootDir

    def _mapToPath(self, fileUrl):
        return os.path.join(self.rootDir, self.resolver.hash(fileUrl))
        
    def contains(self, fileUrl):
        return os.path.exists(self._mapToPath(fileUrl))
     
    def get(self, fileUrl):
        """
        @return: local path if file resolution was successful, None otherwise
        """
        filepath = self._mapToPath(fileUrl) 
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            log.debug('Cache MISS for fileurl: %s   filepath: %s' % (fileUrl, filepath))
            self.resolver.store(fileUrl, filepath)
            
            # Don't cache zero byte files
            if os.path.getsize(filepath) == 0:
                log.warn('file %s resulted in zero byte file...removing...' % fileUrl)
                self.remove(fileUrl)
                return None
        else:
            log.debug('Cache HIT for fileurl: %s   filepath: %s' % (fileUrl, filepath))
            
        return filepath
    
    def remove(self, fileUrl):
        filepath = self._mapToPath(fileUrl)
        if os.path.exists(filepath):
            os.remove(filepath)
            
    def clear(self):
        shutil.rmtree(self.rootDir, True)
        os.makedirs(self.rootDir)