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
import time
import unittest2 as unittest
import util_mock

from mockito import Mock
from mythbox import pool
from mythbox.mythtv.db import inject_db, MythDatabaseFactory
from mythbox.platform import Platform
from mythbox.settings import MythSettings
from mythbox.util import run_async, OnDemandConfig

log = mythboxtest.getLogger('mythbox.unittest')


class SafeDbClient(object):
    
    def __init__(self):
        pass
    
    @inject_db
    def getTuners(self):
        #log.debug('----> getting tuners')
        tuners = self.db().getTuners()
        log.debug('tuners = %d' % len(tuners))
        
    @inject_db
    def getJobs(self):
        jobs = self.db().getJobs()
        log.debug('jobs = %d' % len(jobs))

    @inject_db
    def outerNestedAccessToDb(self):
        self.db().getJobs()
        self.middleNestedAccessToDb()
        
    @inject_db
    def middleNestedAccessToDb(self):
        self.db().getTuners()
        self.innerNestedAccessToDb()
        
    @inject_db
    def innerNestedAccessToDb(self):
        self.db().getJobs()


class OtherDbClient(object):
    
    @inject_db
    def getRecordingGroups(self):
        #log.debug('----> getting tuners')
        groups = self.db().getRecordingGroups()
        log.debug('groups = %d' % len(groups))


class ThreadLocalTest(unittest.TestCase):
    
    def setUp(self):
        p = Platform()
        langInfo = util_mock.XBMCLangInfo(p)
        translator = util_mock.Translator(p, langInfo)
        settings = MythSettings(p, translator)
        domainCache = Mock()
        
        privateConfig = OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        settings.put('mysql_user', privateConfig.get('mysql_user'))  
        settings.put('mysql_password', privateConfig.get('mysql_password'))
        
        self.dbPool = pool.pools['dbPool'] = pool.Pool(MythDatabaseFactory(settings=settings, translator=translator, domainCache=domainCache))
    
    def tearDown(self):
        self.dbPool.shutdown()
        self.dbPool = None
        del pool.pools['dbPool']

    @run_async
    def getTunersAsync(self, client):
        client.getTuners()

    def test_3(self):
        client = SafeDbClient()
        workers = []
        for i in range(20):
            workers.append(self.getTunersAsync(client))
            time.sleep(0.1)
            
        for w in workers:
            w.join()
            
        log.debug('dbPool size = %d' % self.dbPool.size())
        log.debug('dbPool avail = %d' % self.dbPool.available())
        
        self.dbPool.shrink()

        log.debug('dbPool size = %d' % self.dbPool.size())
        log.debug('dbPool avail = %d' % self.dbPool.available())
        
    def test_multiple_calls_to_tls_resource_in_same_thread_allocates_only_one_resource(self):
        client = SafeDbClient()
        client.getTuners()
        client.getJobs()
        self.assertEquals(1, self.dbPool.available())
        self.assertEquals(1, self.dbPool.size())
        self.dbPool.shrink()
        
    def test_nesting_method_calls_to_tls_resources_in_same_thread_allocates_only_one_resources(self):
        client = SafeDbClient()
        client.outerNestedAccessToDb() # impl calls other methods which are also decorated with @inject_db
        self.assertEquals(1, self.dbPool.available())
        self.assertEquals(1, self.dbPool.size())
        self.dbPool.shrink()

    def test_resource_is_shared_by_methods_in_objects_of_differing_class_but_in_the_same_thread(self):
        client1 = SafeDbClient()
        client2 = OtherDbClient()
        
        client1.getJobs()
        client2.getRecordingGroups()
        
        self.assertEquals(1, self.dbPool.available())
        self.assertEquals(1, self.dbPool.size())
        self.dbPool.shrink()
