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
import os
import socket
import sys
import xbmc

log = logging.getLogger('mythbox.core')

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
            'mysql-connector-python',
            'python-twitter',
            'twisted',
            'zope.interface']
        
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
    
    def getFFMpegPath(self):
        return ''

    def getDefaultRecordingsDir(self):
        return ''

    def getMediaPath(self, mediaFile):
        # TODO: Fix when we support multiple skins
        return os.path.join(self.getScriptDir(), 'resources', 'skins', 'Default', 'media', mediaFile)
        

class UnixPlatform(Platform):

    def getName(self):
        return "unix"
    
    def isUnix(self):
        return True
        
    def getFFMpegPath(self):
        return '/usr/bin/ffmpeg'

    def getDefaultRecordingsDir(self):
        return '/var/lib/mythtv/recordings'
    

class WindowsPlatform(Platform):

    def getName(self):
        return "windows"

    def getFFMpegPath(self):
        return os.path.join(self.getScriptDir(), 'resources', 'bin', 'win32', 'ffmpeg.exe')

    def getDefaultRecordingsDir(self):
        return 'c:\\change\\me'


class MacPlatform(Platform):

    def getName(self):
        return 'mac'

    def getFFMpegPath(self):
        return os.path.join(self.getScriptDir(), 'resources', 'bin', 'osx', 'ffmpeg')

    def getDefaultRecordingsDir(self):
        return '/change/me'
