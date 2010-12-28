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
import os
import sys
import traceback
import xbmc
import xbmcgui

from mythbox.bus import EventBus

import inspect

try:
    set
except NameError:
    from sets import Set as set

def getinfo(func):
    """
    Returns an info dictionary containing:
    - name (the name of the function : str)
    - argnames (the names of the arguments : list)
    - defaults (the values of the default arguments : tuple)
    - signature (the signature : str)
    - doc (the docstring : str)
    - module (the module name : str)
    - dict (the function __dict__ : str)
    
    >>> def f(self, x=1, y=2, *args, **kw): pass

    >>> info = getinfo(f)

    >>> info["name"]
    'f'
    >>> info["argnames"]
    ['self', 'x', 'y', 'args', 'kw']
    
    >>> info["defaults"]
    (1, 2)

    >>> info["signature"]
    'self, x, y, *args, **kw'
    """
    assert inspect.ismethod(func) or inspect.isfunction(func)
    regargs, varargs, varkwargs, defaults = inspect.getargspec(func)
    argnames = list(regargs)
    if varargs:
        argnames.append(varargs)
    if varkwargs:
        argnames.append(varkwargs)
    signature = inspect.formatargspec(regargs, varargs, varkwargs, defaults,
                                      formatvalue=lambda value: "")[1:-1]
    return dict(name=func.__name__, argnames=argnames, signature=signature,
                defaults = func.func_defaults, doc=func.__doc__,
                module=func.__module__, dict=func.__dict__,
                globals=func.func_globals, closure=func.func_closure)

# akin to functools.update_wrapper
def update_wrapper(wrapper, model, infodict=None):
    infodict = infodict or getinfo(model)
    try:
        wrapper.__name__ = infodict['name']
    except: # Python version < 2.4
        pass
    wrapper.__doc__ = infodict['doc']
    wrapper.__module__ = infodict['module']
    wrapper.__dict__.update(infodict['dict'])
    wrapper.func_defaults = infodict['defaults']
    wrapper.undecorated = model
    return wrapper

def new_wrapper(wrapper, model):
    """
    An improvement over functools.update_wrapper. The wrapper is a generic
    callable object. It works by generating a copy of the wrapper with the 
    right signature and by updating the copy, not the original.
    Moreovoer, 'model' can be a dictionary with keys 'name', 'doc', 'module',
    'dict', 'defaults'.
    """
    if isinstance(model, dict):
        infodict = model
    else: # assume model is a function
        infodict = getinfo(model)
    assert not '_wrapper_' in infodict["argnames"], (
        '"_wrapper_" is a reserved argument name!')
    src = "lambda %(signature)s: _wrapper_(%(signature)s)" % infodict
    funcopy = eval(src, dict(_wrapper_=wrapper))
    return update_wrapper(funcopy, model, infodict)

# helper used in decorator_factory
def __call__(self, func):
    infodict = getinfo(func)
    for name in ('_func_', '_self_'):
        assert not name in infodict["argnames"], (
           '%s is a reserved argument name!' % name)
    src = "lambda %(signature)s: _self_.call(_func_, %(signature)s)"
    new = eval(src % infodict, dict(_func_=func, _self_=self))
    return update_wrapper(new, func, infodict)

def decorator_factory(cls):
    """
    Take a class with a ``.caller`` method and return a callable decorator
    object. It works by adding a suitable __call__ method to the class;
    it raises a TypeError if the class already has a nontrivial __call__
    method.
    """
    attrs = set(dir(cls))
    if '__call__' in attrs:
        raise TypeError('You cannot decorate a class with a nontrivial '
                        '__call__ method')
    if 'call' not in attrs:
        raise TypeError('You cannot decorate a class without a '
                        '.call method')
    cls.__call__ = __call__
    return cls

def decorator(caller):
    """
    General purpose decorator factory: takes a caller function as
    input and returns a decorator with the same attributes.
    A caller function is any function like this::

     def caller(func, *args, **kw):
         # do something
         return func(*args, **kw)
    
    Here is an example of usage:

    >>> @decorator
    ... def chatty(f, *args, **kw):
    ...     print "Calling %r" % f.__name__
    ...     return f(*args, **kw)

    >>> chatty.__name__
    'chatty'
    
    >>> @chatty
    ... def f(): pass
    ...
    >>> f()
    Calling 'f'

    decorator can also take in input a class with a .caller method; in this
    case it converts the class into a factory of callable decorator objects.
    See the documentation for an example.
    """
    if inspect.isclass(caller):
        return decorator_factory(caller)
    def _decorator(func): # the real meat is here
        infodict = getinfo(func)
        argnames = infodict['argnames']
        assert not ('_call_' in argnames or '_func_' in argnames), (
            'You cannot use _call_ or _func_ as argument names!')
        src = "lambda %(signature)s: _call_(_func_, %(signature)s)" % infodict
        # import sys; print >> sys.stderr, src # for debugging purposes
        dec_func = eval(src, dict(_func_=func, _call_=caller))
        return update_wrapper(dec_func, func, infodict)
    return update_wrapper(_decorator, caller)


@decorator
def timed2(func, *args, **kw):
    import time
    t1 = time.time()
    result = func(*args, **kw)
    t2 = time.time()
    print("TIMER: %s took %2.2f seconds" % (func.__name__, t2 - t1))
    return result


class BootStrapper(object):
    
    def __init__(self, splash):
        self.log = None
        self.platform = None
        self.stage = 'Initializing'
        self.shell = None
        self.splash = splash
        self.failSilent = False
        
    def run(self):
        try:
            try:
                self.bootstrapLogger()
                self.bootstrapPlatform()
                self.bootstrapEventBus()            
                self.bootstrapCaches()
                self.bootstrapSettings()
                self.bootstrapUpdater()
                self.bootstrapFeeds()
                #self.bootstrapDebugShell()
                self.bootstrapHomeScreen()
            except Exception, ex:
                if not self.failSilent:
                    self.handleFailure(ex)
        finally:
            self.splash.close()
            
    def handleFailure(self, cause):
        msg = 'MythBox:%s - Error: %s' % (self.stage, cause)
        xbmc.log(msg)
        print traceback.print_exc()
        if self.log:
            self.log.exception(str(cause))
        xbmcgui.Dialog().ok('MythBox Error', 'Stage: %s' % self.stage, 'Exception: %s' % str(cause))
        
    def updateProgress(self, msg):
        self.log.info(msg)

    @timed2
    def bootstrapLogger(self):
        import logging
        import logging.config
        self.stage = 'Initializing Logger'
        
        # TODO: Remove os.getcwd() when platform is initialized before logging
        if 'win32' in sys.platform:
            loggerIniFile = os.path.join(os.getcwd(), 'mythbox_win32_log.ini')
        elif 'darwin' in sys.platform:
            import StringIO, re
            loggerIniFile = os.path.join(os.getcwd(), 'mythbox_log.ini')
            logconfig = open(loggerIniFile, 'r').read()
            loggerIniFile = StringIO.StringIO(re.sub('mythbox\.log', os.path.expanduser(os.path.join('~', 'Library', 'Logs', 'mythbox.log')) , logconfig, 1))
        else:
            loggerIniFile = os.path.join(os.getcwd(), 'mythbox_log.ini')

        xbmc.log('MythBox: loggerIniFile = %s' % loggerIniFile)
        logging.config.fileConfig(loggerIniFile)
        self.log = logging.getLogger('mythbox.core')
        self.log.info('Mythbox Logger Initialized')

    @timed2
    def bootstrapPlatform(self):
        self.stage = 'Initializing Platform'
        import mythbox.platform
        self.platform = mythbox.platform.getPlatform()
        self.platform.addLibsToSysPath()
        sys.setcheckinterval(0)
        cacheDir = self.platform.getCacheDir()
        from mythbox.util import requireDir
        requireDir(cacheDir)
        
        try:
            self.platform.getFFMpegPath(prompt=True)
        except Exception, e:
            self.failSilent = True
            raise e
        
        self.log.info('Mythbox Platform Initialized')

    @timed2
    def bootstrapEventBus(self):
        self.bus = EventBus()

    @timed2
    def bootstrapCaches(self):
        self.stage = 'Initializing Caches'
        
        from mythbox.util import NativeTranslator
        from mythbox.filecache import FileCache, HttpResolver, MythThumbnailFileCache
        from mythbox.mythtv.resolver import MythChannelIconResolver, MythThumbnailResolver 
        from os.path import join
        
        cacheDir = self.platform.getCacheDir()
        self.translator = NativeTranslator(self.platform.getScriptDir())
        self.mythThumbnailCache = MythThumbnailFileCache(join(cacheDir, 'thumbnail'), MythThumbnailResolver(), self.bus)
        self.mythChannelIconCache = FileCache(join(cacheDir, 'channel'), MythChannelIconResolver())
        self.httpCache = FileCache(join(cacheDir, 'http'), HttpResolver())

        self.cachesByName = {
            'mythThumbnailCache'  : self.mythThumbnailCache, 
            'mythChannelIconCache': self.mythChannelIconCache, 
            'httpCache'           : self.httpCache
        }

    @timed2
    def bootstrapSettings(self):
        
        @timed2
        def bss1():
            self.stage = 'Initializing Settings'
            from mythbox.settings import MythSettings
            self.settings = MythSettings(self.platform, self.translator, 'settings.xml', self.bus)

        @timed2
        def bss2():
            pass        
            #from fanart import FanArt
            #self.log.debug('Settings = \n %s' % self.settings)

        @timed2
        def bss3():
            
            class DelayedInstantiationProxy(object):
                '''Could use a little introspection to sort this out but eh...'''
                
                def __init__(self, *args, **kwargs):
                    self.args = args
                    self.kwargs = kwargs
                    self.fanArt = None
                    
                def requireDelegate(self):
                    if self.fanArt is None:
                        from fanart import FanArt
                        self.fanArt = FanArt(*self.args, **self.kwargs)
                
                def getSeasonAndEpisode(self, program):
                    self.requireDelegate()
                    return self.fanArt.getSeasonAndEpisode(program)
                
                def getRandomPoster(self, program):
                    self.requireDelegate()
                    return self.fanArt.getRandomPoster(program)
                
                def getPosters(self, program):
                    self.requireDelegate()
                    return self.fanArt.getPosters(program)
            
                def hasPosters(self, program):
                    self.requireDelegate()
                    return self.fanArt.hasPosters(program)
                
                def clear(self):
                    self.requireDelegate()
                    self.fanArt.clear() 
            
                def shutdown(self):
                    self.requireDelegate()
                    self.fanArt.shutdown()
                    
                def configure(self, settings):
                    self.requireDelegate()
                    self.fanArt.configure(settings)
                
                def onEvent(self, event):
                    self.requireDelegate()
                    self.fanArt.onEvent(event)
                        
            #from fanart import FanArt
            #self.fanArt = FanArt(self.platform, self.httpCache, self.settings, self.bus)
            self.fanArt = DelayedInstantiationProxy(self.platform, self.httpCache, self.settings, self.bus)
            
            import socket
            socket.setdefaulttimeout(20)
            self.bus.register(self)
            # Generate fake event to reflect value in settings.xml instead of mythbox_log.ini
            from bus import Event
            self.onEvent({'id': Event.SETTING_CHANGED, 'tag':'logging_enabled', 'old':'DontCare', 'new':self.settings.get('logging_enabled')})

        bss1()
        bss2()
        bss3()
        
        
    @timed2
    def bootstrapUpdater(self):
        self.stage = 'Initializing Updater'
        from mythbox.updater import UpdateChecker
        UpdateChecker(self.platform).isUpdateAvailable()

    @timed2
    def bootstrapFeeds(self):
        from mythbox.feeds import FeedHose
        self.feedHose = FeedHose(self.settings, self.bus)

    @timed2
    def bootstrapDebugShell(self):
        # only startup debug shell on my mythboxen
        import socket
        if socket.gethostname() in ('htpc2', 'faraday', 'zeus'):
            try:
                from mythbox.shell import DebugShell
                globals()['bootstrapper'] = self
                self.shell = DebugShell(self.bus, namespace=globals())
                self.shell.start()
            except:
                self.log.exception('Debug shell startup')

    @timed2
    def bootstrapHomeScreen(self):
        
        @timed2
        def bshs1():
            from mythbox.ui.home import HomeWindow
        
        @timed2
        def bshs2():
            from mythbox.ui.home import HomeWindow
            home = HomeWindow(
                'mythbox_home.xml', 
                os.getcwd(), 
                settings=self.settings, 
                translator=self.translator, 
                platform=self.platform, 
                fanArt=self.fanArt, 
                cachesByName=self.cachesByName,
                bus=self.bus,
                feedHose=self.feedHose)
            self.splash.close()
            return home
        
        bshs1()
        home = bshs2()    
        home.doModal()


    def onEvent(self, event):
        from bus import Event
        
        #
        # Apply changes to logger when user turns debug logging on/off
        #
        if event['id'] == Event.SETTING_CHANGED and event['tag'] == 'logging_enabled':
            import logging
            logging.root.debug('Setting changed: %s %s %s' % (event['tag'], event['old'], event['new']))

            if event['new'] == 'True': 
                level = logging.DEBUG
            else: 
                level = logging.WARN
                
            loggerNames = 'unittest mysql core method skin ui perf fanart settings cache event'.split() # wire inject'.split()
                
            for name in loggerNames:
                logger = logging.getLogger('mythbox.%s' %  name)
                logger.setLevel(level)

            # TODO: Adjust xbmc loglevel 
            #savedXbmcLogLevel = xbmc.executehttpapi("GetLogLevel").replace("<li>", "")
            #xbmc.executehttpapi('SetLogLevel(3)')
