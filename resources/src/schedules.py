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
import copy
import logging
import odict
import os
import ui
import util
import xbmcgui

from enums import CheckForDupesIn, CheckForDupesUsing, EpisodeFilter, ScheduleType
from ui import window_busy 
from util import catchall_ui, lirc_hack, catchall, run_async
from injected import inject_conn, inject_db

log = logging.getLogger('mythtv.ui')

# ==============================================================================
class SchedulesWindow(ui.BaseWindow):
    
    def __init__(self, *args, **kwargs):
        ui.BaseWindow.__init__(self, *args, **kwargs)
        
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
        self.platform = kwargs['platform']
        self.fanArt = kwargs['fanArt']
        self.mythChannelIconCache = kwargs['cachesByName']['mythChannelIconCache']
        
        self.schedules = []                       # [RecordingSchedule]
        self.listItemsBySchedule = odict.odict()  # {RecordingSchedule:ListItem}
        self.channelsById = None                  # {int:Channel}
        self.closed = False
        
    @catchall
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.schedulesListBox = self.getControl(600)
            self.refreshButton = self.getControl(250)
            self.render()

    @catchall_ui
    @lirc_hack    
    def onClick(self, controlId):
        source = self.getControl(controlId)
        if source == self.schedulesListBox: 
            self.goEditSchedule()
        elif source == self.refreshButton:
            self.render()
             
    def onFocus(self, controlId):
        pass
            
    @catchall
    @lirc_hack            
    def onAction(self, action):
        if action.getId() in (ui.ACTION_PREVIOUS_MENU, ui.ACTION_PARENT_DIR):
            self.closed = True
            self.close()

    def goEditSchedule(self):
        editScheduleDialog = ScheduleDialog(
            "mythbox_schedule_dialog.xml", 
            os.getcwd(), 
            forceFallback=True,
            schedule=self.schedules[self.schedulesListBox.getSelectedPosition()], 
            translator=self.translator,
            platform=self.platform,
            settings=self.settings)
        editScheduleDialog.doModal()
        if editScheduleDialog.shouldRefresh:
            self.render()
             
    @inject_db
    def cacheChannels(self):
        if not self.channelsById:
            self.channelsById = {}
            for channel in self.db().getChannels():
                self.channelsById[channel.getChannelId()] = channel
                
    @window_busy
    @inject_db
    def render(self):
        
        def compareTitleAsc(x, y):
            if x.title() == y.title():
                return x.getScheduleType() < y.getScheduleType()
            else:
                return cmp(x.title(), y.title())
        
        log.debug('Rendering....')
        self.cacheChannels()
        self.schedules = self.db().getRecordingSchedules()
        self.schedules.sort(compareTitleAsc)
        self.listItemsBySchedule.clear()

        listItems = []
        for i, s in enumerate(self.schedules):
            listItem = xbmcgui.ListItem('Row %d' % i)
            self.setListItemProperty(listItem, 'title', s.title())
            self.setListItemProperty(listItem, 'scheduleType', s.formattedScheduleType())
            #self.setListItemProperty(listItem, 'description', s.formattedDescription())
            self.setListItemProperty(listItem, 'fullTitle', s.fullTitle())
            self.setListItemProperty(listItem, 'priority', '%s' % s.getPriority())
            #self.setListItemProperty(listItem, 'airDate', s.formattedAirDateTime())
            self.setListItemProperty(listItem, 'channelName', s.getChannelName())
            #self.setListItemProperty(listItem, 'originalAirDate', s.formattedOrigAirDate())
            
            channel = self.channelsById[s.getChannelId()]
            if channel.getIconPath():
                channelIcon = self.mythChannelIconCache.get(channel)
                if channelIcon:
                    self.setListItemProperty(listItem, 'channelIcon', channelIcon)
            
            listItems.append(listItem)
            self.listItemsBySchedule[s] = listItem
        self.schedulesListBox.addItems(listItems)
        self.renderPosters()

    def renderPosters(self):
        # split up poster lookup to run in parallel
        for schedules in util.slice(self.listItemsBySchedule.keys(), 4):
            self.renderPostersThread(schedules)

    @run_async
    @catchall
    def renderPostersThread(self, schedules):
        for i, schedule in enumerate(schedules):
            if self.closed:
                return
            # Lookup poster if available
            #log.debug('Poster %d/%d for %s' % (i+1, len(self.listItemsBySchedule), schedule.title()))
            posterPath = self.fanArt.getRandomPoster(schedule)
            listItem = self.listItemsBySchedule[schedule]
            if posterPath:
                self.setListItemProperty(listItem, 'poster', posterPath)
            else:
                channel =  self.channelsById[schedule.getChannelId()]
                if channel.getIconPath():
                    self.setListItemProperty(listItem, 'poster', self.mythChannelIconCache.get(channel))

# =============================================================================            
class ScheduleDialog(xbmcgui.WindowXMLDialog):
    """
    Create new and edit existing recording schedules
    """
        
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        # Leave passed in schedule untouched; work on a copy of it 
        # in case the user cancels the operation.
        self.schedule = copy.copy(kwargs['schedule'])
        self.translator = kwargs['translator']
        self.platform = kwargs['platform']
        self.settings = kwargs['settings']
        self.shouldRefresh = False
        
    @catchall_ui
    def onInit(self):
        log.debug('onInit')
        self.scheduleTypeButton = self.getControl(201)
        self.priorityButton = self.getControl(202)
        self.checkForDupesUsingButton = self.getControl(203)
        self.checkForDupesInButton = self.getControl(204)
        self.episodeFilterButton = self.getControl(208)
        
        self.enabledCheckBox = self.getControl(212)
        self.autoCommFlagCheckBox = self.getControl(205)
        self.autoExpireCheckBox = self.getControl(207)
        self.autoTranscodeCheckBox = self.getControl(218)
        self.recordNewExpireOldCheckBox = self.getControl(213) 
        
        self.maxEpisodesButton = self.getControl(206)
        self.startEarlyButton = self.getControl(209)
        self.endLateButton = self.getControl(210)
        
        self.saveButton = self.getControl(250)
        self.deleteButton = self.getControl(251)
        self.cancelButton = self.getControl(252)
        
        self.headingLabel = self.getControl(20)
        self.channelLabel = self.getControl(21)
        self.stationLabel = self.getControl(22)
        self.timeLabel = self.getControl(23)
        self.titleLabel = self.getControl(24)
        self.dateLabel = self.getControl(25)
        
        self._updateView()

    def onFocus(self, controlId):
        pass
        
    @catchall_ui 
    @lirc_hack
    def onAction(self, action):
        if action.getId() in (ui.ACTION_PREVIOUS_MENU, ui.ACTION_PARENT_DIR):
            log.debug("before close")
            self.close()
            log.debug("after close")
        else:
            log.debug("onAction not handled")

    @catchall_ui
    @lirc_hack    
    @inject_conn
    def onClick(self, controlId):
        log.debug('onClick %s ' % controlId)
        source = self.getControl(controlId)
        schedule = self.schedule
        
        if self.scheduleTypeButton == source:
            self._chooseFromList(ScheduleType.long_translations, 'Record', self.scheduleTypeButton, schedule.setScheduleType)
        
        elif self.priorityButton == source:
            priority = self._enterNumber('Recording Priority', schedule.getPriority(), -99, 99)
            schedule.setPriority(priority)
            self.priorityButton.setLabel(label='Priority', label2=str(priority))
        
        elif self.autoCommFlagCheckBox == source: 
            schedule.setAutoCommFlag(self.autoCommFlagCheckBox.isSelected())
        
        elif self.autoExpireCheckBox == source: 
            schedule.setAutoExpire(self.autoExpireCheckBox.isSelected())
        
        elif self.enabledCheckBox == source: 
            schedule.setEnabled(self.enabledCheckBox.isSelected())
        
        elif self.autoTranscodeCheckBox == source: 
            schedule.setAutoTranscode(self.autoTranscodeCheckBox.isSelected())
        
        elif self.recordNewExpireOldCheckBox == source: 
            schedule.setRecordNewAndExpireOld(self.recordNewExpireOldCheckBox.isSelected())    
        
        elif self.checkForDupesUsingButton == source:
            self._chooseFromList(CheckForDupesUsing.translations, 'Check for Duplicates Using', self.checkForDupesUsingButton, schedule.setCheckForDupesUsing)            
        
        elif self.checkForDupesInButton == source:
            self._chooseFromList(CheckForDupesIn.translations, 'Check for Duplicates In', self.checkForDupesInButton, schedule.setCheckForDupesIn)
        
        elif self.episodeFilterButton == source:
            self._chooseFromList(EpisodeFilter.translations, 'Episode Filter', self.episodeFilterButton, schedule.setEpisodeFilter)
            
        elif self.maxEpisodesButton == source:
            maxEpisodes = self._enterNumber('Keep At Most - Episodes', schedule.getMaxEpisodes(), 0, 99)
            schedule.setMaxEpisodes(maxEpisodes)
            self.maxEpisodesButton.setLabel(
                label='Keep At Most', 
                label2=('%d Episode(s)' % maxEpisodes, 'All Episodes')[maxEpisodes == 0]) 

        elif self.startEarlyButton == source:
            minutes = self._enterNumber('Start Recording Early - Minutes', schedule.getStartOffset(), 0, 60) 
            schedule.setStartOffset(minutes)
            self.startEarlyButton.setLabel(
                label='Start Recording', 
                label2=('%d minute(s) early' % minutes, 'On time')[minutes == 0])

        elif self.endLateButton == source:
            minutes = self._enterNumber('End Recording Late - Minutes', schedule.getEndOffset(), 0, 60) 
            schedule.setEndOffset(minutes)
            self.endLateButton.setLabel(
                label='End Recording', 
                label2=('%d minute(s) late' % minutes, 'On time')[minutes == 0])
            
        elif self.saveButton == source:
            log.debug("Save button clicked")
            self.conn().saveSchedule(self.schedule)
            self.shouldRefresh = True
            self.close()
            
        elif self.deleteButton == source:
            log.debug('Delete button clicked')
            self.conn().deleteSchedule(self.schedule)
            self.shouldRefresh = True
            self.close()
            
        elif self.cancelButton == source:
            log.debug("Cancel button clicked")
            log.debug('onClick - before close')
            self.close()
            log.debug('onClick - after close')

    def _updateView(self):
        schedule = self.schedule
        
        if schedule.getScheduleId() is None:
            self.headingLabel.setLabel('New Recording Schedule')
            self.deleteButton.setEnabled(False)
        else:
            self.headingLabel.setLabel('Edit Recording Schedule')
            
        self.channelLabel.setLabel(schedule.getChannelNumber())
        self.stationLabel.setLabel(schedule.station())
        
        #TODO: Find root cause
        try:
            self.timeLabel.setLabel(schedule.formattedTime())
        except:
            log.exception("HACK ALERT: schedule.formattedTime() blew up. Known issue.")
            self.timeLabel.setLabel('Unknown')
            
#        self.titleLabel.reset()
#        self.titleLabel.addLabel(schedule.title())    
        self.titleLabel.setLabel(schedule.title())
        self.dateLabel.setLabel(schedule.formattedStartDate())
        
        self.scheduleTypeButton.setLabel(label='Record', label2=schedule.formattedScheduleTypeDescription())
        self.priorityButton.setLabel(label='Priority', label2=str(schedule.getPriority()))

        self.autoCommFlagCheckBox.setLabel('Auto-flag Commercials')
        self.autoCommFlagCheckBox.setSelected(schedule.isAutoCommFlag())
        
        self.autoExpireCheckBox.setLabel('Auto-expire')
        self.autoExpireCheckBox.setSelected(schedule.isAutoExpire())
        
        self.checkForDupesUsingButton.setLabel(
            label='Check for Duplicates Using', 
            label2=self.translator.get(CheckForDupesUsing.translations[schedule.getCheckForDupesUsing()]))
        
        self.checkForDupesInButton.setLabel(
            label='Check for Duplicates In', 
            label2=self.translator.get(CheckForDupesIn.translations[schedule.getCheckForDupesIn()]))
        
        self.episodeFilterButton.setLabel(
            label='Episode Filter',
            label2=self.translator.get(EpisodeFilter.translations[schedule.getEpisodeFilter()]))
        
        self.enabledCheckBox.setSelected(schedule.isEnabled())
        self.autoTranscodeCheckBox.setSelected(schedule.isAutoTranscode())
        self.recordNewExpireOldCheckBox.setSelected(schedule.isRecordNewAndExpireOld())
        
        self.maxEpisodesButton.setLabel(label='Keep At Most', 
            label2=('%d Episode(s)' % schedule.getMaxEpisodes(), 'All Episodes')[schedule.getMaxEpisodes() == 0])

        self.startEarlyButton.setLabel(label='Start Recording', 
            label2=('%d minute(s) early' % schedule.getStartOffset(), 'On time')[schedule.getStartOffset() == 0])
        
        self.endLateButton.setLabel(label='End Recording', 
            label2=("%d minute(s) late" % schedule.getEndOffset(), 'On time')[schedule.getEndOffset() == 0])
        
    def _chooseFromList(self, translations, label, button, setter):
        """
        Boiler plate code that presents the user with a dialog box to select a value from a list.
        Once selected, the setter method on the Schedule is called to reflect the selection.
        
        @param translations: odict of {enumerated type:translation index}
        @param label: string - Dialog box title and button label
        @param button: ControlButton that triggered this chooser
        @param setter: method on Schedule to 'set' selected item from chooser
        """
        pickList = self.translator.toList(translations)
        selected = xbmcgui.Dialog().select(label, pickList)
        if selected >= 0:
            button.setLabel(label=label, label2=pickList[selected])
            setter(translations.keys()[selected])
            
    def _enterNumber(self, heading, current, min=None, max=None):
        """
        Prompt user to enter a valid number with optional min/max bounds.
        
        @param heading: Dialog title as string
        @param current: current value as int
        @param min: Min value of number as int
        @param max: Max value of number as int
        @return: entered number as int
        """
        value = xbmcgui.Dialog().numeric(0, heading, str(current))
        if value == str(current):
            return current
        
        result = int(value)
        
        if min is not None and result < min:
            xbmcgui.Dialog().ok('Error', 'Value must be between %d and %d' % (min, max))
            result = current
            
        if max is not None and result > max:
            xbmcgui.Dialog().ok('Error', 'Value must be between %d and %d' % (min, max))
            result = current
            
        return result             