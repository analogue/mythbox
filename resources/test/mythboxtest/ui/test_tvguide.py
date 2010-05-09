#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2010 analogue@yahoo.com
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

from mythbox.ui.tvguide import Pager

log = logging.getLogger('mythbox.unittest')

# =============================================================================
class PagerTest(unittest.TestCase):
    
    def test_pageDown_numChannels_lt_channelsPerPage(self):
        p = Pager(numChannels=5, channelsPerPage=8)
        for i in xrange(0, 5):
            self.assertEquals(0, p.pageDown(i))
        
    def test_pageDown_numChannels_gt_channelsPerPage(self):
        p = Pager(numChannels=18, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(8, p.pageDown(i))
        for i in xrange(8, 16):
            self.assertEquals(16, p.pageDown(i))
        for i in xrange(16,19):
            self.assertEquals(0, p.pageDown(i))
    
    def test_pageDown_numChannels_divisible_channelsPerPage(self):
        p = Pager(numChannels=24, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(8, p.pageDown(i))
        for i in xrange(8, 16):
            self.assertEquals(16, p.pageDown(i), 'i=%d'%i)
        for i in xrange(16, 24):
            self.assertEquals(0, p.pageDown(i), 'i=%d'%i)

        p = Pager(numChannels=16, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(8, p.pageDown(i))
        for i in xrange(8, 16):
            self.assertEquals(0, p.pageDown(i), 'i=%d'%i)

        p = Pager(numChannels=8, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(0, p.pageDown(i))
        
    def test_pageUp_numChannels_lt_channelsPerPage(self):
        p = Pager(numChannels=5, channelsPerPage=8)
        for i in xrange(0, 5):
            self.assertEquals(0, p.pageUp(i))
        
    def test_pageUp_numChannels_gt_channelsPerPage(self):
        p = Pager(numChannels=18, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(16, p.pageUp(i))
        for i in xrange(8, 16):
            self.assertEquals(0, p.pageUp(i))
        for i in xrange(16,19):
            self.assertEquals(8, p.pageUp(i))

    def test_pageUp_numChannels_divisible_channelsPerPage(self):
        p = Pager(numChannels=24, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(16, p.pageUp(i))
        for i in xrange(8, 16):
            self.assertEquals(0, p.pageUp(i), 'i=%d'%i)
        for i in xrange(16, 24):
            self.assertEquals(8, p.pageUp(i), 'i=%d'%i)
        
        p = Pager(numChannels=8, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(0, p.pageUp(i))

        p = Pager(numChannels=16, channelsPerPage=8)
        for i in xrange(0, 8):
            self.assertEquals(8, p.pageUp(i))
        for i in xrange(8, 16):
            self.assertEquals(0, p.pageUp(i))
             
# =============================================================================
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
