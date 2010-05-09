#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
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
import unittest

from mockito import Mock, when, any
from mythbox.feeds import TwitterFeed, FeedHose

log = logging.getLogger('mythbox.unittest')

# =============================================================================
class FeedHostTest(unittest.TestCase):
    
    def test_getLatestEntries_None(self):
        
        # Setup
        settings = Mock()
        when(settings).get(any()).thenReturn('blah')
        feedHose = FeedHose(settings=settings, bus=Mock())
        
        # Test
        entries = feedHose.getLatestEntries()
        
        # Verify
        self.assertTrue(len(entries) == 0)    
        
    def test_getLatestEntries_Sorted_from_newest_to_oldest(self):
        pass

# =============================================================================
class TwitterFeedTest(unittest.TestCase):

    def test_getEntries(self):
        feed = TwitterFeed('mythboxfeed')
        s = feed.getEntries()
        log.debug('feed text = %s' % s)
        self.assertTrue(s)
    
# =============================================================================
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
    