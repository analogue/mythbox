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
import os
import socket
import sys
import xbmc

log = logging.getLogger('mythtv.core')

__instance = None

def getPlatform():
    global __instance
    if not __instance:
        if 'win32' in sys.platform:
            __instance = WindowsPlatform()
        elif 'linux' in sys.platform:
            __instance = UnixPlatform()
        elif 'darwin' in sys.platform:
            __instance = MacPlatform()
        else:
            log.error('ERROR: Platform check did not match win32, linux, or darwin. Was %s instead' % sys.platform)
            __instance = UnixPlatform()
    return __instance

# =============================================================================
class Platform(object):

    def addLibsToSysPath(self):
        """
        Add 3rd party libs in ${scriptdir}/resources/lib to the PYTHONPATH
        """
        libs = [
            'pyxcoder', 
            'decorator', 
            'odict', 
            'elementtree', 
            'tvdb_api', 
            'themoviedb', 
            'IMDbPY', 
            'simplejson', 
            'shove', 
            'durus',
            'mysql-connector-python']
        
        for lib in libs:
            sys.path.append(os.path.join(self.getScriptDir(), 'resources', 'lib', lib))
            
        for i, path in enumerate(sys.path):    
            log.debug('syspath[%d] = %s' % (i, path))
    
    def getName(self):
        return "N/A"
    
    def getScriptDir(self):
        """
        @return: directory that this xbmc script resides in.
        
        linux  : ~/.xbmc/scripts/MythBox
        windows: c:\Documents and Settings\[user]\Application Data\XBMC\scripts\MythBox
        mac    : ~/Library/Application Support/XBMC/scripts/MythBox
        """
        return os.getcwd()

    def getScriptDataDir(self):
        """
        @return: directory for storing user settings for this xbmc script.
        
        linux  : ~/.xbmc/userdata/script_data/MythBox
        windows: c:\Documents and Settings\[user]\Application Data\XBMC\UserData\script_data\MythBox
        mac    : ~/Library/Application Support/XBMC/UserData/script_data/MythBox
        """
        return xbmc.translatePath("T:\\script_data") + os.sep + os.path.basename(self.getScriptDir())

    def getHostname(self):
        try:
            return socket.gethostname()
        except:
            return xbmc.getIPAddress()
        
    def isUnix(self):
        return False
    
    def __repr__(self):
        bar = "=" * 80
        s = bar + \
"""
hostname        = %s
platform        = %s 
script dir      = %s
script data dir = %s
""" % (self.getHostname(), type(self).__name__, self.getScriptDir(), self.getScriptDataDir())
        s += bar
        return s
    
    def getPythonMySqlSharedObjectDir(self):
        """
        @return: Dir containing shared object file (_mysql.so) or dll file (_mysql.pyd) for the python-mysql bindings. 
        """
        pass
    
    def getPythonMySqlBindingsDir(self):
        """
        @return: Dir containing all python bindings for mysql. (all the python files)  
        """
        pass

    def getFFMpegPath(self):
        return ''

    def getDefaultRecordingsDir(self):
        return ''

# =============================================================================
class UnixPlatform(Platform):

    def __init__(self):
        self.mysqlSharedObjectDir = None
        self.mysqlBindingsDir = None
        
    def getName(self):
        return "unix"
    
    def isUnix(self):
        return True
        
    def getPythonMySqlSharedObjectDir(self):
        self._findPythonMySql()
        return self.mysqlSharedObjectDir
    
    def getPythonMySqlBindingsDir(self):
        self._findPythonMySql()
        return self.mysqlBindingsDir

    def _findPythonMySql(self):
        if not self.mysqlBindingsDir or not self.mysqlSharedObjectDir:
            self.mysqlBindingsDir = ''
            self.mysqlSharedObjectDir = ''
        #    verifier = MySqlVerifier(self)
        #    self.mysqlSharedObjectDir, self.mysqlBindingsDir = verifier.getWorkingMySqlConfig()

    def getFFMpegPath(self):
        return '/usr/bin/ffmpeg'

    def getDefaultRecordingsDir(self):
        return '/var/lib/mythtv/recordings'
    
# =============================================================================
class WindowsPlatform(Platform):

    def getName(self):
        return "windows"

    def getPythonMySqlSharedObjectDir(self):
        """
        @return: Dir that contains _mysql.pyd
        """
        return os.path.join(self.getScriptDir(), 'resources', 'lib', 'MySQLdb', 'win32')

    def getPythonMySqlBindingsDir(self):
        return os.path.join(self.getScriptDir(), 'resources', 'lib', 'MySQLdb')

    def getFFMpegPath(self):
        return os.path.join(self.getScriptDir(), 'resources', 'bin', 'win32', 'ffmpeg.exe')

    def getDefaultRecordingsDir(self):
        return 'c:\\change\\me'

# =============================================================================
class MacPlatform(Platform):

    def getName(self):
        return 'mac'

    def getPythonMySqlSharedObjectDir(self):
        """
        @return: Dir that contains mac native _mysql.so
        """
        return os.path.join(self.getScriptDir(), 'resources', 'lib', 'MySQLdb-1.2.1p2', 'osx')

    def getPythonMySqlBindingsDir(self):
        return os.path.join(self.getScriptDir(), 'resources', 'lib', 'MySQLdb-1.2.1p2')

    def getFFMpegPath(self):
        return os.path.join(self.getScriptDir(), 'resources', 'bin', 'osx', 'ffmpeg')

    def getDefaultRecordingsDir(self):
        return '/change/me'
    
# =============================================================================
class MySqlVerifier(object):
    
    def __init__(self, platform):
        self.platform = platform
        
    def getWorkingMySqlConfig(self):
        """
        @return: tuple(python bindings dir, python shared object dir)
        @raise: Exception if working python bindings could not be found. 
        """
        return self.tryDistributionMySqlBindings()

    def pokeMySql(self):
        # should raise exception on failure
        try:
            import MySQLdb
            log.debug('MySQL version = %s' % MySQLdb.apilevel)
        finally:
            try:
                del MySQLdb
            except:
                pass

    def tryDistributionMySqlBindings(self):
        """
        Try to find mysql python bindings and shared lib installed by distribution (not bundled)
        """
        if not self.platform.isUnix():
            raise Exception, 'Distribution mysql bindings only supported on linux'
        
        # Looking for v.1.2.2
        #
        # Ubuntu 9.10 Jaunty
        #  /usr/share/python-support/python-mysqldb
        #  
        # Source (*.py) links to /usr/share version but compiled (*.pyc) not linked:
        #      /var/lib/python-support/python2.5 -> /usr/share/python-support/python-mysqldb 
        #      /var/lib/python-support/python2.6 -> /usr/share/python-support/python-mysqldb
        
        bindingDirs = [
            '/var/lib/python-support/python2.4',                   # Ubuntu
            '/var/lib/python-support/python2.5',                   # Ubuntu
            '/var/lib/python-support/python2.6',                   # Ubuntu 
            #'/usr/share/python-support/python-mysqldb',            # Ubuntu 
            '/usr/lib/python2.4/site-packages',                    # Fedora, OpenSuse, Arch
            '/usr/lib/python2.5/site-packages',                    # Fedora, OpenSuse, Arch
            '/usr/lib/python2.6/site-packages']                    # Fedora, OpenSuse, Arch

        
        # Ubuntu 9.10 Jaunty
        #  /usr/lib/python-support/python-mysqldb/python2.5/_mysql.so
        #  /usr/lib/python-support/python-mysqldb/python2.6/_mysql.so
        #  
        #  links to /usr/lib versions:
        #      TODO
        #      TODO
        
        libDirs = [
            '/usr/lib/python-support/python-mysqldb/python2.4',    # Ubuntu 9.10
            '/usr/lib/python-support/python-mysqldb/python2.5',    # Ubuntu 9.10
            '/usr/lib/python-support/python-mysqldb/python2.6',    # Ubuntu 9.10
            '/usr/lib/python2.4/site-packages',                    # Fedora, OpenSuse, Arch
            '/usr/lib/python2.5/site-packages',                    # Fedora, OpenSuse, Arch
            '/usr/lib/python2.6/site-packages']                    # Fedora, OpenSuse, Arch
        
        for i in range(len(bindingDirs)):
            
            bindingDir = bindingDirs[i]
            bindingFile = os.path.join(bindingDirs[i], '_mysql_exceptions.py')

            libDir = libDirs[i]
            libFile = os.path.join(libDirs[i], '_mysql.so')
            
            log.debug('Attempt %d: mysql bindings in: %s' % (i, bindingDir))
            log.debug('Attempt %d: mysql libs     in: %s' % (i, libDir))
            
            if not os.path.exists(bindingDir):
                log.debug('Skipping: %s does not exist' % bindingDir)
                continue 

            if not os.path.isdir(bindingDir):
                log.debug('Skipping: %s is not a directory' % bindingDir)
                continue 

            if not os.path.exists(bindingFile):
                log.debug('Skipping: %s not found' % bindingFile)
                continue 

            if not os.path.isfile(bindingFile):
                log.debug('Skipping: %s is not a file' % bindingFile)
                continue                                
                                         
            if not os.path.exists(libDir):
                log.debug('Skipping: %s does not exist' % libDir)
                continue 

            if not os.path.isdir(libDir):
                log.debug('Skipping: %s is not a directory' % libDir)
                continue 

            if not os.path.exists(libFile):
                log.debug('Skipping: %s not found' % libFile)
                continue 

            if not os.path.isfile(libFile):
                log.debug('Skipping: %s is not a file' % libFile)
                continue                                

            sys.path.append(bindingDir)
            sys.path.append(libDir)
            try:
                try:
                    self.pokeMySql()
                    log.debug('Successfully loaded python-mysql!')
                    return (bindingDir, libDir)
                except Exception, ex: 
                    log.exception('Skipping: %s' % str(ex))
            finally:
                sys.path.pop()
                sys.path.pop()
        raise Exception, 'Your distribution python-mysql bindings were not found or do not work as expected'