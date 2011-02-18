import unittest

from mockito import Mock, when, any
from mythbox.ui.livetv import LiveTvWindow
from mythbox.mythtv.domain import Channel, TVProgram

class LiveTvWindowTest(unittest.TestCase):

    def testConstructor(self):
        
        fanArt = Mock()
        when(fanArt).pickPoster(any()).thenReturn(None)
        
        kwargs = {}
        kwargs['settings'] = Mock()
        kwargs['translator'] = Mock()
        kwargs['mythChannelIconCache'] = Mock()
        kwargs['platform'] = Mock()
        kwargs['fanArt'] = fanArt
        args = ()
        win = LiveTvWindow(*args, **kwargs)
        
        channels = []
        for i in range(10):
            c = Channel({
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
            p = TVProgram({
                'title': 'title%d' % i, 
                'chanid':i,
                'description':'desc%d'%i,
                'category':'cat%d'%i}, 
                translator=Mock()) 
            programs.append(p)
            
        when(db).getTVGuideDataFlattened(any(), any(), any()).thenReturn(programs)
        
        dbFactory = Mock()
        when(dbFactory).create().thenReturn(db)

        from mythbox import pool    
        pool.pools['dbPool'] = pool.Pool(dbFactory)
        
        win.onInit()
        win.onClick(self, 600)

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()