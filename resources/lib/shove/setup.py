# Copyright (c) 2006-2008 L. C. Rees.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1.  Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2.  Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 3.  Neither the name of the Portable Site Information Project nor the names
# of its contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

'''setup - setuptools based setup for shove.'''

import ez_setup
ez_setup.use_setuptools()

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='shove',
    version='0.2.1',
    description='''Common object storage frontend.''',
    long_description='''Common object storage frontend that supports dictionary-style access, object serialization and compression, and multiple storage and caching backends.

Currently supported storage backends are:

    * Amazon S3 Web Service
    * Berkeley Source Database
    * Filesystem
    * Firebird
    * FTP
    * DBM
    * Durus
    * Memory
    * Microsoft SQL Server
    * MySQL
    * Oracle
    * PostgreSQL
    * SQLite
    * Subversion
    * Zope Object Database (ZODB)

Currently supported caching backends are:

    * Filesystem
    * Firebird
    * memcached
    * Memory
    * Microsoft SQL Server
    * MySQL
    * Oracle
    * PostgreSQL
    * SQLite

The simplest shove use case is:

from shove import Shove

store = Shove()

which creates an in-memory store and cache.

To use another backend for storage or caching, a configuration URI or an existing store or cache instance is passed to shove using the form:

from shove import Shove

<storename> = Shove(<store_uri>, <cache_uri>)

The URI format for a backend is documented in its module. The URI form is the same as SQLAlchemy's:

http://www.sqlalchemy.org/docs/04/dbengine.html#dbengine_establishing

shove implements the Python dictionary/mapping API:

http://docs.python.org/lib/typesmapping.html''',
    author='L. C. Rees',
    author_email='lcrees@gmail.com',
    url='http://pypi.python.org/pypi/shove/',
    license='BSD',
    packages = ['shove', 'shove.cache', 'shove.store', 'shove.tests'],
    py_modules=['ez_setup'],
    data_files=['README'],
    test_suite='shove.tests',
    zip_safe = False,
    keywords='object storage persistence database shelve',
    classifiers=['Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Database :: Front-Ends'],
    install_requires = ['SQLAlchemy==0.4', 'boto'],
    entry_points = '''
    [shove.stores]
    bsddb=shove.store.bsdb:BsdStore
    dbm=shove.store.dbm:DbmStore
    durus=shove.store.durusdb:DurusStore
    file=shove.store.file:FileStore
    firebird=shove.store.db:DbStore
    ftp=shove.store.ftp:FtpStore
    memory=shove.store.memory:MemoryStore
    mssql=shove.store.db:DbStore
    mysql=shove.store.db:DbStore
    oracle=shove.store.db:DbStore
    postgres=shove.store.db:DbStore
    simple=shove.store.simple:SimpleStore
    sqlite=shove.store.db:DbStore
    s3=shove.store.s3:S3Store
    svn=shove.store.svn:SvnStore
    zodb=shove.store.zodb:ZodbStore
    [shove.caches]
    bsddb=shove.cache.bsdb:BsdCache
    file=shove.cache.file:FileCache
    filelru=shove.cache.filelru:FileLRUCache
    firebird=shove.cache.db:DbCache
    memcache=shove.cache.memcached:MemCached
    memlru=shove.cache.memlru:MemoryLRUCache
    memory=shove.cache.memory:MemoryCache
    mssql=shove.cache.db:DbCache
    mysql=shove.cache.db:DbCache
    oracle=shove.cache.db:DbCache
    postgres=shove.cache.db:DbCache
    simple=shove.cache.simple:SimpleCache
    simplelru=shove.cache.simplelru:SimpleLRUCache
    sqlite=shove.cache.db:DbCache
    '''
)