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

'''"memcache" cache.

The shove psuedo-URL for a memcache cache is:
    
memcache://<memcache_server>
'''

try:
    import memcache
except ImportError:
    raise ImportError("Memcache cache requires the 'memcache' library")

from shove import Base

__all__ = ['MemCached']


class MemCached(Base):

    '''Memcached cache backend'''    
    
    def __init__(self, engine, **kw):
        super(MemCached, self).__init__(engine, **kw)
        if engine.startswith('memcache://'): engine = engine.split('://')[1]
        self._store = memcache.Client(engine.split(';'))
        # Set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        value = self._store.get(key)
        if value is None: raise KeyError('%s' % key)
        return self.loads(value)
        
    def __setitem__(self, key, value):
        self._store.set(key, self.dumps(value), self.timeout)

    def __delitem__(self, key):
        self._store.delete(key)