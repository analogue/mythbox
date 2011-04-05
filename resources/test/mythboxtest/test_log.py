# -*- coding: utf-8 -*-
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
import os
import mythboxtest
import unittest2 as unittest
import tempfile
import shutil
import time

from mythbox.util import run_async
from mythbox.log import LogScraper

log = mythboxtest.getLogger('mythbox.unittest')

class LogScraperTest(unittest.TestCase):    

    def setUp(self):
        self.sandbox = tempfile.mkdtemp()
        self.abortGrow = False
        
    def tearDown(self):
        shutil.rmtree(self.sandbox, ignore_errors=True)

    @run_async
    def growFile(self, fname, contents, writeLineEveryEnnSeconds):
        f = open(fname, 'w+')
        for line in contents:
            print('Writing "%s" to %s' % (line, fname))
            f.write(line)
            f.flush()
            time.sleep(writeLineEveryEnnSeconds)
            if self.abortGrow:
                break
        f.close()
        
    def test_matchLineAsync_When_search_string_found_Then_callback_invoked_with_matching_text(self):

        fname = os.path.join(self.sandbox, 'xbmc.log')

        try:
            t = self.growFile(fname, ['aaa','bbb','ccc','xxx','yyy'], 1)
            while not os.path.exists(fname):
                time.sleep(1)
            
            def mycallback(s):
                log.debug('mycallback received %s' % s)
                self.callbackResult = s
                
            scraper = LogScraper(fname)
            worker = scraper.matchLineAsync('xxx', 10, mycallback)
            worker.join()
            self.assertEqual('xxx', self.callbackResult)
        finally:
            self.abortGrow = True
            t.join()

    def test_matchLineAsync_When_search_string_not_found_Then_callback_invoked_with_None(self):

        fname = os.path.join(self.sandbox, 'xbmc.log')

        try:
            t = self.growFile(fname, ['aaa','bbb','ccc','xxx','yyy'], 1)
            while not os.path.exists(fname):
                time.sleep(1)
            
            def mycallback(s):
                log.debug('mycallback received %s' % s)
                self.callbackResult = s
                
            scraper = LogScraper(fname)
            worker = scraper.matchLineAsync('zzz', 3, mycallback)
            worker.join()
            self.assertIsNone(self.callbackResult)
        finally:
            self.abortGrow = True
            t.join()
        
    def test_matchLine_When_search_string_found_Then_return_matching_text(self):
        
        fname = os.path.join(self.sandbox, 'xbmc.log')
        
        try:
            t = self.growFile(fname, ['aaa','bbb','ccc','xxx','yyy'], 1)
            
            while not os.path.exists(fname):
                time.sleep(1)
            
            scraper = LogScraper(fname)
            text = scraper.matchLine('xxx', 10)
            print 'text = %s ' % text
            self.assertEqual('xxx',text)
        finally:
            self.abortGrow = True
            t.join()

    def test_matchLine_When_search_string_eventually_shows_up_in_log_but_times_out_first_Then_return_None(self):
        
        fname = os.path.join(self.sandbox, 'xbmc.log')
        
        try:
            t = self.growFile(fname, ['aaa','bbb','ccc','xxx','yyy'], 1)
            
            while not os.path.exists(fname):
                time.sleep(1)
            
            scraper = LogScraper(fname)
            text = scraper.matchLine('yyy', 1)
            self.assertIsNone(text)
        finally:
            self.abortGrow = True
            t.join()

    def test_matchLine_When_search_string_not_found_Then_times_out_and_returns_None(self):
        
        fname = os.path.join(self.sandbox, 'xbmc.log')
        
        try:
            t = self.growFile(fname, ['aaa','bbb','ccc'], 1)
            
            while not os.path.exists(fname):
                time.sleep(1)
            
            scraper = LogScraper(fname)
            text = scraper.matchLine('zzz', 5)
            self.assertIsNone(text)
        finally:
            self.abortGrow = True
            t.join()

    def test_matchLine_When_called_in_succession_many_times_Then_doesnt_fail(self):
        
        fname = os.path.join(self.sandbox, 'xbmc.log')
        
        try:
            t = self.growFile(fname, ['aaa','bbb','ccc','xxx','yyy','zzz','jjj'], 1)
            
            while not os.path.exists(fname):
                time.sleep(1)
            
            scraper = LogScraper(fname)
            self.assertEqual('ccc', scraper.matchLine('ccc', 5))
            self.assertEqual('yyy', scraper.matchLine('yyy', 5))
            self.assertEqual('jjj', scraper.matchLine('jjj', 5))
        finally:
            self.abortGrow = True
            t.join()

    def test_matchLine_When_file_does_not_exist_Then_throws_IOError(self):
        fname = os.path.join(self.sandbox, 'bogus.log')
        scraper = LogScraper(fname)

        try:
            scraper.matchLine('ccc', 5)
            self.fail('Expected IOError on non-existant file')
        except IOError:
            # SUCCESS
            pass
