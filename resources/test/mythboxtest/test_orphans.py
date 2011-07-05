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
import logging
import os
import tempfile
import unittest2 as unittest

from mockito import Mock
from mythbox.bus import EventBus
from mythbox.mythtv.enums import Upcoming
from mythbox.mythtv.conn import Connection, EventConnection, createChainId, ServerException, encodeLongLong, decodeLongLong
from mythbox.mythtv.db import MythDatabase 
from mythbox.mythtv.protocol import ProtocolException
from mythbox.platform import getPlatform
from mythbox.settings import MythSettings
from mythbox.util import OnDemandConfig

log = logging.getLogger('mythbox.unittest')


class DeleteOrphansTest(unittest.TestCase):

    def setUp(self):
        self.platform = getPlatform()
        self.translator = Mock()
        self.domainCache = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        self.settings.put('streaming_enabled', 'False')
        
        privateConfig = OnDemandConfig()
        self.settings.put('mysql_host', privateConfig.get('mysql_host'))
        self.settings.put('mysql_port', privateConfig.get('mysql_port'))
        self.settings.setMySqlDatabase(privateConfig.get('mysql_database'))
        self.settings.setMySqlUser(privateConfig.get('mysql_user'))  
        self.settings.put('mysql_password', privateConfig.get('mysql_password'))
        self.settings.put('paths_recordedprefix', privateConfig.get('paths_recordedprefix'))
        
        self.db = MythDatabase(self.settings, self.translator, self.domainCache)
        self.bus = EventBus()
        self.conn = Connection(self.settings, self.translator, self.platform, self.bus, self.db)

    def tearDown(self):
        self.conn.close()

    def test_getAllRecordings(self):
        recordings = self.conn.getAllRecordings()
        log.debug('Num Recordings = %s' % len(recordings))
        for i,r in enumerate(recordings):
            print i,r.getBareFilename()
 
        dirs = ['/usr2/mythtv','/usr2/mythtv2', '/usr2/mythtv3']
        
        mpgs = []
        
        for d in dirs:
            files = os.listdir(d)
            for f in files:
                if f.endswith('.mpg'):
                    mpgs.append(f)
                    print f
                    
        print 'Recs  total = ', len(recordings)
        print 'Files total = ', len(mpgs)
        print 'Extras      = ', len(mpgs) - len(recordings)    
        
        todelete = mpgs[:]
        for r in recordings:
            if r.getBareFilename() in mpgs:
                todelete.remove(r.getBareFilename())
                
        print 'Todelete    = ', len(todelete)

        bucket = []
        
        import datetime
        
        for f in todelete:
            for d in dirs:
                path = os.path.join(d,f)
                if os.path.exists(path):
                    bucket.append(path)
                    print path, os.path.getsize(path)
                        
        print 'Bucket     = ', len(bucket)
        sorted(bucket)
        
        total = 0
        for f in bucket:
            s = os.path.getsize(f)
            total += s
            
        print total/1000000000
        
        import shutil
        
        for src in bucket[:25]:
            dest = '/usr2/mythtv/backup/' + os.path.basename(src)
            print src,' -> ', dest
            #shutil.move(src, dest) 

            
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
