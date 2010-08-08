from twisted.internet import reactor
from twisted.cred import portal, checkers 
from twisted.conch import manhole, manhole_ssh

links = {'Twisted': 'http://twistedmatrix.com/', 'Python': 'http://python.org' }

def getManholeFactory(namespace, **passwords):
    realm = manhole_ssh.TerminalRealm()
     
    def getManhole(_): 
        return manhole.Manhole(namespace)
     
    realm.chainedProtocolFactory.protocolFactory = getManhole
    p = portal.Portal(realm) 
    p.registerChecker(checkers.InMemoryUsernamePasswordDatabaseDontUse(**passwords))
    f = manhole_ssh.ConchFactory(p) 
    return f

from mythbox.util import run_async
t = None

@run_async
def runserver():
    port = reactor.listenTCP(9999, getManholeFactory(globals(), admin='aaa'))
    reactor.run(installSignalHandlers=False)


from twisted.conch import telnet
from twisted.conch.manhole_tap import _StupidRealm, makeTelnetProtocol 
from twisted.conch.insults import insults
from twisted.internet import protocol

def getTelnetFactory():

    namespace = globals()
    checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(admin='aaa')
    
    telnetRealm = _StupidRealm(telnet.TelnetBootstrapProtocol,
                               insults.ServerProtocol,
                               manhole.ColoredManhole,
                               namespace)

    telnetPortal = portal.Portal(telnetRealm, [checker])

    telnetFactory = protocol.ServerFactory()
    telnetFactory.protocol = makeTelnetProtocol(telnetPortal)
    return telnetFactory
    #telnetService = strports.service(options['telnetPort'],
    #                                 telnetFactory)
    #telnetService.setServiceParent(svc)

port = None

@run_async 
def runtelnet():
    port = reactor.listenTCP(9999, getTelnetFactory())
    #reactor.callLater(5, reactor.stop)
    reactor.run(installSignalHandlers=False)
    
    
import time
print "Running server"

#runserver()
t = runtelnet()
print "Waiting..."
#time.sleep(2)

#reactor.callLater(5, reactor.stop)

time.sleep(20)
reactor.callFromThread(reactor.stop)
print "Wokeup and stop listening.."
#port.stopListening()
print "Stopping"
#reactor.stop()
print "Done"
#import sys
#sys.exit()
        
#portal = portal.Portal(ExampleRealm())
#passwdDB = checkers.InMemoryUsernamePasswordDatabaseDontUse()
#passwdDB.addUser('user', 'password')
#portal.registerChecker(passwdDB)
#portal.registerChecker(InMemoryPublicKeyChecker())
#ExampleFactory.portal = portal
#
#if __name__ == '__main__':
#    reactor.listenTCP(5022, ExampleFactory())
#    reactor.run()        