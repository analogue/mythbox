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
import unittest2 as unittest
import feedparser

log = mythboxtest.getLogger('mythbox.unittest')

class FeedParserTest(unittest.TestCase):
    
    def test_mythbox_atom_feed(self):
        d = feedparser.parse('http://mythbox-xbmc.blogspot.com/feeds/posts/default')
        log.debug('Atom title = %s' % d.feed.title)
        log.debug('Atom link  = %s' % d.feed.link)
        log.debug('Atom desc  = %s' % d.feed.description)
        log.debug('Atom date  = %s' % d.feed.date)
        log.debug('Atom dp    = %s' % d.feed.date_parsed)
        
        for entry in d.entries:
            log.debug('Entry link = %s' % entry.link)
            log.debug('Entry desc = %s' % entry.description)
            log.debug('Entry summ = %s' % entry.summary)
            log.debug('Entry date = %s' % entry.date)
            log.debug('Entry dp   = %s' % entry.date_parsed)            
            log.debug('Entry id   = %s' % entry.id)
        
        self.assertEquals(u'MythBox for XBMC', d.feed.title)

    def test_mythbox_rss_feed(self):
        d = feedparser.parse('http://mythbox-xbmc.blogspot.com/feeds/posts/default?alt=rss')
        log.debug('RSS title = %s' % d.feed.title)
        log.debug('RSS link  = %s' % d.feed.link)
        log.debug('RSS desc  = %s' % d.feed.description)
        log.debug('RSS date  = %s' % d.feed.date)
        log.debug('RSS dp    = %s' % d.feed.date_parsed)
        
        for entry in d.entries:
            log.debug('Entry link = %s' % entry.link)
            log.debug('Entry desc = %s' % entry.description)
            log.debug('Entry summ = %s' % entry.summary)
            log.debug('Entry date = %s' % entry.date)
            log.debug('Entry dp   = %s' % entry.date_parsed)            
            log.debug('Entry id   = %s' % entry.id)
        
        self.assertEquals(u'MythBox for XBMC', d.feed.title)
