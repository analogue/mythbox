#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
#  Copyright (C) 2005 Tom Warkentin <tom@ixionstudios.com>
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
import ConfigParser
import logging
import os
import mythbox
import Queue
import re
import socket
import sre
import string
import sys
import time
import xbmc
import xbmcgui

from decorator import decorator

log = logging.getLogger('mythtv.core')
plog = logging.getLogger('mythtv.perf')
elog = logging.getLogger('mythbox.event')

# =============================================================================
global __gFileLocations  # TODO: Delete and refactor
__gFileLocations = {}    # TODO: Delete and refactor

# Globally available per thread local storage used by 
# @inject_conn and @inject_db decorators
threadlocals = {}   


# =============================================================================
class ProtocolException(Exception):
    """
    Thrown on protcol version mismatch between frontend and backend or
    general protocol related errors.
    """ 
    pass

class ClientException(Exception): 
    """TODO: When thrown?"""
    pass

class ServerException(Exception): 
    """
    TODO: When thrown?
    TODO: Rename to MythException
    """
    pass

class SettingsException(Exception):
    """Thrown when a setting fails validation in MythSettings""" 
    pass

class StatusException(Exception): 
    pass

# =============================================================================
def formatSize(sizeKB, gb=False):
    size = float(sizeKB)
    if size > 1024*1000 and gb:
        value = str("%.2f %s"% (size/(1024.0*1000.0), "GB"))
    elif size > 1024:
        value = str("%.2f %s"% (size/(1024.0), 'MB')) 
    else:
        value = str("%.2f %s"% (size, 'KB')) 
    return re.sub(r'(?<=\d)(?=(\d\d\d)+\.)', ',', value)
    
def decodeLongLong(low32Bits, high32Bits):
    """
    @type low32Bits: int or str
    @type high32Bits: int or str
    @return: Decodes two 32bit ints to a 64bit long
    @rtype: long
    """
    if isinstance(low32Bits, str): 
        low32Bits = long(low32Bits)
    if isinstance(high32Bits, str): 
        high32Bits = long(high32Bits)
    return low32Bits & 0xffffffffL | (high32Bits << 32)

def encodeLongLong(long64Bits):
    """
    @rtype: (low32Bits, high32Bits)
    @return: Encodes 64bit long into pair of 32 bit ints
    """
    return long64Bits & 0xffffffffL, long64Bits >> 32

def frames2seconds(frames, fps):
    """
    Converts a number of frames (long) to number of seconds (float w/ 2 decimal precision) 
    with given fps (float) 
    """
    return float('%.2f'%(float(long(frames) / float(fps))))

def seconds2frames(seconds, fps):
    """
    Converts number of seconds (float) to number of frames (long) with fiven fps (float)
    """  
    return long(float(seconds) * float(fps))

# =============================================================================
def formatSeconds(secs):
    """
    Returns number of seconds into a nicely formatted string --> 00h 00m 00s
    The hours and minutes are left off if zero 
    """
    assert secs >= 0, 'Seconds must be > 0'
    time_t  = time.gmtime(secs)
    hours   = time_t[3]  # tm_hour
    mins    = time_t[4]  # tm_min 
    seconds = time_t[5]  # tm_sec
    result  = ""
    
    if hours > 0:
        result += "%sh" % hours
        if mins > 0 or seconds > 0:
            result += " "
            
    if mins > 0:
        result += "%sm" % mins
        if seconds > 0:
            result += " "
            
    if (len(result) == 0) or (len(result) > 0 and seconds > 0):
        result += "%ss"%seconds
        
    return result

# =============================================================================
def slice(items, num):
    """
    Slices a list of items into the given number of separate lists
    @param items: list of items to split
    @param num: number of lists to split into
    @return: list of lists
    @example: [1,2,3,4,5,6,7,8] with num=3 returns [[1,4,7], [2,5,8], [3,6]]
    """
    queues = []
    for i in range(num):
        queues.append([])
    for i, item in enumerate(items):
        queues[i%num].append(item)
    return queues

# =============================================================================
class BoundedEvictingQueue(object):
    """
    Fixed size queue that evicts objects in FIFO order when capacity
    has been reached. 
    """

    def __init__(self, size):
        self._queue = Queue.Queue(size)
        
    def empty(self):
        return self._queue.empty()
    
    def qsize(self):
        return self._queue.qsize()
    
    def full(self):
        return self._queue.full()
    
    def put(self, item):
        if self._queue.full():
            self._queue.get()
        self._queue.put(item, False, None)
        
    def get(self):
        return self._queue.get(False, None)

# =============================================================================

_lircEvents = BoundedEvictingQueue(2)

@decorator
def lirc_hack(func, *args, **kwargs):
    """
    With XBMC's integration with lirc on Linux, a single button press on the 
    remote control sometimes generates two successive button presses instead.
    For example, exiting a screen can accidentally exit the entire application.
    This issues has been logged in XBMC's TRAC, but marked as a WON'T FIX.  
    Whaddya gonna do?
    
    This hack is a workaround to consume the second button press if
    - the difference in time between the two button presses is relatively close. 
    - the buttons generating the events are those most likely to cause problems
      - PREVIOUS_MENU
      - PREVIOUS_ACTION
      - ENTER
    """
    win = args[0]   # decorator always applies to a method on a Window
    debug = elog.isEnabledFor(logging.DEBUG)
    #if debug: elog.debug('lirc hack: Entered lirc_hack decorator - num events = %d @ %s' % (_lircEvents.qsize(), _lircEvents))
    
    def getKey(*args):
        action = args[1]
        if type(action) == int:
            return action
        else:
            return action.getId()
        
    def interested(func, *args, **kwargs):
        """
        @return: True if this is a button press that causes problems if repeated
        """
        if debug:
            elog.debug('lirc hack: Function name = %s' % func.__name__)
            elog.debug('lirc hack: num args = %d' % len(args))
            for i, arg in enumerate(args):
                elog.debug(' lirc hack:   arg[%d] = %s' % (i, type(arg)))

        if func.__name__ in ('onAction', 'onActionHook') :
            action = args[1]
            #log.debug('actionId = %s' % action.getId())
            import ui
            if action.getId() in (ui.ACTION_PREVIOUS_MENU, ui.ACTION_PARENT_DIR, ui.ACTION_SELECT_ITEM):
                return True
        elif func.__name__ == 'onClick':
            return True
        else:
            elog.warn('lirc hack: interested func name %s not valid' % func.__name__)
            return False
        
    # Hack only applies to linux
    if not win.platform.isUnix():
        return func(*args, **kwargs)

    # Lirc hack setting must be turned on via settings screen
    if not win.settings.getBoolean('lirc_hack'):
        return func(*args, **kwargs)
    
    # Filter out only events we're interested in 
    if not interested(func, *args, **kwargs):
        if debug:
            elog.debug('lirc hack: not interested')
        return func(*args, **kwargs)
    
    global _lircEvents
    _lircEvents.put({'func': func.__name__, 'action': getKey(*args), 'time' : time.time()})
        
    # Hack requires at least two events
    if not _lircEvents.full():
        return func(*args, **kwargs)
    
    # TODO: Don't save all events
    t1 = _lircEvents.get()
    t2 = _lircEvents.get()
    
    if t1['action'] != t2['action']:
        _lircEvents.put(t2)
        if debug: elog.debug('lirc hack: not same action %s %s' % (t1['action'], t2['action']))
        return func(*args, **kwargs)
    elif t1['func'] in ('onClick') and t2['func'] in ('onAction', 'onActionHook'):
        if debug: elog.debug('lirc hack: not same action but click/action combo')
    else:
        if debug: elog.debug('lirc hack: same action %s %s' % (t1['action'], t2['action']))
         
    diff = t2['time'] - t1['time']
    if debug: elog.debug('lirchack diff: %s' % diff)
    eatButtonPress = (diff < 1.0)
    
    if not eatButtonPress:
        _lircEvents.put(t2)
        if debug: elog.debug('lirc hack: not eating event %s ' % t2['action'])
        return func(*args, **kwargs)
    else:
        log.debug('\n\n\n\t\tlirc hack consumed event with delta = %s\n\n' % diff)
        return None

# =============================================================================
@decorator
def run_async(func, *args, **kwargs):
    """
        run_async(func)
            function decorator, intended to make "func" run in a separate
            thread (asynchronously).
            Returns the created Thread object

            E.g.:
            @run_async
            def task1():
                do_something

            @run_async
            def task2():
                do_something_too

            t1 = task1()
            t2 = task2()
            ...
            t1.join()
            t2.join()
    """
    from threading import Thread
    #from functools import wraps

    #@wraps(func)
    #def async_func(*args, **kwargs):
    func_hl = Thread(target = func, args = args, kwargs = kwargs)
    func_hl.start()
    return func_hl

    #return async_func

# =============================================================================
@decorator
def timed(func, *args, **kw):
    """
    Decorator for logging method execution times. 
    Make sure 'mythtv.perf' logger in is set to WARN or lower. 
    """
    if plog.isEnabledFor(logging.DEBUG):
        t1 = time.time()
        result = func(*args, **kw)
        t2 = time.time()
        diff = t2 - t1
        if diff > 0.5:
            plog.warning("TIMER: %s took %2.2f seconds" % (func.__name__, diff))
        elif diff > 0.1:
            plog.debug("TIMER: %s took %2.2f seconds" % (func.__name__, diff))
        return result
    else:
        return func(*args, **kw)

# =============================================================================
@decorator
def ui_locked(func, *args, **kw):
    """
    Decorator for setting/unsetting the xbmcgui lock on method
    entry and exit.
    
    @todo: make re-entrant 
    """
    try:
        xbmcgui.lock()
        result = func(*args, **kw)
    finally:
        xbmcgui.unlock()
    return result

# =============================================================================
@decorator
def catchall(func, *args, **kw):
    """
    Decorator for catching and logging exceptions on methods which
    can't safely propagate exceptions to the caller
    """
    try:
        return func(*args, **kw)
    except Exception, ex:
        log.exception('CATCHALL: Caught exception %s on method %s' % (str(ex), func))

# =============================================================================
@decorator
def catchall_ui(func, *args, **kw):
    """
    Decorator for catching, logging, and displaying exceptions on methods which
    can't safely propagate exceptions to the caller (on* callback methods from xbmc)
    """
    try:
        return func(*args, **kw)
    except Exception, ex:
        log.exception('CATCHALL_UI: Caught exception %s on method %s' % (str(ex), func))
        xbmcgui.Dialog().ok('Error: CATCHALL', 'Exception: %s' % str(ex), 'Function: %s' % str(func))

# =============================================================================
def synchronized(func):
    """
    Method synchronization decorator.
    """
    def wrapper(self,*__args,**__kw):
        try:
            rlock = self._sync_lock
        except AttributeError:
            from threading import RLock
            rlock = self.__dict__.setdefault('_sync_lock',RLock())
        rlock.acquire()
        try:
            return func(self,*__args,**__kw)
        finally:
            rlock.release()
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

# =============================================================================
def which(program, all=False):
    """emulates unix' "which" command (with one argument only)"""
    
    def is_exe(exe):
        return os.path.exists(exe) and os.access(exe, os.X_OK)

    def full_exes(program):
        for path in os.environ['PATH'].split(os.pathsep):
            log.debug('Checking PATH %s for %s' %(path, program))
            exe = os.path.join(path, program)
            if is_exe(exe):
                yield exe

    ppath, pname = os.path.split(program)
    if ppath:
        if is_exe(program):
            return program
    else:
        paths = full_exes(program)
        if not all:
            try:
                return paths.next()
            except StopIteration:
                return None
        else:
            return list(paths)
    return None

# =============================================================================
def findMediaFile(filename):
    """
    @deprecated: Use WindowXML
    """
    retPath = None
    if filename in __gFileLocations:
        retPath = __gFileLocations[filename];
    else:
        skinDir = getSkinDir()
        filePath = skinDir + "media" + os.sep + filename
        if os.path.exists( filePath ):
            retPath = filePath

        if not retPath:
            filePath = os.getcwd() + os.sep + "skin" + os.sep + \
                "shared" + os.sep + "media" + os.sep + filename
            if os.path.exists( filePath ):
                retPath = filePath

        if retPath:
            globals()['__gFileLocations'][filename] = retPath
    #log.debug("findMediaFile(%s) => %s"%(filename, retPath))
    return retPath

# =============================================================================
def findSkinFile( filename, width, height ):
    """
    Function to find the appropriate skin file based on screen resolution.

    Resolution              Directories checked under $SCRIPTHOME/skin/shared
    ======================= =================================================
    1920x1080               1080i, 720p, ntsc16x9, pal16x9, ntsc, pal, shared
    1280x720                720p, ntsc16x9, pal16x9, ntsc, pal, shared
    720x480                 ntsc, pal, shared
    otherwise               pal, ntsc, shared

    @deprecated: Use WindowXML
    """

    # figure out which directories to check
    retDir = None
    if filename in __gFileLocations:
        retDir = __gFileLocations[filename]
    else:
        dirsToCheck = []
        if width == 1920 and height == 1080:
            dirsToCheck = ['1080i', '720p', 'ntsc16x9', 'pal16x9', 'ntsc', 'pal']
        elif width == 1280 and height == 720:
            dirsToCheck = ['720p', 'ntsc16x9', 'pal16x9', 'ntsc', 'pal']
        elif width == 720 and height == 480:
            dirsToCheck = ['ntsc16x9','pal16x9','ntsc', 'pal']
        #elif width == 720 and height == 576:
        else:
            dirsToCheck = ['pal', 'ntsc']

        mainSkinDir = getSkinDir()
        sharedSkinDir = os.getcwd() + os.sep + "skin" + os.sep + "shared" + os.sep

        if mainSkinDir == sharedSkinDir:
            doShared = False
        else:
            doShared = True
            
        # check directories until the file is found once
        # first check 'custom' skins, then 'shared'
        #log.debug("Checking %s exists" % mainSkinDir)
        
        if os.path.exists( mainSkinDir ):
            
            for dir in dirsToCheck:
                skinDir = mainSkinDir + dir + os.sep + filename
                
                log.debug("skinDir = %s"%skinDir )
                if os.path.exists( skinDir ):
                    retDir = skinDir
                    break
            
        if not retDir and doShared:
            # have moved all 'shared' skins into similar directory structure
            # so search those directories too
            for dir in dirsToCheck:
                skinDir = sharedSkinDir + dir + os.sep + filename
                #log.debug("skinDir = %s"%skinDir )
                if os.path.exists( skinDir ):
                    retDir = skinDir
                    break
        
        if retDir:
            globals()['__gFileLocations'][filename] = retDir
        else:
            raise Exception, "Unable to find skin file '%s' in subdirs of '%s'."%(filename, getSkinDir())
    
    #log.debug('findSkinFile(%s, %d, %d) => %s'%(filename, width, height, retDir))
    return retDir

# =============================================================================
def loadFile(fileName, width, height):
    """ 
    Loads skin xml file and resolves embedded #include directives.
    Returns completely loaded file as a string. 

    @deprecated: Use WindowXML
    """
        
    #log.debug("loadFile(%s, %d, %d)"%(fileName, width, height ) )
    s = ""
    f = file( fileName )
    for l in f.readlines():
        # log.debug(fileName + ":" + l) 
        m = sre.match( '^#include (.*)$', l )
        if m:
            incFile = m.group(1)
            incFile = incFile.strip()
            if sre.match( '^\w+\.xml$', incFile ):
                # need to find skin file
                incFile = findSkinFile( incFile, width, height )
            elif sre.match( '\%SKINDIR\%', incFile ):
                incFile = string.replace(incFile, "%SKINDIR%", getSkinDir())
            else:
                # convert path separators to proper path separator - just in case
                incFile = string.replace( incFile, "/", os.sep )
                incFile = string.replace( incFile, "\\", os.sep )

                # assume relative path provided
                path = os.path.dirname( fileName )
                path += os.sep + incFile
                incFile = path
            s += loadFile( incFile, width, height )
        else:
            s += l
    f.close()
    return s

# =============================================================================
def loadSkin(skinName, width, height):
    """
    Function to load the specified skin for the specified resolution.  When a
    file is loaded, it is checked for include statements.  An attempt is made
    to resolve all includes until no more includes are left.

    On success, the function returns a string containing the skin XML with all
    include statements resolved.

    On failure, the function returns None.

    @deprecated: Use WindowXML
    """
    fileName = findSkinFile(skinName, width, height)
    skinXml = loadFile(fileName, width, height)
    return skinXml
    
# =============================================================================
def getSkinDir():
    """
    Function to return the path to the skin directory.  This will return
    something like:

    ./skin/Project Mayhem/

    Note: This is different than what xbmc.getSkinDir() returns.

    @deprecated: Use WindowXML
    """
    global skinDir # TODO: Why global?
    skinDir = os.getcwd() + os.sep + "skin" + os.sep + string.lower(xbmc.getSkinDir()) + os.sep
    try:
        s = os.stat(skinDir)
    except OSError:
        nextSkinDir = os.getcwd() + os.sep + "skin" + os.sep + "shared" + os.sep
        #log.warn("MythBox Skin Directory %s NOT found - Using default skindir %s" %(skinDir, nextSkinDir))
        try:
            s = os.stat(nextSkinDir)
        except OSError:
            raise Exception, "Default skindir fallback failed - %s." % nextSkinDir
    return skinDir

# =============================================================================
def initialize():
    """
    Initialize utility module.  Should be called on startup before calling any
    other methods.
    
    @todo: Remove me
    """
    socket.setdefaulttimeout(60)
    globals()["__gFileLocations"] = {}
    log.info(" ============ MythBox Started ================")

# =============================================================================
class NativeTranslator(xbmc.Language):
    
    def __init__(self, scriptPath, defaultLanguage=None, *args, **kwargs):
        xbmc.Language.__init__(self, scriptPath, defaultLanguage, *args, **kwargs)
        
    def get(self, id):
        """
        Alias for getLocalizedString(...)

        @param id: translation id
        @type id: int
        @return: translated text
        @rtype; string
        """
        # if id is a string, assume no need to lookup translation
        if type(id) is str:
            return id
        else:
            return self.getLocalizedString(id)
    
    def toList(self, someMap):
        """
        @param someMap: dict with translation ids as values. Keys are ignored
        @return: list of strings containing translations
        """
        result = []
        for key in someMap.keys():
            result.append(self.get(someMap[key]))
        return result
    
# =============================================================================
class OnDemandConfig(object):
    """
    Used by unit tests to query user for values on stdin as they
    are needed (passwords, for example) . Once entered, the value is saved
    to a config file so future invocations can run unattended.  
    """ 
    
    def __init__(self, filename='ondemandconfig.ini', section='default'):
        self.filename = filename
        self.section = section
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.filename)
    
    def get(self, key):
        if not self.config.has_section(self.section):
            self.config.add_section(self.section)
        
        if self.config.has_option(self.section, key):
            value = self.config.get(self.section, key)
        else:
            print "\n==============================="
            print "Enter a value for key %s:" % key
            value = sys.stdin.readline()
            print "Value is stored in %s if you would like to change it later." % self.filename
            print "===============================\n"
            
            value = str(value).strip() # nuke newline
            self.config.set(self.section, key, value)
            inifile = file(self.filename, "w")
            self.config.write(inifile)
            inifile.close()
        return value

