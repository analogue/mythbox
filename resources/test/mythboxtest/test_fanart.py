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
from mockito import Mock, when, verify, any, verifyZeroInteractions
from mythbox.fanart import chain, ImdbFanartProvider, TvdbFanartProvider, \
    TheMovieDbFanartProvider, GoogleImageSearchProvider, SuperFastFanartProvider, \
    OneStrikeAndYoureOutFanartProvider, SpamSkippingFanartProvider, \
    HttpCachingFanartProvider, TvRageProvider
from mythbox.filecache import FileCache, HttpResolver
from mythbox.mythtv.domain import TVProgram, Program, RecordedProgram
from mythbox.util import run_async, safe_str
from mythboxtest.mythtv.test_domain import pdata, socketDateTime
import mythbox.mythtv.protocol as protocol


import datetime
import mythboxtest
import os
import random
import shutil
import tempfile
import time
import unittest2 as unittest
from tvdb_exceptions import tvdb_error
from unittest2.case import SkipTest
from decorator import decorator

log = mythboxtest.getLogger('mythbox.unittest')

ustr = u'Königreich der Himmel'
P = protocol.Protocol57()


class ChainDecoratorTest(unittest.TestCase):

    class Link1(object):
        @chain
        def foo(self, p1):
            return None

    class Link2(object):
        @chain
        def foo(self, p1):
            return "Wow!"
    
    class Link3(object):
        @chain
        def foo(self, p1):
            return []
    
    class Link4(object):
        @chain
        def foo(self, p1):
            return ['Wee!']
        
    def test_chain_When_decorated_func_returns_none_Then_return_nextProviders_result(self):
        link1 = ChainDecoratorTest.Link1()
        link2 = ChainDecoratorTest.Link2()
        
        link1.nextProvider = link2
        link2.nextProvider = None
        
        result = link1.foo('blah')
        self.assertEqual("Wow!", result)

    def test_chain_When_decorated_func_returns_value_Then_return_value(self):
        link1 = ChainDecoratorTest.Link1()
        link2 = ChainDecoratorTest.Link2()
        
        link1.nextProvider = None
        link2.nextProvider = link1
        
        result = link2.foo('blah')
        self.assertEqual("Wow!", result)

    def test_chain_When_decorated_func_returns_none_and_nextProvider_none_Then_return_none(self):
        link1 = ChainDecoratorTest.Link1()
        link1.nextProvider = None
        result = link1.foo('blah')
        self.assertIsNone(result)

    def test_chain_When_decorated_func_returns_empty_list_Then_return_nextProviders_result(self):
        link3 = ChainDecoratorTest.Link3()
        link4 = ChainDecoratorTest.Link4()
        link3.nextProvider = link4
        result = link3.foo('blah')
        self.assertEqual('Wee!', result[0])

    def test_chain_When_decorated_func_returns_non_empty_list_Then_return_non_empty_list(self):
        link3 = ChainDecoratorTest.Link3()
        link4 = ChainDecoratorTest.Link4()
        link3.nextProvider = None
        link4.nextProvider = link3
        result = link4.foo('blah')
        self.assertEqual('Wee!', result[0])
        
    def test_chain_When_decorated_func_returns_empty_list_and_nextProvider_none_Then_return_empty_list(self):
        link3 = ChainDecoratorTest.Link3()
        link3.nextProvider = None
        result = link3.foo('blah')
        self.assertListEqual([], result)


    class SequenceWithValues(object):
        @chain
        def foo(self, p1):
            return "Wow", "Wee"

    class SequenceWithNones(object):
        @chain
        def foo(self, p1):
            return None, None

    def test_chain_When_decorated_func_returns_sequence_with_values_Then_return_sequence(self):
        link1 = ChainDecoratorTest.SequenceWithValues()
        link2 = ChainDecoratorTest.SequenceWithNones()
        
        link1.nextProvider = link2
        link2.nextProvider = None
        
        r1, r2 = link1.foo('blah')
        self.assertEqual('Wow', r1)
        self.assertEqual('Wee', r2)

    def test_chain_When_decorated_func_returns_sequence_with_nones_Then_return_nextproviders_result(self):
        link1 = ChainDecoratorTest.SequenceWithNones()
        link2 = ChainDecoratorTest.SequenceWithValues()
        
        link1.nextProvider = link2
        link2.nextProvider = None
        
        r1, r2 = link1.foo('blah')
        self.assertEqual('Wow', r1)
        self.assertEqual('Wee', r2)


class BaseFanartProviderTestCase(unittest.TestCase):
    
    movies = [
        u'The Shawshank Redemption',
        u'Ghostbusters',
        u'Memento',
        u'Pulp Fiction',
        u'No Country For Old Men',
        u'There Will Be Blood',
        u'Red Dawn',
        u'The Prestige',
        u'Caddyshack',
        u'Lost In Translation',
        u'Inglorious Basterds',
        u'Minority Report',
        u'Bottle Rocket',
        u'The Station Agent',
        u'Sling Blade',
        u'Apocalypse Now',
        u'Forrest Gump', 
        u'Born on the Fourth of July'
    ]

    tvShows = [
        u'Seinfeld',
        u'House',
        u'Desperate Housewives',
        u'30 Rock',
        u'60 Minutes',
        u'The Mentalist',
        u'Parks and Recreation',
        u'Smallville',
        u'The Simpsons',
        u'The Big Bang Theory',
        u'Chuck',
        u'The Good Wife',
        u'The Biggest Loser',
        u'Dancing with the Stars',
        u'Lost',
        u'Criminal Minds',
        u'The Marriage Ref',
        u'Star Trek',
        u'Family Guy',
        u'Dirty Jobs',
        u'Jackass',
        u'Ghost Whisperer',
        u'Friday Night Lights',
        u'Perry Mason'
    ]

    def getMovies(self):
        return map(lambda t: TVProgram({'title': t, 'category_type':'movie'}, translator=Mock()), self.movies)
        
    def getTvShows(self):
        return map(lambda t: TVProgram({'title': t, 'category_type':'series'}, translator=Mock()), self.tvShows)
        
    def base_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably(self):
        programs = self.getPrograms()
        provider = self.getProvider()
        
        @run_async
        def work(p):
            posters = provider.getPosters(p)
            if len(posters) == 0:
                log.exception('Failed on %s' % safe_str(p.title()))
                self.fail = True
            for poster in posters:
                log.debug('%s - %s' % (safe_str(p.title()), poster))

        self.fail = False
        threads = [] 
        for p in programs[:5]:
            threads.append(work(p))
        for t in threads:
            t.join()
            
        self.assertFalse(self.fail)
        

class ImdbFanartProviderTest(BaseFanartProviderTestCase):

    def getPrograms(self):
        return self.getMovies()
    
    def getProvider(self):
        return ImdbFanartProvider(nextProvider=None)
                
    def test_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably(self):
        self.base_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably()
        
    def test_getPosters_When_program_is_a_movie_Then_returns_fanart(self):
        # Setup
        program = TVProgram({'title':'Fargo', 'category_type':'movie'}, translator=Mock())
        provider = ImdbFanartProvider(nextProvider=None)
        
        # Test
        posters = provider.getPosters(program)
        
        # Verify
        log.debug('Poster URLs = %s' % posters)
        for p in posters:
            self.assertEqual('http', p[0:4])

    def test_getPosters_When_program_is_not_movie_Then_returns_empty_list(self):
        program = TVProgram({'title':'Seinfeld', 'category_type':'series'}, translator=Mock())
        provider = ImdbFanartProvider(nextProvider=None)
        self.assertListEqual([], provider.getPosters(program))
        

@decorator
def skipIfTvdbDown(func, *args, **kw):
    try:
        func(*args, **kw)
    except tvdb_error, e:
        if 'timed out' in str(e):
            raise SkipTest('TVDB down')
        else:
            raise e


class TvdbFanartProviderTest(BaseFanartProviderTestCase):
            
    def setUp(self):
        self.platform = Mock()
        self.sandbox = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        when(self.platform).getCacheDir().thenReturn(self.sandbox)
            
    def getPrograms(self):
        return self.getTvShows()
    
    def getProvider(self):
        return TvdbFanartProvider(self.platform, nextProvider=None)

    @skipIfTvdbDown
    def test_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably(self):
        self.base_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably()

    @skipIfTvdbDown
    def test_getPosters_When_program_is_not_movie_Then_returns_posters(self):
        # Setup
        program = TVProgram({'title':'Seinfeld', 'category_type':'series'}, translator=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        # Test
        posterUrls = provider.getPosters(program)
        
        # Verify
        log.debug('Poster URLs = %s' % posterUrls)
        for posterUrl in posterUrls:
            self.assertEqual("http", posterUrl[0:4])
 
    @skipIfTvdbDown
    def test_getPosters_When_program_is_movie_Then_returns_empty_list(self):
        program = TVProgram({'title':'Departed', 'category_type':'movie'}, translator=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        self.assertListEqual([], provider.getPosters(program))

    @skipIfTvdbDown
    def test_getPosters_When_title_has_funny_chars_Then_dont_fail_miserably(self):
        # Setup
        program = TVProgram({'title': u'Königreich der Himmel', 'category_type':'series'}, translator=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        # Test
        posters = provider.getPosters(program)
        
        # Verify
        log.debug('Posters = %s' % posters)
        for p in posters:
            self.assertEqual('http', p[0:4])

    @skipIfTvdbDown
    def test_getPosters_When_pounded_by_many_threads_looking_up_same_program_Then_doesnt_fail_miserably(self):
        
        programs = []
        for i in xrange(10): #@UnusedVariable
            programs.append(TVProgram({'title': 'Seinfeld', 'category_type':'series'}, translator=Mock()))
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        @run_async
        def work(p):
            posters = provider.getPosters(p)
            if len(posters) == 0:
                self.fail = True
            for poster in posters:
                log.debug('%s - %s' % (p.title(), poster))

        self.fail = False
        threads = [] 
        for p in programs:
            threads.append(work(p))
        for t in threads:
            t.join()

        self.assertFalse(self.fail)
        
    @skipIfTvdbDown
    def test_getSeasonAndEpisode_Success(self):
        # Given
        fields = {
            'title'     : u'The Real World',
            'starttime' : socketDateTime(2008, 11, 4, 22, 45, 00),
            'endtime'   : socketDateTime(2008, 11, 4, 23, 50, 00),
            'hasairdate': 1,
            'airdate'   : u'2010-07-14'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=Mock(), protocol=P, conn=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertEqual('24', season)
        self.assertEqual('3', episode)
        
    @skipIfTvdbDown
    def test_getSeasonAndEpisode_When_episode_not_found_Then_returns_none(self):
        # Given
        fields = {
            'title'     : u'MasterChef',
            'starttime' : socketDateTime(2008, 11, 4, 22, 45, 00),
            'endtime'   : socketDateTime(2008, 11, 4, 23, 50, 00),
            'hasairdate': 1,
            'airdate'   : u'2010-08-03'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=Mock(), protocol=P, conn=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertIsNone(season)
        self.assertIsNone(episode)

    @skipIfTvdbDown
    def test_getSeasonAndEpisode_When_show_not_found_Then_returns_none(self):
        # Setup
        fields = {
            'title'     : u'This Show Does Not Exist',
            'starttime' : socketDateTime(2008, 11, 4, 22, 45, 00),
            'endtime'   : socketDateTime(2008, 11, 4, 23, 45, 00),
            'hasairdate': 1,
            'airdate'   : u'2010-08-03'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=Mock(), protocol=P, conn=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertIsNone(season)
        self.assertIsNone(episode)
        
    @skipIfTvdbDown
    def test_getBanners_When_program_is_not_movie_Then_returns_banners(self):
        # Setup
        program = TVProgram({'title':'Seinfeld', 'category_type':'series'}, translator=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        # Test
        bannerUrls = provider.getBanners(program)
        
        # Verify
        [log.debug('Banner = %s' % banner) for banner in bannerUrls]
        self.assertTrue(len(bannerUrls) > 0)
        for bannerUrl in bannerUrls:
            self.assertEqual("http", bannerUrl[0:4])

    @skipIfTvdbDown
    def test_getBackgrounds_When_program_is_not_movie_Then_returns_backgrounds(self):
        # Setup
        program = TVProgram({'title':'Seinfeld', 'category_type':'series'}, translator=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        
        # Test
        urls = provider.getBackgrounds(program)
        
        # Verify
        [log.debug('Background = %s' % url) for url in urls]
        self.assertTrue(len(urls) > 0)
        for url in urls:
            self.assertEqual("http", url[0:4])

    @skipIfTvdbDown
    def test_getPosters_When_title_has_override_Then_returns_posters_for_override(self):
        # 'Conan' is mapped to 'Conan (2010)' as TVDB's official title
        program = TVProgram({'title':u'Conan', 'category_type':u'series'}, translator=Mock())
        provider = TvdbFanartProvider(self.platform, nextProvider=None)
        urls = provider.getPosters(program)
        self.assertTrue(len(urls) > 0)
        
        
class TheMovieDbFanartProviderTest(BaseFanartProviderTestCase):

    def getPrograms(self):
        return self.getMovies()
    
    def getProvider(self):
        return TheMovieDbFanartProvider(nextProvider=None)

    def test_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably(self):
        self.base_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably()

    def test_getPosters_When_program_is_movie_Then_returns_posters(self):
        # Setup
        program = TVProgram({'title': 'Ghostbusters', 'category_type':'movie'}, translator=Mock())
        provider = TheMovieDbFanartProvider(nextProvider=None)
        
        # Test
        posters = provider.getPosters(program)
        
        # Verify
        log.debug('Posters = %s' % posters)
        for p in posters:
            self.assertEqual('http', p[0:4])

    def test_getPosters_When_program_is_not_movie_Then_returns_empty_list(self):
        program = TVProgram({'title': 'Seinfeld', 'category_type':'series'}, translator=Mock())
        provider = TheMovieDbFanartProvider(nextProvider=None)
        self.assertListEqual([], provider.getPosters(program))


class GoogleImageSearchProviderTest(BaseFanartProviderTestCase):

    def getPrograms(self):
        return self.getMovies()
    
    def getProvider(self):
        return GoogleImageSearchProvider(nextProvider=None)

    def test_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably(self):
        self.base_getPosters_When_pounded_by_many_threads_Then_doesnt_fail_miserably()
        
    def test_getPosters_works(self):
        # Setup
        program = TVProgram({'title': 'Top Chef', 'category_type':'series'}, translator=Mock())
        provider = GoogleImageSearchProvider(nextProvider=None)
        
        # Test
        posters = provider.getPosters(program)
        
        # Verify
        log.debug('Posters = %s' % posters)
        self.assertTrue(len(posters) > 0)
        for p in posters:
            self.assertEqual('http', p[0:4])

    def test_getPosters_When_title_has_funny_chars_Then_dont_fail_miserably(self):
        # Setup
        program = TVProgram({'title': u'Königreich der Himmel', 'category_type':'series'}, translator=Mock())
        provider = GoogleImageSearchProvider(nextProvider=None)
        
        # Test
        posters = provider.getPosters(program)
        
        # Verify
        log.debug('Posters = %s' % posters)
        self.assertTrue(len(posters) > 0)
        for p in posters:
            self.assertEqual('http', p[0:4])


class HttpCachingFanartProviderTest(unittest.TestCase):

    def setUp(self):
        self.nextProvider = Mock()
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.httpCache = FileCache(self.dir, HttpResolver())
        self.program = TVProgram({'title': 'Not Important', 'category_type':'series'}, translator=Mock())
        self.provider = HttpCachingFanartProvider(self.httpCache, self.nextProvider)
        self.addCleanup(self.provider.close)

    def test_getPosters_When_next_provider_returns_posters_Then_cache_and_return_first_poster_and_add_remaining_to_work_queue(self):
        httpUrls = [
            'http://www.gstatic.com/hostedimg/1f4337d461f1431c_large',
            'http://www.gstatic.com/hostedimg/50edad09a73fa0ed_large',
            'http://www.gstatic.com/hostedimg/d915322b880dcaf2_large',
            'http://www.gstatic.com/hostedimg/998ad397414e3727_large',
            'http://www.gstatic.com/hostedimg/ba55ddda30df5f96_large',
            'http://www.gstatic.com/hostedimg/7f0a19596a92fad1_large',
            'http://www.gstatic.com/hostedimg/8edb2dfe5ba34685_large',
            'http://www.gstatic.com/hostedimg/ffdb442e9f46a3c3_large']
             
        when(self.nextProvider).getPosters(any(Program)).thenReturn(httpUrls)
        
        # Test
        posters = self.provider.getPosters(self.program)
        
        # Verify
        log.debug('Posters= %s' % posters)
        self.assertEqual(1, len(posters))
        
        while len(posters) < len(httpUrls):
            time.sleep(1)
            log.debug('Images downloaded: %d' % len(posters))
        
    def test_getPosters_When_next_link_in_chain_returns_posters_Then_cache_locally_on_filesystem(self):
        # Setup
        when(self.nextProvider).getPosters(any(Program)).thenReturn(['http://www.google.com/intl/en_ALL/images/logo.gif'])
        when(self.httpCache).get(any(str)).thenReturn('logo.gif')
        
        # Test
        posters = self.provider.getPosters(self.program)
        
        # Verify
        log.debug('Posters= %s' % posters)
        self.assertEqual('logo.gif', posters[0])

    def test_getPosters_When_next_link_in_chain_doesnt_find_posters_Then_dont_cache_anything(self):
        when(self.nextProvider).getPosters(any(Program)).thenReturn([])
        self.assertListEqual([], self.provider.getPosters(self.program))

        
class OneStrikeAndYoureOutFanartProviderTest(unittest.TestCase):

    def setUp(self):
        self.delegate = Mock()
        self.nextProvider = Mock()
        self.platform = Mock()
        self.sandbox = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.sandbox)
        when(self.platform).getCacheDir().thenReturn(self.sandbox)
        self.program = TVProgram({
            'title': 'Two Fat Ladies', 
            'category_type':'series',
            'channum' : '5.1',
            'starttime' : datetime.datetime.now(),
            'endtime': datetime.datetime.now(),
            'subtitle': 'blah',
            'description': 'blah'
            },
            translator=Mock())
    
    def test_getPosters_When_not_struck_out_and_delegate_returns_empty_list_Then_strike_out_and_return_nextProviders_result(self):
        # Setup
        provider = OneStrikeAndYoureOutFanartProvider(self.platform, self.delegate, self.nextProvider)
        key = provider.createKey('getPosters', self.program)
        when(self.delegate).getPosters(any()).thenReturn([])
        when(self.nextProvider).getPosters(any()).thenReturn(['blah.png'])
        
        # Test
        posters = provider.getPosters(self.program)
        
        # Verify
        self.assertEqual('blah.png', posters[0])
        self.assertIn(self.program.title(), provider.struckOut[key].values())
        
    def test_getPosters_When_not_struck_out_and_delegate_returns_posters_Then_return_posters(self):
        # Setup
        provider = OneStrikeAndYoureOutFanartProvider(self.platform, self.delegate, self.nextProvider)
        when(self.delegate).getPosters(any()).thenReturn(['blah.png'])
        
        # Test
        posters = provider.getPosters(self.program)
        
        # Verify
        self.assertEqual('blah.png', posters[0])
        self.assertNotIn(self.program.title(), provider.struckOut.values())
        verifyZeroInteractions(self.nextProvider)

    def test_getPosters_When_struck_out_Then_skip_delegate_and_return_nextProviders_result(self):
        # Setup
        provider = OneStrikeAndYoureOutFanartProvider(self.platform, self.delegate, self.nextProvider)
        key = provider.createKey('getPosters', self.program)
        provider.strikeOut(key, self.program)
        when(self.nextProvider).getPosters(any()).thenReturn(['blah.png'])
        
        # Test
        posters = provider.getPosters(self.program)
        
        # Verify
        self.assertEqual('blah.png', posters[0])
        self.assertIn(self.program.title(), provider.struckOut[key].values())
        verifyZeroInteractions(self.delegate)

    def test_clear_When_struckout_not_empty_Then_empties_struckout_and_forwards_to_delegate(self):
        # Setup
        provider = OneStrikeAndYoureOutFanartProvider(self.platform, self.delegate, self.nextProvider)
        provider.struckOut[self.program.title()] = self.program.title()
        
        # Test
        provider.clear()
        
        # Verify
        self.assertFalse(len(provider.struckOut))
        verify(self.delegate, times=1).clear(any())
        
    def test_constructor_When_delegate_is_none_Then_raise_exception(self):
        try:
            OneStrikeAndYoureOutFanartProvider(self.platform, delegate=None, nextProvider=self.nextProvider)
            self.fail('Expected exception to be thrown when delegate is null')
        except Exception:
            log.debug('SUCCESS: got exception on null delegate')

    def test_getSeasonAndEpisode_When_not_struck_out_and_delegate_returns_empty_tuple_Then_strike_out_and_return_nextProviders_result(self):
        # Setup
        provider = OneStrikeAndYoureOutFanartProvider(self.platform, self.delegate, self.nextProvider)
        key = provider.createKey('getSeasonAndEpisode', self.program)
        when(self.delegate).getSeasonAndEpisode(any()).thenReturn((None,None,))
        when(self.nextProvider).getSeasonAndEpisode(any()).thenReturn(('1','2',))
        
        # Test
        season, episode = provider.getSeasonAndEpisode(self.program)
        
        # Verify
        self.assertEqual('1', season)
        self.assertEqual('2', episode)
        self.assertIn(self.program.title(), provider.struckOut[key].values())

    def test_getSeasonAndEpisode_When_struck_out_Then_skip_delegate_and_return_nextProviders_result(self):
        # Setup
        provider = OneStrikeAndYoureOutFanartProvider(self.platform, self.delegate, self.nextProvider)
        key = provider.createKey('getSeasonAndEpisode', self.program)
        provider.strikeOut(key, self.program)
        when(self.nextProvider).getSeasonAndEpisode(any()).thenReturn(('1','2'))
        
        # Test
        season, episode = provider.getSeasonAndEpisode(self.program)
        
        # Verify
        self.assertEqual('1', season)
        self.assertEqual('2', episode)
        self.assertIn(self.program.title(), provider.struckOut[key].values())
        verifyZeroInteractions(self.delegate)

    def test_getSeasonAndEpisode_When_not_struck_out_and_delegate_returns_season_and_episode_Then_return_season_and_episode(self):
        # Setup
        provider = OneStrikeAndYoureOutFanartProvider(self.platform, self.delegate, self.nextProvider)
        when(self.delegate).getSeasonAndEpisode(any()).thenReturn(('1','2',))
        
        # Test
        season, episode = provider.getSeasonAndEpisode(self.program)
        
        # Verify
        self.assertEqual('1', season)
        self.assertEqual('2', episode)
        self.assertNotIn(self.program.title(), provider.struckOut.values())
        verifyZeroInteractions(self.nextProvider)


class SpamSkippingFanartProviderTest(unittest.TestCase):
        
    def setUp(self):
        self.spam = TVProgram({'title': 'Paid Programming', 'category_type':'series'}, translator=Mock())
        self.notSpam = TVProgram({'title': 'I am not spam', 'category_type':'series'}, translator=Mock())
        self.next = Mock()
        self.provider = SpamSkippingFanartProvider(nextProvider=self.next)  
            
    def test_getPosters_When_spam_Then_returns_no_posters(self):
        self.assertListEqual([], self.provider.getPosters(self.spam))
        
    def test_getPosters_When_not_spam_Then_forwards_to_next(self):
        when(self.next).getPosters(any()).thenReturn(['blah.png'])
        self.assertEqual('blah.png', self.provider.getPosters(self.notSpam)[0])
     
    def test_hasPosters_When_spam_Then_true(self):
        self.assertTrue(self.provider.hasPosters(self.spam))

    def test_hasPosters_When_not_spam_Then_forwards_to_next(self):
        when(self.next).hasPosters(any()).thenReturn(False)
        self.assertFalse(self.provider.hasPosters(self.notSpam))


class SuperFastFanartProviderTest(unittest.TestCase):
    
    def setUp(self):
        self.sandbox = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        self.nextProvider = Mock()
        self.platform = Mock()
        when(self.platform).getCacheDir().thenReturn(self.sandbox)
        self.program = TVProgram({'title': 'Two Fat Ladies', 'category_type':'series'}, translator=Mock())
        self.provider = SuperFastFanartProvider(self.platform, self.nextProvider)

    @staticmethod
    def programs(cnt):
        for i in xrange(cnt): #@UnusedVariable
            yield TVProgram({
                'starttime': '20081121140000',
                'endtime'  : '20081121140000',
                'chanid'   : random.randint(1,9999999),
                'channum'  : str(random.randint(1,10)),
                'title'    : 'Two Fat Ladies %d' % random.randint(1,999999),
                'subtitle' : 'Away we go....', 
                'description' : 'blah blah blah', 
                'category_type':'series'}, 
                translator=Mock())

    def test_pickling(self):
        when(self.nextProvider).getPosters(any(Program)).thenReturn(['logo.gif'])
        for p in self.programs(20000):
            self.provider.getPosters(p)
        self.provider.close()
        filesize = os.path.getsize(self.provider.pfilename)
        log.debug('Pickle file size = %d' % filesize)
        self.assertGreater(filesize, 0)
        
    def test_cache_consistent_across_sessions(self):
        sandbox = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, sandbox, ignore_errors=True)
        nextProvider = Mock()
        platform = Mock()
        when(platform).getCacheDir().thenReturn(sandbox)
        when(nextProvider).getPosters(any(Program)).thenReturn(['http://a.com/a.gif', 'http://b.com/b.gif', 'http://c.com/c.gif', 'http://d.com/d.gif'])
        provider = SuperFastFanartProvider(platform, nextProvider)

        programs = []        
        for i in xrange(1000):
            program = TVProgram({'title': 'P%d' % i, 'category_type':'series'}, translator=Mock())
            httpUrls = provider.getPosters(program)
            self.assertTrue(4, len(httpUrls))
            programs.append(program)
        provider.close()
        
        nextProvider = Mock()
        provider2 = SuperFastFanartProvider(platform, nextProvider)
        for p in programs:
            httpUrls = provider2.getPosters(p)
            self.assertTrue(4, len(httpUrls))
        provider2.close()
    
    def test_getPosters_When_posters_not_in_cache_and_returned_by_next_in_chain_Then_cache_locally_and_return_posters(self):
        # Setup
        when(self.nextProvider).getPosters(any(Program)).thenReturn(['logo.gif'])
        key = self.provider.createKey('getPosters', self.program)
        self.assertNotIn(key, self.provider.imagePathsByKey)
                        
        # Test
        posters = self.provider.getPosters(self.program)
        
        # Verify
        log.debug('Posters = %s' % posters)
        self.assertEqual('logo.gif', posters[0])
        self.assertIn(key, self.provider.imagePathsByKey)

    def test_getPosters_When_next_link_in_chain_doesnt_find_posters_Then_dont_cache_anything(self):
        # Setup
        when(self.nextProvider).getPosters(any(Program)).thenReturn([])
        key = self.provider.createKey('getPosters', self.program)
        self.assertNotIn(key, self.provider.imagePathsByKey)
                        
        # Test
        posters = self.provider.getPosters(self.program)
        
        # Verify
        self.assertListEqual([], posters)
        self.assertNotIn(key, self.provider.imagePathsByKey)

    def test_createKey_When_program_title_contains_unicode_chars_Then_dont_blow_up(self):
        program = TVProgram({'title': u'madeleine (Grabación Manual)', 'category_type':'series'}, translator=Mock())
        key = self.provider.createKey('getPosters', program)
        self.assertGreater(len(key), 0)


class TvRageProviderTest(unittest.TestCase):
    
    def setUp(self):
        self.sandbox = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        self.platform = Mock()
        when(self.platform).getCacheDir().thenReturn(self.sandbox)
    
    def test_getSeasonAndEpisode_Success(self):
        # Given
        fields = {
            'title'     : u'The Real World',
            'starttime' : socketDateTime(2008, 11, 4, 23, 45, 00), 
            'endtime'   : socketDateTime(2008, 11, 4, 23, 45, 00),
            'hasairdate': 1,
            'airdate'   : u'2010-07-14'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=self.platform, protocol=P, conn=Mock())
        provider = TvRageProvider(self.platform)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertEqual('24', season)
        self.assertEqual('3', episode)

    def test_getSeasonAndEpisode_Success_HouseHunters(self):
        # Given
        fields = {
            'title'     : u'House Hunters',
            'starttime' : socketDateTime(2010, 12, 2, 22, 45, 00), 
            'endtime'   : socketDateTime(2010, 12, 2, 23, 50, 00),
            'hasairdate': 1,
            'airdate'   : u'2008-11-02'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=self.platform, protocol=P, conn=Mock())
        provider = TvRageProvider(self.platform)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertEqual('30', season)
        self.assertEqual('2', episode)

    def test_getSeasonAndEpisode_dont_blowup_when_a_season_is_missing(self):
        # Given
        fields = {
            'title'     : u'The Daily Show With Jon Stewart',
            'starttime' : socketDateTime(2010, 12, 2, 22, 45, 00), 
            'endtime'   : socketDateTime(2010, 12, 2, 23, 50, 00),
            'hasairdate': 1,
            'airdate'   : u'2005-01-04'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=self.platform, protocol=P, conn=Mock())
        provider = TvRageProvider(self.platform)
        
        # When -- Season 3 for The Daily Show with Jon Stewart is missing
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertIsNotNone(season)
        self.assertIsNotNone(episode)

    def test_getSeasonAndEpisode_When_show_not_found_Then_returns_none(self):
        # Given
        fields = {
            'title'     : u'Crap Crappity Crapola',
            'starttime' : socketDateTime(2008, 11, 4, 22, 45, 00),
            'endtime'   : socketDateTime(2008, 11, 4, 23, 50, 00),
            'hasairdate': 1,
            'airdate'   : u'2010-08-03'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=self.platform, protocol=P, conn=Mock())
        provider = TvRageProvider(self.platform)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertIsNone(season)
        self.assertIsNone(episode)

    def test_getSeasonAndEpisode_try_to_cache_output(self):
        # Given
        fields = {
            'title'     : u'Seinfeld',
            'starttime' : socketDateTime(2008, 11, 4, 23, 45, 00), 
            'endtime'   : socketDateTime(2008, 11, 4, 23, 50, 00),
            'hasairdate': 1,
            'airdate'   : u'1989-07-05'
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=self.platform, protocol=P, conn=Mock())
        provider = TvRageProvider(self.platform)
        
        # When
        for i in xrange(100):  #@UnusedVariable
            # TODO Verify hitting cache < 1sec per invocation.
            #      Since tvrage api is not injected, cannot mock
            season, episode = provider.getSeasonAndEpisode(program)
            # Then
            self.assertEqual('1', season)
            self.assertEqual('1', episode)

    def test_getSeasonAndEpisode_When_match_not_found_using_original_airdate_Then_match_by_subtitle(self):
        # Given
        fields = {
            'title'     : u'WCG Ultimate Gamer',
            'subtitle'  : u'In The Crosshairs',
            'starttime' : socketDateTime(2010, 12, 2, 22, 45, 00), 
            'endtime'   : socketDateTime(2010, 12, 2, 23, 50, 00),
            'hasairdate': 1,
            'airdate'   : u'2010-09-20',   # TVRage shows date as 2010-09-16
        }
        program = RecordedProgram(data=pdata(fields,P.version()), settings=Mock(), translator=Mock(), platform=self.platform, protocol=P, conn=Mock())
        provider = TvRageProvider(self.platform)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertEqual('2', season)
        self.assertEqual('5', episode)

    def test_getSeasonAndEpisode_NBCNightlyNews_returns_None_cuz_TVRage_throws_KeyError(self):
        # Given
        fields = {
            'title'       :u'NBC Nightly News',
            'subtitle'    :u'blah',
            'starttime'   :socketDateTime(2008, 11, 4, 23, 45, 00),
            'endtime'     :socketDateTime(2008, 11, 4, 23, 50, 00),
            'hasairdate'  :1,
            'airdate'     :u'2010-07-14'
        }
        
        program = RecordedProgram(pdata(fields, P.version()), settings=Mock(), translator=Mock(), platform=self.platform, protocol=P, conn=Mock())
        provider = TvRageProvider(self.platform)
        
        # When
        season, episode = provider.getSeasonAndEpisode(program)
        
        # Then
        self.assertIsNone(season)
        self.assertIsNone(episode)
