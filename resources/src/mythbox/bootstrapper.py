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
import os
import sys
import traceback
import xbmc
import xbmcgui

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
            self.bootstrapLegacy()
            #self.bootstrapMySql()
            self.bootstrapCaches()
            self.bootstrapSettings()
            self.bootstrapUpdater()
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
        self.log = logging.getLogger('mythtv.core')
        self.log.info('Mythbox Logger Initialized')
    
    def bootstrapPlatform(self):
        self.stage = 'Initializing Platform'
        import mythbox
        self.platform = mythbox.getPlatform()
        self.platform.addLibsToSysPath()
        self.log.info('Mythbox Platform Initialized')
        
    def bootstrapLegacy(self):
        self.stage = 'Initializing'
        import util
        util.initialize()

#    def bootstrapMySql(self):
#        self.stage = 'Initializing MySQL'
#        # MySQL rigamarole..
#        import platform
#        mysqlVerifier = platform.MySqlVerifier(self.platform)
#        (mySqlBindingDir, mySqlLibDir) = mysqlVerifier.getWorkingMySqlConfig()  
#        sys.path.append(mySqlBindingDir)
#        sys.path.append(mySqlLibDir)

    def bootstrapCaches(self):
        self.stage = 'Initializing Caches'
        
        import util
        self.translator = util.NativeTranslator(self.platform.getScriptDir())

        import filecache
        import injected
        dataDir = self.platform.getScriptDataDir()
        self.mythThumbnailCache = filecache.FileCache(os.path.join(dataDir, 'mythThumbnailCache'), injected.InjectedMythThumbnailResolver())
        self.mythChannelIconCache = filecache.FileCache(os.path.join(dataDir, 'mythChannelIconCache'), injected.InjectedMythChannelIconResolver())
        self.fileCache = filecache.FileCache(os.path.join(dataDir, 'networkCache'), filecache.FileSystemResolver())
        self.httpCache = filecache.FileCache(os.path.join(dataDir, 'httpCache'), filecache.HttpResolver())

        self.cachesByName = {
            'mythThumbnailCache'  : self.mythThumbnailCache, 
            'mythChannelIconCache': self.mythChannelIconCache, 
            'fileCache'           : self.fileCache, 
            'httpCache'           : self.httpCache
        }
        
    def bootstrapSettings(self):
        self.stage = 'Initializing Settings'
        import mythtv
        import fanart
        self.settings = mythtv.MythSettings(self.platform, self.translator, 'settings.xml')
        self.log.debug('Settings = \n %s' % self.settings)
        self.fanArt = fanart.FanArt(self.platform, self.httpCache, self.settings)
        self.settings.addListener(LogSettingsListener())

    def bootstrapUpdater(self):
        self.stage = 'Initializing Updater'
        import updater
        updater.UpdateChecker(self.platform).isUpdateAvailable()
        
    def bootstrapHomeScreen(self):
        import mythbox.home
        mythbox.home.HomeWindow(
            'mythbox_home.xml', 
            os.getcwd(), 
            settings=self.settings, 
            translator=self.translator, 
            platform=self.platform, 
            fanArt=self.fanArt, 
            cachesByName=self.cachesByName).doModal()

# =============================================================================            
class LogSettingsListener(object):
    
    def settingChanged(self, tag, old, new):
        if tag == 'logging_enabled':
            import logging
            logging.root.debug('Setting changed: %s %s %s' % (tag, old, new))
            if new == 'True':
                logging.root.disabled = True
            elif new == 'False':
                logging.root.disabled = False
                