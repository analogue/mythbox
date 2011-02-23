
import logging
import xbmc

from mythbox.bus import Event
from mythbox.util import run_async
from mythbox.mythtv.conn import EventConnection

log = logging.getLogger('mythbox.core')

class MythEventPublisher(object):

    def __init__(self, *args, **kwargs):
        [setattr(self, k, v) for k,v in kwargs.items() if k in ['bus', 'settings','translator','platform']]
        self.closed = False
            
    @run_async
    def startup(self):
        log.debug('Starting MythEventPublisher..')
        self.eventConn = EventConnection(settings=self.settings, translator=self.translator, platform=self.platform, bus=self.bus)
        while not self.closed and not xbmc.abortRequested:
            try:
                tokens = self.eventConn._readMsg(self.eventConn.cmdSock)
                log.debug(tokens)
                if len(tokens)>=3 and tokens[0] == 'BACKEND_MESSAGE':
                    if tokens[1].startswith('SYSTEM_EVENT'):
                        if 'SCHEDULER_RAN' in tokens[1]:
                            log.debug('Publishing scheduler ran...')
                            self.bus.publish({'id':Event.SCHEDULER_RAN})
            except Exception, e:
                log.exception(e)
        log.debug('Exiting MythEventPublisher')
    
    def shutdown(self):
        self.closed = True
        try:
            self.eventConn.close()
        except:
            log.exception('on shutdown')