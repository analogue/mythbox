import unittest

import logging
import livetv
import domain

from mockito import *

class LiveTvWindowTest(unittest.TestCase):

    def testConstructor(self):
        
        fanArt = Mock()
        when(fanArt).getRandomPoster(any()).thenReturn(None)
        
        kwargs = {}
        kwargs['settings'] = Mock()
        kwargs['translator'] = Mock()
        kwargs['mythChannelIconCache'] = Mock()
        kwargs['platform'] = Mock()
        kwargs['fanArt'] = fanArt
        args = ()
        win = livetv.LiveTvWindow(*args, **kwargs)
        
        channels = []
        for i in range(10):
            c = domain.Channel({
                'chanid':i, 
                'channum': '%d' % (i*2), 
                'name': 'name%d' % i, 
                'callsign':'callsign%d'%i
            })
            channels.append(c)
        
        db = Mock()
        when(db).getChannels().thenReturn(channels)
        
        programs = []
        for i in range(10):
            p = domain.TVProgram({
                'title': 'title%d' % i, 
                'chanid':i,
                'description':'desc%d'%i,
                'category':'cat%d'%i}, 
                translator=Mock()) 
            programs.append(p)
            
        when(db).getProgramListings(any(), any()).thenReturn(programs)
        
        dbFactory = Mock()
        when(dbFactory).create().thenReturn(db)

        import pool    
        pool.pools['dbPool'] = pool.Pool(dbFactory)
        
        win.onInit()
        win.onClick(self, 600)

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()