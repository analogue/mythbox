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
import sys
import util

import injected
import mythdb
import pool
import ui
import uisettings
import xbmc
import xbmcgui

from enums import *
from ui import window_busy
from util import catchall_ui, lirc_hack 
from injected import inject_conn, inject_db

log = logging.getLogger('mythtv.ui')

# =============================================================================
class HomeWindow(ui.BaseWindow):
    
    def __init__(self, *args, **kwargs):
        ui.BaseWindow.__init__(self, *args, **kwargs)
        self.settings     = kwargs['settings']
        self.translator   = kwargs['translator']
        self.platform     = kwargs['platform']
        self.fanArt       = kwargs['fanArt']
        self.cachesByName = kwargs['cachesByName']
        self.win = None
        
        self.mythThumbnailCache = self.cachesByName['mythThumbnailCache']
        self.mythChannelIconCache = self.cachesByName['mythChannelIconCache']
        self.httpCache = self.cachesByName['httpCache']
        self.progressDialog = None
        self.coverFlow = False
        
    def onFocus(self, controlId):
        pass
    
    @catchall_ui
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.tunersListBox = self.getControl(249)
            self.jobsListBox = self.getControl(248)
            self.coverFlow = self.getControl(500)
            
            # button ids -> funtion ptr
            self.dispatcher = {
                250 : self.goWatchRecordings,
                251 : self.goWatchTv,
                252 : self.goTvGuide,
                253 : self.goRecordingSchedules,
                254 : self.goUpcomingRecordings,
                256 : self.goSettings,
                255 : self.refresh
            }
            
            if self.startup():
                self.render()
        elif self.settingsOK:
            self.refresh()
   
    @catchall_ui
    @lirc_hack            
    def onAction(self, action):
        if action.getId() in (ui.ACTION_PREVIOUS_MENU, ui.ACTION_PARENT_DIR):
            self.closed = True
            self.shutdown()
            self.close()

    @catchall_ui
    @lirc_hack    
    def onClick(self, controlId):
        try:
            self.dispatcher[controlId]()
        except KeyError:
            pass
   
    @window_busy
    def startup(self):
        """
        @return: True if startup successful, False otherwise
        """
        self.settingsOK = False
        try:
            self.settings.verify()
            self.settingsOK = True
        except util.SettingsException, se:
            ui.showPopup('Settings Error', str(se), 10000)
            self.goSettings()
            try:
                self.settings.verify() # TODO: optimize unnecessary re-verify
                self.settingsOK = True
            except util.SettingsException:
                self.shutdown()
                self.close()
                return False
            
        if self.settingsOK:      
            # init pools for @inject_db and @inject_conn
            pool.pools['dbPool'] = pool.Pool(mythdb.MythDatabaseFactory(settings=self.settings, translator=self.translator))
            pool.pools['connPool'] = pool.Pool(injected.ConnectionFactory(settings=self.settings, translator=self.translator, platform=self.platform))
            self.settings.addListener(DatabaseSettingsListener())
        
        return self.settingsOK
    
    def shutdown(self):
        try:
            # print pool stats and shutdown
            for (poolName, poolInstance) in pool.pools.items():
                log.info('Pool %s: available = %d  size = %d' % (poolName, poolInstance.available(), poolInstance.size()))
                poolInstance.shutdown()
            log.info('Goodbye!')
        except:
            log.exception('Error while shutting down')

        try:
            logging.shutdown()
            sys.modules.clear()
        except Exception, e:
            xbmc.log('%s' % str(e))            
        
    def goWatchTv(self):
        import livetv; 
        livetv.LiveTvWindow(
            'mythbox_livetv.xml', 
            os.getcwd(), 
            settings=self.settings, 
            translator=self.translator, 
            mythChannelIconCache=self.mythChannelIconCache, 
            fanArt=self.fanArt, 
            platform=self.platform).doModal()
        
    def goWatchRecordings(self):
        import recordings 
        #recordings.RecordingsWindow(
        #    'mythbox_recordings.xml', 
        #    os.getcwd(), 
        #    settings=self.settings, 
        #    translator=self.translator, 
        #    platform=self.platform, 
        #    fanArt=self.fanArt, 
        #    cachesByName=self.cachesByName).doModal()
        
        #import recordings; 
        recordings.showWindow(self.progressDialog, self.settings, self.translator, self.mythThumbnailCache, self.platform)
        
    def goTvGuide(self):
        import tvguide; 
        tvguide.showWindow(self.progressDialog, self.settings, self.translator, self.platform)    
    
    def goRecordingSchedules(self):
        import schedules; 
        schedules.SchedulesWindow(
            'mythbox_schedules.xml', 
            os.getcwd(), 
            settings=self.settings, 
            translator=self.translator, 
            platform=self.platform, 
            fanArt=self.fanArt, 
            cachesByName=self.cachesByName).doModal()
            
    def goUpcomingRecordings(self):
        import upcoming
        upcoming.UpcomingRecordingsWindow(
            'mythbox_upcoming.xml', 
            os.getcwd(), 
            settings=self.settings, 
            translator=self.translator, 
            platform=self.platform, 
            fanArt=self.fanArt, 
            cachesByName=self.cachesByName).doModal()
        
    def goSettings(self):
        uisettings.SettingsWindow(
            'mythbox_settings.xml', 
            os.getcwd(), 
            settings=self.settings, 
            translator=self.translator, 
            platform=self.platform, 
            fanArt=self.fanArt, 
            cachesByName=self.cachesByName).doModal()

    def refresh(self):
        self.render()

    @window_busy
    def render(self):
        self.renderTuners()
        self.renderJobs()
        self.renderStats()
        self.renderCoverFlow()

    @inject_conn
    def renderCoverFlow(self):
        if not self.coverFlow:
            self.coverFlow = True
            recordings = self.conn().getRecordings()
            import random
            random.shuffle(recordings)
            self.coverFlow.reset()
            for i, r in enumerate(recordings[:5]):
                log.debug(r)
                listItem = xbmcgui.ListItem('Row %d' % i)
                #self.setListItemProperty(listItem, 'title', r.title())
                #self.setListItemProperty(listItem, 'thumb', self.fanArt.getRandomPoster(r))
                self.setListItemProperty(listItem, 'title', r.title())
                cover = self.fanArt.getRandomPoster(r)
                if not cover:
                    cover = self.mythThumbnailCache.get(r)
                self.setListItemProperty(listItem, 'thumb', cover)
                # TODO: Refactor to use addItems(...)
                self.coverFlow.addItem(listItem)
        
    @inject_conn
    def renderTuners(self):
        tuners = self.conn().getTuners()
        listItems = []
        for i, t in enumerate(tuners):
            listItem = xbmcgui.ListItem('Row %d' % i)
            self.setListItemProperty(listItem, 'tuner', '%s %s' % (t.tunerType, t.tunerId))
            self.setListItemProperty(listItem, 'hostname', t.hostname)
            self.setListItemProperty(listItem, 'status', t.formattedTunerStatus())
            listItems.append(listItem)
        self.tunersListBox.addItems(listItems)

    @inject_db
    def renderJobs(self):
        running = self.db().getJobs(program=None, jobType=None, jobStatus=JobStatus.RUNNING)
        queued = self.db().getJobs(program=None, jobType=None, jobStatus=JobStatus.QUEUED)
        listItems = []

        for i, j in enumerate(running):
            listItem = xbmcgui.ListItem('Row %d' % i)
            self.setListItemProperty(listItem, 'job', j.formattedJobType())
            self.setListItemProperty(listItem, 'hostname', j.hostname)
            self.setListItemProperty(listItem, 'status', j.formattedJobStatus())
            program = j.getProgram()
            log.debug('getting program for job %s %s %s' % (j.channelId, j.startTime, program))
            if program:
                self.setListItemProperty(listItem, 'job', program.title())
                self.setListItemProperty(listItem, 'status', '%s %s' % ('Comm flagging', self.getJobStats(j)))
            listItems.append(listItem)

        for i, j in enumerate(queued):
            listItem = xbmcgui.ListItem('Row %d' % i)
            self.setListItemProperty(listItem, 'job', j.formattedJobType())
            self.setListItemProperty(listItem, 'hostname', j.hostname)
            self.setListItemProperty(listItem, 'status', j.formattedJobStatus())
            program = j.getProgram()
            log.debug('getting program for job %s %s %s' % (j.channelId, j.startTime, program))
            if program:
                self.setListItemProperty(listItem, 'job', program.title())
            listItems.append(listItem)
        
        self.jobsListBox.addItems(listItems)

    def getJobStats(self, job):
        if job.jobStatus == JobStatus.QUEUED:
            position, numJobs = job.getPositionInQueue() 
            return 'Queued %d of %d' % (position, numJobs)
        elif job.jobStatus == JobStatus.RUNNING:
            try:
                return '%d%% at %2.0f fps' % (job.getPercentComplete(), job.getCommFlagRate())
            except util.StatusException:
                return job.comment
        else:                                    
            return job.formattedJobStatus()
                    
    @inject_conn
    def renderStats(self):
        space = self.conn().getFreeSpace()
        self.setWindowProperty('spaceFree', space[0])
        self.setWindowProperty('spaceTotal', space[1])
        self.setWindowProperty('spaceUsed', space[2])

        loads = self.conn().getLoad()
        self.setWindowProperty('load1min', str(loads[0]))
        self.setWindowProperty('load5min', str(loads[1]))
        self.setWindowProperty('load15min', str(loads[2]))

        self.setWindowProperty('mythFillStatus', self.conn().getMythFillStatus())
        self.setWindowProperty('guideData', self.conn().getGuideData())
        
# =============================================================================            
class DatabaseSettingsListener(object):
    
    def settingChanged(self, tag, old, new):
        import logging
        if tag in ('mysql_host', 'mysql_port', 'mysql_database', 'mysql_user', 'mysql_password'):
            logging.root.debug('Setting changed: %s %s %s' % (tag, old, new))
            # TODO: reset db pools?
            
                