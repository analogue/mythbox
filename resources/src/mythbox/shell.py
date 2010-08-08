from zope.interface import implements
from twisted.conch import manhole, telnet
#from twisted.conch.manhole_tap import _StupidRealm, makeTelnetProtocol 
from twisted.conch.insults import insults
from twisted.internet import protocol, reactor
from twisted.cred import portal, checkers 

from mythbox.util import run_async

class DebugShell(object):
    
    def __init__(self, port=9999, namespace=None):
        self.port = port
        self.namespace = namespace
    
    def start(self):
        
        def run_in_thread():
            checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(mb='mb')
            #checker = checkers.AllowAnonymousAccess()
            
            telnetRealm = _StupidRealm(telnet.TelnetBootstrapProtocol,
                                       insults.ServerProtocol,
                                       manhole.ColoredManhole,
                                       self.namespace)
        
            telnetPortal = portal.Portal(telnetRealm, [checker])
            telnetFactory = protocol.ServerFactory()
            telnetFactory.protocol = makeTelnetProtocol(telnetPortal)
            port = reactor.listenTCP(self.port, telnetFactory)
            reactor.run(installSignalHandlers=False)
            
        from threading import Thread
        worker = Thread(target = run_in_thread)
        worker.start()
    
    def stop(self):
        reactor.callFromThread(reactor.stop)


class makeTelnetProtocol:
    def __init__(self, portal):
        self.portal = portal

    def __call__(self):
        auth = telnet.AuthenticatingTelnetProtocol
        #auth = telnet.StatefulTelnetProtocol
        args = (self.portal,)
        return telnet.TelnetTransport(auth, *args)


class _StupidRealm:
    implements(portal.IRealm)

    def __init__(self, proto, *a, **kw):
        self.protocolFactory = proto
        self.protocolArgs = a
        self.protocolKwArgs = kw

    def requestAvatar(self, avatarId, *interfaces):
        if telnet.ITelnetProtocol in interfaces:
            return (telnet.ITelnetProtocol,
                    self.protocolFactory(*self.protocolArgs, **self.protocolKwArgs),
                    lambda: None)
        raise NotImplementedError()
