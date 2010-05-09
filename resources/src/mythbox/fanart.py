# -*- coding: utf-8 -*-
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
import md5
import os
import random
import tmdb
import imdb
import imdb.helpers
import shove
import shutil
import simplejson as json
import urllib2
import urllib

from decorator import decorator
from mythbox.util import synchronized, safe_str, run_async
from tvdb_api import Tvdb

log = logging.getLogger('mythbox.fanart')

# =============================================================================
@decorator
def chain(func, *args, **kwargs):
    provider = args[0]
    result = func(*args, **kwargs)
    if not result and provider.nextProvider:
        nfunc = getattr(provider.nextProvider, func.__name__)
        return nfunc(*args[1:], **kwargs)
    else:
        return result

# =============================================================================
class BaseFanartProvider(object):

    def __init__(self, nextProvider=None):
        self.nextProvider = nextProvider
        
    def getPosters(self, program):
        raise Exception, 'Abstract method'
    
    def getRandomPoster(self, program):
        posters = self.getPosters(program)
        if posters:
            return random.choice(posters)
        else:
            return None

    def clear(self):
        if self.nextProvider:
            self.nextProvider.clear()
    
    def close(self):
        if self.nextProvider:
            self.nextProvider.close()

# =============================================================================
class NoOpFanartProvider(BaseFanartProvider):

    def getPosters(self, program):
        return []
    
    def getRandomPoster(self, program):
        return None
    
# =============================================================================
class OneStrikeAndYoureOutFanartProvider(BaseFanartProvider):
    """
    If a fanart provider can't serve up fanart for a program the first time, 
    chances are it won't succeed on subsequent requests. For instances where
    subsequent requests can be 'expensive', this decorator will short-circuit
    the lookup process after <insert criteria here>.
    """
    
    def __init__(self, platform, delegate, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)
        if not delegate:
            raise Exception('delegate cannot be None')
        self.delegate = delegate
        self.struckOut = shove.Shove('file://' + os.path.join(platform.getScriptDataDir(), 'oneStrikeAndYoureOut'))

    def createKey(self, method, program):
        return '%s-%s' % (method, md5.new(safe_str(program.title())).hexdigest())
        
    @synchronized
    def hasStruckOut(self, key):
        return key in self.struckOut
    
    @synchronized
    def strikeOut(self, key, program):
        self.struckOut[key] = program.title()
    
    @chain
    def getPosters(self, program):
        posters = []
        key = self.createKey('getPosters', program) 
        if not self.hasStruckOut(key):
            posters = self.delegate.getPosters(program)
            if not posters:
                self.strikeOut(key, program)
        return posters
    
    def clear(self):
        super(OneStrikeAndYoureOutFanartProvider, self).clear()
        self.struckOut.clear()
        self.struckOut.sync()
        self.delegate.clear()

    def close(self):
        super(OneStrikeAndYoureOutFanartProvider, self).close()
        self.struckOut.close()
        self.delegate.close()
        
# =============================================================================
class SpamSkippingFanartProvider(BaseFanartProvider):
    """
    Lets not waste cycles looking up fanart for programs which probably don't
    have fanart.
    """
    
    SPAM = ['Paid Programming', 'No Data'] 
    
    def __init__(self, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)
    
    def getPosters(self, program):
        if (program.title() in SpamSkippingFanartProvider.SPAM):
            return []
        if self.nextProvider:
            return self.nextProvider.getPosters(program)
                
    def hasPosters(self, program):
        if (program.title() in SpamSkippingFanartProvider.SPAM):
            return True
        return self.nextProvider.hasPosters(program)
        
# =============================================================================
class SuperFastFanartProvider(BaseFanartProvider):
    """
    A fanart provider that remembers past attempts to lookup fanart and returns
    locally cached results (fast) instead of hitting the network (slow). This 
    can be good (super fast) and bad (images may become stale if fanart is updated 
    in the system of record) but then everything has its trade-offs :-)
    """
    
    def __init__(self, platform, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)
        self.platform = platform
        # TODO: durus craps out when running in xbmc for some reason. file r/w perm related...
        #self.imagePathsByKey = shove.Shove('durus://' + os.path.join(platform.getScriptDataDir(), 'superFastFanartProviderDb'))
        self.imagePathsByKey = shove.Shove('file://' + os.path.join(platform.getScriptDataDir(), 'superFastFanartProviderDb'))

    def getPosters(self, program):
        posters = []
        key = self.createKey('getPosters', program)
        if key in self.imagePathsByKey:
            posters = self.imagePathsByKey[key]
        
        if not posters and self.nextProvider:
            posters = self.nextProvider.getPosters(program)
            if posters:  # cache returned poster 
                self.imagePathsByKey[key] = posters
                # TODO: Figure out if this is detrimental to performance -- sync on update
                self.imagePathsByKey.sync()
        return posters
        
    def hasPosters(self, program):
        return self.createKey('getPosters', program) in self.imagePathsByKey
        
    def createKey(self, methodName, program):
        key = "%s-%s" % (methodName, safe_str(program.title()))
        return key
    
    def clear(self):
        super(SuperFastFanartProvider, self).clear()
        self.imagePathsByKey.clear()
        self.imagePathsByKey.sync()

    def close(self):
        super(SuperFastFanartProvider, self).close()
        self.imagePathsByKey.close()
        
# =============================================================================
class CachingFanartProvider(BaseFanartProvider):
    """
    Caches references to fanart images retrieved via http on the local filesystem
    """
    
    def __init__(self, httpCache, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)
        self.httpCache = httpCache

    def getPosters(self, program):
        # If the chained provider returns a http:// style url, 
        # cache the contents and return the locally cached file path
        posters = []
        if self.nextProvider:
            httpPosters = self.nextProvider.getPosters(program)
            posters = self.cachePosters(httpPosters)
            #for p in httpPosters:
            #    poster = self.tryToCache(p)
            #    if poster:
            #        posters.append(poster)
        return posters

    def cachePosters(self, httpPosters):
        results = []
        
        @run_async
        def async_wrapper(poster):
            poster = self.tryToCache(poster)
            if poster:
                results.append(poster)
        
        workers = []
        for p in httpPosters:    
            workers.append(async_wrapper(p))
            
        for w in workers:
            w.join()
    
        return results
    
    def tryToCache(self, poster):
        if poster and poster[:4] == 'http':
            try:
                poster = self.httpCache.get(poster)
            except Exception, ioe:
            #except IOError, ioe:
                log.exception(ioe)
                return None
        return poster
    
    def clear(self):
        super(CachingFanartProvider, self).clear()
        self.httpCache.clear()
        
# =============================================================================
class ImdbFanartProvider(BaseFanartProvider):

    def __init__(self, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)
        self.imdb = imdb.IMDb(accessSystem='httpThin')

    @chain
    def getPosters(self, program):
        posters = []
        if program.isMovie():
            try:
                movies = self.imdb.search_movie(title=program.title(), results=1)
                for movie in movies:
                    m = self.imdb.get_movie(movie.getID())
                    #for key,value in m.items():
                    #    log.debug('movie[%d] id[%s] key[%s] -> %s' % (index, m.getID(), key, value))
                    posters.append(imdb.helpers.fullSizeCoverURL(m['cover url']))
            except imdb.IMDbError, e:
                log.error('IMDB error looking up movie: %s' % program.title())
            except Exception, e:
                log.error('IMDB error looking up %s: %s' % (program.title(), str(e)))
        return posters
    
# =============================================================================
class TvdbFanartProvider(BaseFanartProvider):
    
    def __init__(self, platform, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)
        self.tvdbCacheDir = os.path.join(platform.getScriptDataDir(), 'tvdbFanartProviderCache')
        self.tvdb = Tvdb(interactive=False, 
            select_first=True, 
            debug=False, 
            cache=self.tvdbCacheDir, 
            banners=True, 
            actors=False, 
            custom_ui=None, 
            language=None, 
            search_all_languages=False, 
            apikey='E2032A158BE34568')
    
    @chain
    def getPosters(self, program):
        posters = []
        if not program.isMovie():
            try:
                # Example: tvdb['scrubs']['_banners']['poster']['680x1000']['35308']['_bannerpath']
                #posterUrl = self.tvdb[program.title()]['_banners']['poster'].itervalues().next().itervalues().next()['_bannerpath']
                
                # TODO: Fix this --  TVDB errored out on "K�nigreich der Himmel" with error "'ascii' codec can't decode byte 0xc3 in position 1: ordinal not in range(128)"
                postersByDimension = self._queryTvDb(program.title()) 
                for dimension in postersByDimension.keys():
                    log.debug('key=%s' % dimension)
                    for id in postersByDimension[dimension].keys():
                        log.debug('idkey = %s' % id)
                        bannerPath = postersByDimension[dimension][id]['_bannerpath']
                        log.debug('bannerPath = %s' % bannerPath)
                        posters.append(bannerPath)
            except Exception, e:
                log.error('TVDB errored out on "%s" with error "%s"' % (program.title(), str(e)))
        return posters

    def clear(self):
        super(TvdbFanartProvider, self).clear()        
        shutil.rmtree(self.tvdbCacheDir, ignore_errors=True)
        os.makedirs(self.tvdbCacheDir)

    @synchronized
    def _queryTvDb(self, title):
        # serialize queries to tvdb since tvdb api seems to have concurrency issues
        return self.tvdb[title]['_banners']['poster']

# =============================================================================
class TheMovieDbFanartProvider(BaseFanartProvider):
    
    def __init__(self, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)        
        tmdb.config['apikey'] = '4956f64b34ac586d01d6820de8e93d58'
        self.mdb = tmdb.MovieDb()
    
    @chain
    def getPosters(self, program):
        posters = []
        if program.isMovie():
            try:
                results = self.mdb.search(program.title())
                if results and len(results) > 0:
                    filmId = results[0]['id']
                    film = self.mdb.getMovieInfo(filmId)
                    
                    for id in film['images']['poster']:
                        if 'mid' in film['images']['poster'][id]:
                        #for size in film['images']['poster'][id]:
                            size = 'mid'
                            url = film['images']['poster'][id][size]
                            #log.debug('TMDB: %s size = %s  url = %s' % (id, size, url))
                            posters.append(url)

                    #for i, result in enumerate(results):    
                        # Poster keys: 
                        #    'cover'      -- little small - 185px by 247px 
                        #    'mid'        -- just right   - 500px by 760px
                        #    'original'   -- can be huge  - 2690px by 3587px
                        #    'thumb'      -- tiny         - 92px by 136px
                        
                        #for key, value in result['poster'].items():
                        #    log.debug('TMDB: %d key = %s  value = %s' % (i, key, value))

                        #if  'mid' in result['poster']:
                        #    posters.append(result['poster']['mid'])
                else:
                    log.debug('TMDB found nothing for: %s' % program.title())
            except Exception, e:
                log.error('TMDB fanart search error: %s %s' % (program.title(), e))
        return posters

# =============================================================================
class GoogleImageSearchProvider(BaseFanartProvider):
    
    # safe search on, tall image preferred,   
    # 2 megapixel quality preferred = &imgsz=2MP
    # 
    URL = 'http://ajax.googleapis.com/ajax/services/search/images?v=1.0&safe=on&imgar=t' #&imgtype=photo 
    REFERRER = 'http://mythbox.googlecode.com' 
    
    def __init__(self, nextProvider=None):
        BaseFanartProvider.__init__(self, nextProvider)        
    
    @chain
    def getPosters(self, program):
        posters = []
        try:
            # TODO: Verify this is no longer an issue -- 
            #       GOOGLE fanart search:  K�nigreich der Himmel 'ascii' codec can't decode byte 0xc3 in position 1: ordinal not in range(128)
            searchUrl = '%s&q=%s' % (self.URL, urllib.quote("'%s'"% unicode(program.title()).encode('utf-8')))
            req = urllib2.Request(searchUrl)
            req.add_header('Referer', self.REFERRER)
            resp = urllib2.urlopen(req)
            s = resp.readlines()
            obj = json.loads(s[0])
            
            #if log.isEnabledFor('debug'):
            #    log.debug(json.dumps(obj, sort_keys=True, indent=4))
            #    log.debug('url = %s' % searchUrl)
            #    for result in obj['responseData']['results']: 
            #        log.debug(result['unescapedUrl'])            
            
            for i,result in enumerate(obj['responseData']['results']):
                #log.debug('%d googleresult = %s' % (i, result['unescapedUrl']))
                posters.append(result['unescapedUrl'])
                
        except Exception, e:
            log.error('GOOGLE fanart search:  %s %s' % (program.title(), str(e)))
        return posters
        
# =============================================================================
class FanArt(object):
    """One stop shop for fanart"""
    
    def __init__(self, platform, httpCache, settings):
        self.platform = platform
        self.httpCache = httpCache
        self.settings = settings
        self.provider = NoOpFanartProvider()
        self.configure(self.settings)
        self.settings.addListener(self)
        
    def getRandomPoster(self, program):
        """
        @type program: Program 
        @return: returns path to image suitable as a boxcover that is shaped taller 
                 than wide (portrait mode) with medium quality resolution
                 (not for thumbnails). 
        """
        return self.provider.getRandomPoster(program)
    
    def getPosters(self, program):
        return self.provider.getPosters(program)

    def hasPosters(self, program):
        return self.provider.hasPosters(program)
    
    def clear(self):
        self.provider.clear() 

    def configure(self, settings):
        self.provider.close()
        p = None
        if settings.getBoolean('fanart_google'): p = GoogleImageSearchProvider(p)
        if settings.getBoolean('fanart_imdb')  : p = OneStrikeAndYoureOutFanartProvider(self.platform, ImdbFanartProvider(), p)
        if settings.getBoolean('fanart_tmdb')  : p = OneStrikeAndYoureOutFanartProvider(self.platform, TheMovieDbFanartProvider(), p)        
        if settings.getBoolean('fanart_tvdb')  : p = OneStrikeAndYoureOutFanartProvider(self.platform, TvdbFanartProvider(self.platform), p)
                        
        p = CachingFanartProvider(self.httpCache, p)
        p = SuperFastFanartProvider(self.platform, p)
        p = SpamSkippingFanartProvider(p)
        self.provider = p
    
    def settingChanged(self, tag, old, new):
        if tag in ('fanart_tvdb', 'fanart_tmdb', 'fanart_imdb', 'fanart_google'):
            log.debug('Applying %s change to fanart provider' % tag)
            self.configure(self.settings)
