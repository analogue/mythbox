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

'''Database object store.

The shove psuedo-URL used for database object stores is the format used by
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

from sqlalchemy import MetaData, Table, Column, String, Binary, select

from shove import BaseStore, DbBase

__all__ = ['DbStore']


class DbStore(BaseStore, DbBase):

    '''Database cache backend.'''

    def __init__(self, engine, **kw):
        super(DbStore, self).__init__(engine, **kw)
        # Get tablename
        tablename = kw.get('tablename', 'store')
        # Bind metadata
        self._metadata = MetaData(engine)
        # Make store table
        self._store = Table(tablename, self._metadata,
            Column('key', String(256), primary_key=True, nullable=False),
            Column('value', Binary, nullable=False))
        # Create store table if it does not exist
        if not self._store.exists(): self._store.create()

    def __getitem__(self, key):
        row = select(
            [self._store.c.value],
            self._store.c.key==key
        ).execute().fetchone()
        if row is not None: return self.loads(str(row.value))
        raise KeyError('Key "%s" not found.' % key)

    def __setitem__(self, k, v):
        v, store = self.dumps(v), self._store
        # Update database if key already present
        if k in self:
            store.update(store.c.key==k).execute(value=v)
        # Insert new key if key not present
        else:
            store.insert().execute(key=k, value=v)

    def keys(self):
        '''Returns a list of keys in the store.'''
        return list(i[0] for i in select(
            [self._store.c.key]
        ).execute().fetchall())