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
#    3. Neither the name of the Portable Site Information project nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
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

'''Durus object database frontend.

shove's psuedo-URL for Durus stores follows the form:

durus://<path>


Where the path is a URL path to a durus FileStorage database. Alternatively, a
native pathname to a durus database can be passed as the 'engine' parameter.
'''

from durus.connection import Connection
from durus.file_storage import FileStorage

from shove.store import SyncStore

__all__ = ['DurusStore']


class DurusStore(SyncStore):
    
    '''Class for Durus object database frontend.'''

    init = 'durus://'    

    def __init__(self, engine, **kw):
        super(DurusStore, self).__init__(engine, **kw)
        self._db = FileStorage(self._engine)
        self._connection = Connection(self._db)
        self.sync = self._connection.commit
        self._store = self._connection.get_root()

    def close(self):
        '''Closes all open storage and connections.'''
        self.sync()
        self._db.close()
        super(DurusStore, self).close()