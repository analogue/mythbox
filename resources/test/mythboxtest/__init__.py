
from os.path import join, exists, abspath
from os import getcwd

from mythbox.mythtv.protocol import Protocol63

TEST_PROTOCOL = Protocol63()

def getParent(d):
    if not exists(d):
        return None
    return abspath(join(d, '..'))

def getLogger(loggerName):
    #print "getlogger called"
    import logging
    logger  = logging.getLogger(loggerName)
    if not logger.handlers:
        logging.basicConfig()
    return logger
