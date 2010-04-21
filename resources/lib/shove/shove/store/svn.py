# Copyright (c) 2005, the Lawrence Journal-World
# Copyright (c) 2006 L. C. Rees
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Django nor the names of its contributors may be used
#       to endorse or promote products derived from this software without
#       specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''subversion managed store.

The shove psuedo-URL used for a subversion store that is password protected is:
    
svn:<username><password>:<path>?url=<url>

or for non-password protected repositories:

svn://<path>?url=<url>

<path> is the local repository copy
<url> is the URL of the subversion repository
'''

import os
import urllib
import threading

try:
    import pysvn
except ImportError:
    raise ImportError('Requires Python Subversion library')

from shove import BaseStore, synchronized

__all__ = ['SvnStore']


class SvnStore(BaseStore):

    '''Class for subversion store.'''
    
    def __init__(self, engine=None, **kw):
        super(SvnStore, self).__init__(engine, **kw)
        # Get path, url from keywords if used
        path, url = kw.get('path'), kw.get('url')
        # Get username. password from keywords if used
        user, password = kw.get('user'), kw.get('password')
        # Process psuedo URL if used
        if engine is not None:
            path, query = engine.split('n://')[1].split('?')
            url = query.split('=')[1]
            # Check for username, password
            if '@' in path:
                auth, path = path.split('@')
                user, password = auth.split(':')
            path = urllib.url2pathname(path)
        # Create subversion client
        self._client = pysvn.Client()
        # Assign username, password
        if user is not None: self._client.set_username(user)
        if password is not None: self._client.set_password(password)
        # Verify that store exists in repository
        try:
            self._client.info2(url)
        # Create store in repository if it doesn't exist
        except pysvn.ClientError:
            self._client.mkdir(url, 'Adding directory')
        # Verify that local copy exists
        try:			
            if self._client.info(path) is None: 
                self._client.checkout(url, path)            
        # Check it out if it doesn't exist
        except pysvn.ClientError:
            self._client.checkout(url, path)
        self._path, self._url = path, url
        # Lock
        self._lock = threading.Condition()

    @synchronized
    def __getitem__(self, key):
        try:
            return self.loads(self._client.cat(self._key_to_file(key)))
        except:
            raise KeyError('%s' % key)

    @synchronized
    def __setitem__(self, key, value):
        fname = self._key_to_file(key)
        # Write value to file
        open(fname, 'wb').write(self.dumps(value))
        # Add to repository
        if key not in self: self._client.add(fname)
        self._client.checkin([fname], 'Adding %s' % fname)
        
    @synchronized
    def __delitem__(self, key):
        try:
            fname = self._key_to_file(key)
            self._client.remove(fname)
            # Remove deleted value from repository
            self._client.checkin([fname], 'Removing %s' % fname)
        except:
            raise KeyError('%s' % key)    
    
    def _key_to_file(self, key):
        '''Gives the filesystem path for a key.'''
        return os.path.join(self._path, urllib.quote_plus(key))

    @synchronized
    def keys(self):
        '''Returns a list of keys in the subversion repository.'''
        return list(str(i.name.split('/')[-1]) for i
            in self._client.ls(self._path))