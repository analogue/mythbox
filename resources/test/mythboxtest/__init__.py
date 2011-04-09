
from os.path import join, exists, abspath
from os import getcwd

def getParent(d):
    if not exists(d):
        return None
    return abspath(join(d, '..'))

def getLogger(loggerName):
    #print "getlogger called"
    import logging
    logger  = logging.getLogger(loggerName)
    if not logger.handlers:
        #print 'loading log config'
        import logging.config
        
        d = getcwd()
        f = join(d, 'mythbox_log.ini')
        
        while not exists(f) and d:
            d  = getParent(d)
            f = join(d, 'mythbox_log.ini')
            
        if d:
            #print 'loading log config from %s' % f
            logging.config.fileConfig(f)
            logger = logging.getLogger(loggerName)
            
    return logger
