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

'''File-based cache

shove's psuedo-URL for file caches follows the form:

file://<path>

Where the path is a URL path to a directory on a local filesystem.
Alternatively, a native pathname to the directory can be passed as the 'engine'
argument.
'''

import time

from shove import FileBase
from shove.cache.simple import SimpleCache

__all__ = ['FileCache']


class FileCache(FileBase, SimpleCache):

    '''File-based cache backend'''    
    
    def __init__(self, engine, **kw):
        super(FileCache, self).__init__(engine, **kw)

    def __getitem__(self, key):
        try:
            exp, value = super(FileCache, self).__getitem__(key)
            # Remove item if time has expired.
            if exp < time.time():
                del self[key]
                raise KeyError('%s' % key)  
            return value
        except:
            raise KeyError('%s' % key)                

    def __setitem__(self, key, value):
        if len(self) >= self._max_entries: self._cull()
        super(FileCache, self).__setitem__(
            key, 
            (time.time() + self.timeout, value)
        )