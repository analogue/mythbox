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
import xbmcgui

from mythbox.mythtv.db import inject_db
from mythbox.mythtv.conn import inject_conn
from mythbox.mythtv.domain import StatusException
from mythbox.mythtv.enums import JobType, JobStatus
from mythbox.ui.player import MythPlayer, NoOpCommercialSkipper, TrackingCommercialSkipper
from mythbox.ui.schedules import ScheduleDialog
from mythbox.ui.toolkit import *
from mythbox.util import catchall, catchall_ui, run_async, lirc_hack, coalesce, CyclingBidiIterator

log = logging.getLogger('mythbox.ui')

# =============================================================================
class RecordingDetailsWindow(BaseWindow):
    
    def __init__(self, *args, **kwargs):
        """
        @keyword program: RecordedProgram
        @keyword settings: MythSettings
        @keyword translator: Translator
        @keyword mythThumbnailCache: FileCache
        """
        BaseWindow.__init__(self, *args, **kwargs)
        self.programIterator = kwargs['programIterator']
        self.program = self.programIterator.current() 
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
        self.platform = kwargs['platform']
        self.mythThumbnailCache = kwargs['mythThumbnailCache']
        self.isDeleted = False
        self.initialized = False
        self.win = None
            
    @catchall_ui
    def onInit(self):
        if not self.initialized:
            self.initialized = True
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            
            # Buttons
            self.playButton = self.getControl(250)
            self.playSkipButton = self.getControl(251)
            self.deleteButton = self.getControl(252)
            self.rerecordButton = self.getControl(253)
            self.firstInQueueButton = self.getControl(254)
            self.refreshButton = self.getControl(255)
            self.editScheduleButton = self.getControl(256)
            
            self.dispatcher = {
                self.playButton.getId()        : self.play,
                self.playSkipButton.getId()    : self.playWithCommSkip,
                self.deleteButton.getId()      : self.delete,
                self.rerecordButton.getId()    : self.rerecord,
                self.firstInQueueButton.getId(): self.moveToFrontOfJobQueue,
                self.refreshButton.getId()     : self.refresh,
                self.editScheduleButton.getId(): self.editSchedule
            }
            self.render()
        
    @inject_db    
    def autoexpire(self):
        self.db().setRecordedAutoexpire(
            self.program.getChannelId(), 
            self.program.starttime(), 
            not self.program.isAutoExpire())
        self.refresh()

    def delete(self):
        yes = True
        if self.settings.isConfirmOnDelete():
            yes = xbmcgui.Dialog().yesno(self.translator.get(28), self.translator.get(65))

        @run_async
        @catchall
        @inject_conn
        def deleteAsync(self):
            self.conn().deleteRecording(self.program)
            
        if yes:
            deleteAsync(self)
            self.isDeleted = True
            self.close()
    
    def rerecord(self):
        yes = True
        if self.settings.isConfirmOnDelete():
            yes = xbmcgui.Dialog().yesno(self.translator.get(28), self.translator.get(65))
      
        @run_async
        @catchall
        @inject_conn
        def rerecordAsync(self):
            self.conn().rerecordRecording(self.program)
            
        if yes:
            rerecordAsync(self)
            self.isDeleted = True
            self.close()

    @inject_db
    def moveToFrontOfJobQueue(self):
        jobs = self.db().getJobs(program=self.program, jobStatus=JobStatus.QUEUED, jobType=JobType.COMMFLAG)
        if len(jobs) == 1:
            job = jobs[0]
            job.moveToFrontOfQueue()
            self.refresh()
        else:
            xbmcgui.Dialog().ok('Error', 'Job not found')

    def play(self):
        p = MythPlayer(mythThumbnailCache=self.mythThumbnailCache)
        p.playRecording(self.program, NoOpCommercialSkipper(p, self.program))
        del p 
    
    def playWithCommSkip(self):
        p = MythPlayer(mythThumbnailCache=self.mythThumbnailCache)
        p.playRecording(self.program, TrackingCommercialSkipper(p, self.program))
        del p 
        
    @inject_db
    def editSchedule(self):
        if self.program.getScheduleId() is None:
            xbmcgui.Dialog().ok('Info', 'Recording schedule not found.')
            return
    
        schedules = self.db().getRecordingSchedules(scheduleId=self.program.getScheduleId())
        if len(schedules) == 0:
            xbmcgui.Dialog().ok('Info', 'Recording schedule not found.')
            return 

        editScheduleDialog = ScheduleDialog(
            "mythbox_schedule_dialog.xml", 
            os.getcwd(), 
            forceFallback=True,
            schedule=schedules[0], 
            translator=self.translator,
            platform=self.platform,
            settings=self.settings)
        editScheduleDialog.doModal()
        if editScheduleDialog.shouldRefresh:
            self.render()
    
    def nextRecording(self):
        self.program = self.programIterator.next()
        self.render()
        
    def previousRecording(self):
        self.program = self.programIterator.previous()
        self.render()
                
    @catchall_ui 
    @lirc_hack
    def onAction(self, action):
        id = action.getId()
        if id in (Action.PREVIOUS_MENU, Action.PARENT_DIR):
            self.close()
        elif id == Action.PAGE_UP:
            self.previousRecording()
        elif id == Action.PAGE_DOWN:
            self.nextRecording()
        else: 
            log.debug('action = %s  id = %s' % (action, action.getId()))

    def onFocus(self, controlId):
        pass
            
    @catchall_ui 
    @lirc_hack   
    @window_busy
    def onClick(self, controlId):
        #log.debug('onClick %s ' % controlId)
        source = self.getControl(controlId)
        try:
            self.dispatcher[source.getId()]()
            return True
        except KeyError:
            return False

    @inject_conn
    def refresh(self):
        refreshedProgram = self.conn().getRecording(self.program.getChannelId(), self.program.starttime())
        if refreshedProgram:
            self.program = refreshedProgram
            self.render()
        else:
            raise Exception, 'Program %s not found.' % self.program.title() 

    @window_busy
    def render(self):
        self.renderThumbnail()
        self.renderDetail()
        self.renderCommBreaks()  # NOTE: async
        
    def renderDetail(self):
        s = self.program
        self.setWindowProperty('title', s.fullTitle())
        self.setWindowProperty('airDate', s.formattedAirDateTime())
        self.setWindowProperty('originalAirDate', s.formattedOriginalAirDate())
        self.setWindowProperty('channel', s.formattedChannel())
        self.setWindowProperty('description', s.formattedDescription())
        self.setWindowProperty('category', s.category())
        self.setWindowProperty('fileSize', s.formattedFileSize())
        self.setWindowProperty('autoExpire', (('No', 'Yes')[s.isAutoExpire()]))
        self.setWindowProperty('commBreaks', 'Loading...')       
    
    @run_async
    @catchall
    @inject_db
    @coalesce
    def renderCommBreaks(self):
        self.playSkipButton.setEnabled(self.program.hasCommercials())
        self.firstInQueueButton.setEnabled(False)
        commBreaks = 'No'
        if self.program.isCommFlagged():
            if self.program.hasCommercials():
                # TODO: Only set focus on first entry to screen
                self.setFocus(self.playSkipButton)
                commBreaks = "%d" % len(self.program.getCommercials())
            else:
                commBreaks = 'None'
        else:
            jobs = self.db().getJobs(program=self.program, jobType=JobType.COMMFLAG)
            if len(jobs) == 1:
                job = jobs[0]
                if job.jobStatus == JobStatus.QUEUED:
                    position, numJobs = job.getPositionInQueue() 
                    commBreaks = 'Queued %d of %d' % (position, numJobs)
                    if position != 1:
                        self.firstInQueueButton.setEnabled(True)
                elif job.jobStatus == JobStatus.RUNNING:
                    try:
                        # TODO: Add ETA 
                        commBreaks = '%d%% at %2.0f fps' % (job.getPercentComplete(), job.getCommFlagRate())
                    except StatusException:
                        commBreaks = job.comment
                else:                                    
                    commBreaks = job.formattedJobStatus()
        self.setWindowProperty('commBreaks', commBreaks)
        
    def renderThumbnail(self):
        thumbFile = self.mythThumbnailCache.get(self.program)
        if thumbFile:
            self.setWindowProperty('thumbnailShadow', 'mb-DialogBack.png')
            self.setWindowProperty('thumbnail', thumbFile)
        else:
            log.error('Recording thumbnail preview image not found: %s' % self.program.title())