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

ilog = logging.getLogger('mythtv.inject')   # dependency injection via decorators


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
