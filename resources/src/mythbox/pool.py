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
import threading

from mythbox.util import sync_instance

log = logging.getLogger('mythbox.inject')

# Globally available resources pools
#    key   = name of pool
#    value = Pool instance
pools = {}
          
# =============================================================================
class PoolableFactory(object):
    """
    Any resource which is pooled needs a factory to create concrete instances.
    """
    def create(self):
        raise Exception, "Abstract method"
    
    def destroy(self, resource):
        raise Exception, "Abstract method"

# =============================================================================
class Pool(object):
    """
    Simple no frills unbounded resource pool
    """
    
    def __init__(self, factory):
        """
        @type factory: PoolableFactory
        """
        self.factory = factory
        self.isShutdown = False
        self.inn = []
        self.out = []
        self.lock = threading.RLock()

    @sync_instance
    def checkout(self):
        if self.isShutdown: raise Exception, 'Pool shutdown'
        if len(self.inn) == 0:
            log.debug('Creating resource %d' % (len(self.out)+1))
            resource = self.factory.create()
        else:
            resource = self.inn.pop()
        self.out.append(resource)
        return resource

    @sync_instance
    def checkin(self, resource):
        if self.isShutdown: raise Exception, 'Pool shutdown'
        self.inn.append(resource)
        self.out.remove(resource)
    
    @sync_instance
    def shutdown(self):
        for resource in self.inn:
            try:
                self.factory.destroy(resource)
            except:
                log.exception('Destroy pooled resource')
        if len(self.out) > 0:
            log.warn('%d pooled resources still out on shutdown' % len(self.out))
        self.isShutdown = True
    
    @sync_instance
    def size(self):
        return len(self.inn) + len(self.out)
    
    @sync_instance
    def available(self):
        return len(self.inn)
    
    @sync_instance
    def shrink(self):
        if self.isShutdown: raise Exception, 'Pool shutdown'
        if len(self.inn) > 0:
            for r in self.inn[:]:
                try:
                    self.inn.remove(r)
                    self.factory.destroy(r)
                except:
                    log.exception('while shrinking')

    @sync_instance
    def grow(self, size):
        if self.isShutdown: raise Exception, 'Pool shutdown'
        if size > self.size():
            delta = size - self.size()
            for i in range(delta):
                r = self.factory.create()
                self.inn.append(r)