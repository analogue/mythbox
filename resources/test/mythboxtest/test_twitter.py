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
import unittest2 as unittest
import twitter
import mythboxtest

log = mythboxtest.getLogger('mythbox.unittest')

class TwitterTest(unittest.TestCase):
    
    def test_mythbox_timeline(self):
        api = twitter.Api()
        log.debug(api)
        messages = api.GetUserTimeline(user='cnnbrk', count=10)        
        for m in messages:
            log.debug(m.text[:50])
