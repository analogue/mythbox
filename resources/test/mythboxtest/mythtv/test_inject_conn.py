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
from mythbox.mythtv.db import MythDatabaseFactory
from mythbox.platform import Platform
from mythbox.settings import MythSettings
from mythbox.util import run_async, OnDemandConfig
from mythbox.mythtv.conn import ConnectionFactory, inject_conn

log = mythboxtest.getLogger('mythbox.unittest')


class SafeClient(object):
    
    def __init__(self):
        pass
    
    @inject_conn
    def getTuners(self):
        self.conn().getLoad()
        
    @inject_conn
    def getJobs(self):
        self.conn().getUptime()

    @inject_conn
    def outerNestedAccessToDb(self):
        self.conn().getUptime()
        self.middleNestedAccessToDb()
        
    @inject_conn
    def middleNestedAccessToDb(self):
        self.conn().getTuners()
        self.innerNestedAccessToDb()
        
    @inject_conn
    def innerNestedAccessToDb(self):
        self.conn().getLoad()
    
    @inject_conn
    def delayed(self, delay):
        time.sleep(delay)
        self.conn().getLoad()
        
class OtherClient(object):
    
    @inject_conn
    def getRecordingGroups(self):
        log.debug('uptime = %s' % self.conn().getUptime())


class InjectConnDecoratorTest(unittest.TestCase):
    
    def setUp(self):
        p = Platform()
        bus = Mock()
        translator = util_mock.Translator(p, langInfo=util_mock.XBMCLangInfo(p))
        settings = MythSettings(p, translator)
        domainCache = Mock()
        
        privateConfig = OnDemandConfig()
        settings.put('mysql_host', privateConfig.get('mysql_host'))
        settings.put('mysql_database', privateConfig.get('mysql_database'))
        settings.put('mysql_user', privateConfig.get('mysql_user'))  
        settings.put('mysql_password', privateConfig.get('mysql_password'))
        
        self.dbPool = pool.pools['dbPool'] = pool.Pool(MythDatabaseFactory(settings=settings, translator=translator, domainCache=domainCache))
        self.connPool = pool.pools['connPool'] = pool.Pool(ConnectionFactory(settings=settings, translator=translator, platform=p, bus=bus))
        
    def tearDown(self):
        self.connPool.shutdown()
        self.connPool = None
        del pool.pools['connPool']

        self.dbPool.shutdown()
        self.dbPool = None
        del pool.pools['dbPool']
        
    @run_async
    def getTunersAsync(self, client):
        client.delayed(1) # make sure theres overlap with delay
        
    def test_pound_with_20_threads(self):
        client = SafeClient()
        workers = []
        for i in xrange(20):
            workers.append(self.getTunersAsync(client))
            time.sleep(0.1)
            
        for w in workers:
            w.join()

        self.assertTrue(self.connPool.size() > 0)
        self.assertTrue(self.connPool.available() > 0)
        log.debug('connPool size = %d' % self.connPool.size())
        log.debug('connPool avail = %d' % self.connPool.available())
        
        self.connPool.shrink()
        self.assertEqual(0, self.connPool.size())
        self.assertEqual(0, self.connPool.available())
        log.debug('connPool size = %d' % self.connPool.size())
        log.debug('connPool avail = %d' % self.connPool.available())
        
    def test_multiple_calls_to_tls_resource_in_same_thread_allocates_only_one_resource(self):
        client = SafeClient()
        client.getTuners()
        client.getJobs()
        self.assertEquals(1, self.connPool.available())
        self.assertEquals(1, self.connPool.size())
        self.connPool.shrink()
        
    def test_nesting_method_calls_to_tls_resources_in_same_thread_allocates_only_one_resources(self):
        client = SafeClient()
        client.outerNestedAccessToDb() # impl calls other methods which are also decorated with @inject_conn
        self.assertEquals(1, self.connPool.available())
        self.assertEquals(1, self.connPool.size())
        self.connPool.shrink()

    def test_resource_is_shared_by_methods_in_objects_of_differing_class_but_in_the_same_thread(self):
        client1 = SafeClient()
        client2 = OtherClient()
        
        client1.getJobs()
        client2.getRecordingGroups()
        
        self.assertEquals(1, self.connPool.available())
        self.assertEquals(1, self.connPool.size())
        self.connPool.shrink()
