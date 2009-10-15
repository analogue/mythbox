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
import domain
import mythtv
import pool

from util import threadlocals
from decorator import decorator

ilog = logging.getLogger('mythtv.inject')   # dependency injection via decorators

# =============================================================================
@decorator
def inject_conn(func, *args, **kwargs):
    """
        Decorator to inject a thread-safe mythtv.Connection object into the context 
        of a method invocation.
        
        To use:
          1. Decorate method with @inject_conn
          2. Within method, use self.conn() to obtain a reference to the Connection.
    """
    self = args[0]
    connPool = pool.pools['connPool']
    
    # Create thread local storage if not already allocated
    import thread
    tlsKey = thread.get_ident()
    try:
        threadlocals[tlsKey]
        ilog.debug('threading.local() already allocated')
    except KeyError:
        import threading
        threadlocals[tlsKey] = threading.local()
        ilog.debug('Allocating threading.local() to thread %d'  % tlsKey)

    # Bolt-on getter method so client can access connection.
    def conn_accessor():
        return threadlocals[thread.get_ident()].conn
    self.conn = conn_accessor  

    # Only acquire resource once per thread
    try:
        if threadlocals[tlsKey].conn == None:
            raise AttributeError # force allocation
        alreadyAcquired = True; 
        ilog.debug('Skipping acquire resource')
    except AttributeError:
        alreadyAcquired = False
        ilog.debug('Going to acquire resource')

    try:
        if not alreadyAcquired:
            # store conn in thread local storage
            threadlocals[tlsKey].conn = connPool.checkout()
            ilog.debug('--> injected conn %s into %s' % (threadlocals[tlsKey].conn, threadlocals[tlsKey]))
            
        result = func(*args, **kwargs) 
    finally:
        if not alreadyAcquired:
            ilog.debug('--> removed conn %s from %s' % (threadlocals[tlsKey].conn, threadlocals[tlsKey]))
            connPool.checkin(threadlocals[tlsKey].conn)
            threadlocals[tlsKey].conn = None
    return result

# =============================================================================
@decorator
def inject_db(func, *args, **kwargs):
    """
        Decorator to inject a thread-safe MythDatabase object into the context 
        of a method invocation.
        
        To use:
          1. Decorate method with @inject_db
          2. Within method, use self.db() to obtain a reference to the database.
    """
    self = args[0]
    dbPool = pool.pools['dbPool']
    
    # Create thread local storage if not already allocated
    import thread
    tlsKey = thread.get_ident()
    try:
        threadlocals[tlsKey]
        ilog.debug('threading.local() already allocated')
    except KeyError:
        import threading
        threadlocals[tlsKey] = threading.local()
        ilog.debug('Allocating threading.local() to thread %d'  % tlsKey)
                    
#    try:
#        self.db
#        if self.db == None:
#            raise AttributeError # force allocation
#        ilog.debug('db accessor already bolted on')
#    except AttributeError:
#        ilog.debug('bolting on db accessor')
#        def db_accessor():
#            return threadlocals[thread.get_ident()].db 
#        self.db = db_accessor  

    # Bolt-on getter method so client can access db.
    def db_accessor():
        return threadlocals[thread.get_ident()].db 
    self.db = db_accessor  

    # Only acquire resource once per thread
    try:
        if threadlocals[tlsKey].db == None:
            raise AttributeError # force allocation
        alreadyAcquired = True; 
        ilog.debug('Skipping acquire resource')
    except AttributeError:
        alreadyAcquired = False
        ilog.debug('Going to acquire resource')

    try:
        if not alreadyAcquired:
            # store db in thread local storage
            threadlocals[tlsKey].db = dbPool.checkout()
            ilog.debug('--> injected db %s into %s' % (threadlocals[tlsKey].db, threadlocals[tlsKey]))
            
        result = func(*args, **kwargs) 
    finally:
        if not alreadyAcquired:
            ilog.debug('--> removed db %s from %s' % (threadlocals[tlsKey].db, threadlocals[tlsKey]))
            dbPool.checkin(threadlocals[tlsKey].db)
            threadlocals[tlsKey].db = None
    return result

## =============================================================================
#@decorator
#def inject_foo(func, *args, **kwargs):
#
#    self = args[0]
#    connPool = pool.pools['connPool']
#    return inject_dependency(self, connPool)
#
## =============================================================================
#def inject_dependency(clazz, pool, name):
#    # Create thread local storage if not already allocated
#    import thread
#    tlsKey = thread.get_ident()
#    try:
#        threadlocals[tlsKey]
#        ilog.debug('threading.local() already allocated')
#    except KeyError:
#        import threading
#        threadlocals[tlsKey] = threading.local()
#        ilog.debug('Allocating threading.local() to thread %d'  % tlsKey)
#
#    # Bolt-on getter method so client can access connection.
#    def accessor():
#        tls = threadlocals[thread.get_ident()]
#        return tls.__getattribute__(name)
#    
#    clazz.__setattr__(name, accessor)  
#
#    # Only acquire resource once per thread
#    try:
#        if threadlocals[tlsKey].conn == None:
#            raise AttributeError # force allocation
#        alreadyAcquired = True; 
#        ilog.debug('Skipping acquire resource')
#    except AttributeError:
#        alreadyAcquired = False
#        ilog.debug('Going to acquire resource')
#
#    try:
#        if not alreadyAcquired:
#            # store conn in thread local storage
#            threadlocals[tlsKey].conn = connPool.checkout()
#            ilog.debug('--> injected conn %s into %s' % (threadlocals[tlsKey].conn, threadlocals[tlsKey]))
#            
#        result = func(*args, **kwargs) 
#    finally:
#        if not alreadyAcquired:
#            ilog.debug('--> removed conn %s from %s' % (threadlocals[tlsKey].conn, threadlocals[tlsKey]))
#            connPool.checkin(threadlocals[tlsKey].conn)
#            threadlocals[tlsKey].conn = None
#    return result

# =============================================================================
class ConnectionFactory(pool.PoolableFactory):
    
    def __init__(self, *args, **kwargs):
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
        self.platform = kwargs['platform']
    
    def create(self):
        conn = InjectedConnection(self.settings, self.translator, self.platform)
        return conn
    
    def destroy(self, conn):
        conn.close()
        del conn

# =============================================================================
class InjectedConnection(mythtv.Connection):

    def __init__(self, settings, translator, platform):
        mythtv.Connection.__init__(self, settings=settings, db=None, translator=translator, platform=platform)

    @inject_db
    def getChannels(self):
        return super(InjectedConnection, self).getChannels()

    @inject_db
    def getTuners(self):
        return super(InjectedConnection, self).getTuners()

    @inject_db
    def getTunerShowing(self, showName):
        return super(InjectedConnection, self).getTunerShowing(self, showName)
    
    @inject_db
    def getTunerStatus(self, tuner):
        return super(InjectedConnection, self).getTunerStatus(tuner)
    
    @inject_db
    def getMythFillStatus(self):
        return super(InjectedConnection, self).getMythFillStatus()

    @inject_db    
    def saveSchedule(self, schedule):
        return super(InjectedConnection, self).saveSchedule(schedule)

    @inject_db  
    def deleteSchedule(self, schedule):
        return super(InjectedConnection, self).deleteSchedule(schedule)

# =============================================================================
class InjectedRecordedProgram(domain.RecordedProgram):

    def __init__(self, data, settings, translator, platform):
        domain.RecordedProgram.__init__(self, data=data, conn=None, settings=settings, translator=translator, platform=platform)

    @inject_conn
    def getCommercials(self):
        return super(InjectedRecordedProgram, self).getCommercials()

    @inject_conn
    def setBookmark(self, seconds):
        super(InjectedRecordedProgram, self).setBookmark(seconds)

    @inject_conn
    def getBookmark(self):
        return super(InjectedRecordedProgram, self).getBookmark()
        
# =============================================================================
class InjectedJob(domain.Job):

    def __init__(self, id, channelId, startTime, insertTime, 
                 jobType, cmds, flags, jobStatus, statusTime,
                 hostname, comment, scheduledRunTime, translator):
        domain.Job.__init__(self, None, None, id, channelId, startTime, insertTime, 
                 jobType, cmds, flags, jobStatus, statusTime,
                 hostname, comment, scheduledRunTime, translator)

    @inject_db
    def getPositionInQueue(self):
        return super(InjectedJob, self).getPositionInQueue()
    
    @inject_db
    def moveToFrontOfQueue(self):
        super(InjectedJob, self).moveToFrontOfQueue()
    
    @inject_conn
    def getProgram(self):
        return super(InjectedJob, self).getProgram()
        
# =============================================================================
class InjectedTuner(domain.Tuner):

    def __init__(self, tunerId, hostname, signalTimeout, channelTimeout, tunerType = ''):
        domain.Tuner.__init__(self, tunerId, hostname, signalTimeout, channelTimeout, tunerType, conn=None)

    @inject_conn
    def isWatchingOrRecording(self, showName):
        return super(InjectedTuner, self).isWatchingOrRecording(showName)

    @inject_conn
    def isRecording(self):
        return super(InjectedTuner, self).isRecording()

    @inject_conn
    def getRecordingBytesWritten(self):
        return super(InjectedTuner, self).getRecordingBytesWritten()

    @inject_conn
    def getWhatsPlaying(self):
        return super(InjectedTuner, self).getWhatsPlaying()

    @inject_conn
    def getChannels(self):
        return super(InjectedTuner, self).getChannels()

    @inject_conn
    def startLiveTV(self, channelNumber):
        super(InjectedTuner, self).startLiveTV(channelNumber)

    @inject_conn
    def stopLiveTV(self):
        super(InjectedTuner, self).stopLiveTV()

    @inject_conn
    def getLiveTVStatus(self):
        return super(InjectedTuner, self).getLiveTVStatus()
    
    @inject_conn  
    def getTunerStatus(self):
        return super(InjectedTuner, self).getTunerStatus()

    @inject_conn
    def formattedTunerStatus(self):
        return super(InjectedTuner, self).formattedTunerStatus()
    
# =============================================================================    
class InjectedMythThumbnailResolver(mythtv.MythThumbnailResolver):
    
    def __init__(self):
        mythtv.MythThumbnailResolver.__init__(self, conn=None)
    
    @inject_conn
    def store(self, program, dest):
        return super(InjectedMythThumbnailResolver, self).store(program, dest)
    
# =============================================================================    
class InjectedMythChannelIconResolver(mythtv.MythChannelIconResolver):
    
    def __init__(self):
        mythtv.MythChannelIconResolver.__init__(self, conn=None)
    
    @inject_conn
    def store(self, channel, dest):
        return super(InjectedMythChannelIconResolver, self).store(channel, dest)    