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

'''Database object cache.


The shove psuedo-URL used for database object caches is the format used by
SQLAlchemy:

<driver>://<username>:<password>@<host>:<port>/<database>

<driver> is the database engine. The engines currently supported SQLAlchemy are
sqlite, mysql, postgres, oracle, mssql, and firebird.
<username> is the database account user name
<password> is the database accound password
<host> is the database location
<port> is the database port
<database> is the name of the specific database

For more information on specific databases see:

http://www.sqlalchemy.org/docs/dbengine.myt#dbengine_supported
'''

import time
import random
from datetime import datetime

from sqlalchemy import (
    MetaData, Table, Column, String, Binary, DateTime, bindparam, select, 
    update, insert, delete,
)

from shove import DbBase 

__all__ = ['DbCache']


class DbCache(DbBase):

    '''Database cache backend.'''

    def __init__(self, engine, **kw):
        super(DbCache, self).__init__(engine, **kw)
        # Get table name
        tablename = kw.get('tablename', 'cache')
        # Bind metadata
        self._metadata = MetaData(engine)
        # Make cache table
        self._store = Table(tablename, self._metadata,
            Column('key', String(60), primary_key=True, nullable=False),
            Column('value', Binary, nullable=False),
            Column('expires', DateTime, nullable=False))
        # Create cache table if it does not exist
        if not self._store.exists(): self._store.create()
        # Set maximum entries
        self._max_entries = kw.get('max_entries', 300)
        # Maximum number of entries to cull per call if cache is full
        self._maxcull = kw.get('maxcull', 10)
        # Set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        row = select(
             [self._store.c.value, self._store.c.expires],
            self._store.c.key==key
        ).execute().fetchone()
        if row is not None:
            # Remove if item expired
            if row.expires < datetime.now().replace(microsecond=0):
                del self[key]
                raise KeyError('%s' % key)
            return self.loads(str(row.value))
        raise KeyError('%s' % key)

    def __setitem__(self, key, value):
        timeout, value, cache = self.timeout, self.dumps(value), self._store
        # Cull if too many items
        if len(self) >= self._max_entries: self._cull()
        # Generate expiration time
        expires = datetime.fromtimestamp(
            time.time() + timeout
        ).replace(microsecond=0)
        # Update database if key already present
        if key in self:
            update(
                cache,
                cache.c.key==key,
                dict(value=value, expires=expires)
            ).execute()
        # Insert new key if key not present
        else:
            insert(cache, dict(key=key, value=value, expires=expires)).execute()

    def _cull(self):
        '''Remove items in cache to make more room.'''
        cache, maxcull = self._store, self._maxcull
        # Remove items that have timed out
        now = datetime.now().replace(microsecond=0)
        delete(cache, cache.c.expires < now).execute()
        # Remove any items over the maximum allowed number in the cache
        if len(self) >= self._max_entries:
            # Upper limit for key query
            ul = maxcull * 2
            # Get list of keys
            keys = [
                i[0] for i in select(
                    [cache.c.key], limit=ul
                ).execute().fetchall()
            ]
            # Get some keys at random
            delkeys = list(random.choice(keys) for i in xrange(maxcull))
            # Delete keys
            fkeys = tuple({'key':k} for k in delkeys)
            delete(cache, cache.c.key.in_(bindparam('key'))).execute(*fkeys)