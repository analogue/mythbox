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
import os
import sys
import traceback
import xbmc
import xbmcgui

from mythbox.bus import EventBus

# =============================================================================
class BootStrapper(object):
    
    def __init__(self):
        self.log = None
        self.platform = None
        self.stage = 'Initializing'
    
    def run(self):
        try:
            self.bootstrapLogger()
            self.bootstrapPlatform()
            self.bootstrapEventBus()            
            self.bootstrapCaches()
            self.bootstrapSettings()
            self.bootstrapUpdater()
            self.bootstrapFeeds()
            self.bootstrapHomeScreen()
        except Exception, ex:
            self.handleFailure(ex)
        
    def handleFailure(self, cause):
        msg = 'MythBox:%s - Error: %s' % (self.stage, cause)
        xbmc.log(msg)
        print traceback.print_exc()
        if self.log:
            self.log.exception(str(cause))
        xbmcgui.Dialog().ok('MythBox Error', 'Stage: %s' % self.stage, 'Exception: %s' % str(cause))
        
    def updateProgress(self, msg):
        self.log.info(msg)

    def bootstrapLogger(self):
        import logging
        import logging.config
        self.stage = 'Initializing Logger'
        if 'win32' in sys.platform:
            loggerIniFile = os.path.join(os.getcwd(), 'mythbox_win32_log.ini')
        else:
            loggerIniFile = os.path.join(os.getcwd(), 'mythbox_log.ini')
        xbmc.log('MythBox: loggerIniFile = %s' % loggerIniFile)
        logging.config.fileConfig(loggerIniFile)
        self.log = logging.getLogger('mythbox.core')
        self.log.info('Mythbox Logger Initialized')
    
    def bootstrapPlatform(self):
        self.stage = 'Initializing Platform'
        from mythbox.platform import getPlatform
        self.platform = getPlatform()
        self.platform.addLibsToSysPath()
        self.log.info('Mythbox Platform Initialized')

    def bootstrapEventBus(self):
        self.bus = EventBus()
        
    def bootstrapCaches(self):
        self.stage = 'Initializing Caches'
        
        from mythbox.util import NativeTranslator
        from mythbox.filecache import FileCache, FileSystemResolver, HttpResolver, MythThumbnailFileCache
        from mythbox.mythtv.resolver import MythChannelIconResolver, MythThumbnailResolver 
        from os.path import join
        
        dataDir = self.platform.getScriptDataDir()
        self.translator = NativeTranslator(self.platform.getScriptDir())
        self.mythThumbnailCache = MythThumbnailFileCache(join(dataDir, 'mythThumbnailCache'), MythThumbnailResolver(), self.bus)
        self.mythChannelIconCache = FileCache(join(dataDir, 'mythChannelIconCache'), MythChannelIconResolver())
        self.fileCache = FileCache(join(dataDir, 'networkCache'), FileSystemResolver())
        self.httpCache = FileCache(join(dataDir, 'httpCache'), HttpResolver())

        self.cachesByName = {
            'mythThumbnailCache'  : self.mythThumbnailCache, 
            'mythChannelIconCache': self.mythChannelIconCache, 
            'fileCache'           : self.fileCache, 
            'httpCache'           : self.httpCache
        }
        
    def bootstrapSettings(self):
        self.stage = 'Initializing Settings'
        from fanart import FanArt
        from mythbox.settings import MythSettings
        self.settings = MythSettings(self.platform, self.translator, 'settings.xml', self.bus)
        self.log.debug('Settings = \n %s' % self.settings)
        self.fanArt = FanArt(self.platform, self.httpCache, self.settings, self.bus)
        
        import socket
        socket.setdefaulttimeout(20)
        
        self.bus.register(self)
        
        # Generate fake event to reflect value in settings.xml instead of mythbox_log.ini
        from bus import Event
        self.onEvent({'id': Event.SETTING_CHANGED, 'old':'DontCare', 'new':self.settings.get('logging_enabled')})
        
    def bootstrapUpdater(self):
        self.stage = 'Initializing Updater'
        from mythbox.updater import UpdateChecker
        UpdateChecker(self.platform).isUpdateAvailable()
        
    def bootstrapFeeds(self):
        from mythbox.feeds import FeedHose
        self.feedHose = FeedHose(self.settings, self.bus)
            
    def bootstrapHomeScreen(self):
        from mythbox.ui.home import HomeWindow
        HomeWindow(
            'mythbox_home.xml', 
            os.getcwd(), 
            settings=self.settings, 
            translator=self.translator, 
            platform=self.platform, 
            fanArt=self.fanArt, 
            cachesByName=self.cachesByName,
            bus=self.bus,
            feedHose=self.feedHose).doModal()

    def onEvent(self, event):
        from bus import Event
        
        #
        # Apply changes to logger when user turns debug logging on/off
        #
        if event['id'] == Event.SETTING_CHANGED and event['tag'] == 'logging_enabled':
            import logging
            logging.root.debug('Setting changed: %s %s %s' % (event['tag'], event['old'], event['new']))

            if event['new'] == 'True': 
                level = logging.DEBUG
            else: 
                level = logging.WARN
                
            loggerNames = 'unittest mysql core method skin wire ui perf fanart settings cache event inject'.split()
                
            for name in loggerNames:
                logger = logging.getLogger('mythbox.%s' %  name)
                logger.setLevel(level)

            # TODO: Adjust xbmc loglevel 
            #savedXbmcLogLevel = xbmc.executehttpapi("GetLogLevel").replace("<li>", "")
            #xbmc.executehttpapi('SetLogLevel(3)')
