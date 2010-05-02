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

import datetime
import logging
import odict
import xbmcgui

from mythbox.mythtv.db import inject_db
from mythbox.mythtv.conn import inject_conn
from mythbox.ui.toolkit import BaseWindow, window_busy, Action
from mythbox.util import catchall_ui, lirc_hack, timed, run_async, catchall, ui_locked, coalesce, ui_locked2

log = logging.getLogger('mythtv.ui')

ONE_DAY = datetime.timedelta(days=1)
ONE_WEEK = datetime.timedelta(weeks=1)

# ==============================================================================
class UpcomingRecordingsWindow(BaseWindow):
    
    def __init__(self, *args, **kwargs):
        BaseWindow.__init__(self, *args, **kwargs)
        
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
        self.platform = kwargs['platform']
        self.fanArt = kwargs['fanArt']
        self.mythChannelIconCache = kwargs['cachesByName']['mythChannelIconCache']
        
        self.programs = []                       # [RecordedProgram]
        self.channelsById = None                 # {int:Channel}
        self.tunersById = None                   # {int:Tuner}
        self.listItemsByProgram = odict.odict()  # {Program:ListItem}
        self.closed = False
        
    @catchall_ui
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.programsListBox = self.getControl(600)
            self.refreshButton = self.getControl(250)
            self.refresh()
        
    @catchall_ui
    @lirc_hack    
    def onClick(self, controlId):
        source = self.getControl(controlId)
        if source == self.programsListBox: 
            xbmcgui.Dialog().ok('Info', 'Program selected')
        elif source == self.refreshButton:
            self.refresh()
             
    def onFocus(self, controlId):
        pass
            
    @catchall_ui
    @lirc_hack            
    def onAction(self, action):
        #log.debug('Key got hit: %s   Current focus: %s' % (ui.toString(action), self.getFocusId()))
        if action.getId() in (Action.PREVIOUS_MENU, Action.PARENT_DIR):
            self.closed = True
            self.close()

    @inject_db
    def cacheChannels(self):
        if not self.channelsById:
            self.channelsById = {}
            for channel in self.db().getChannels():
                self.channelsById[channel.getChannelId()] = channel

    @inject_db
    def cacheTuners(self):
        if not self.tunersById:
            self.tunersById = {}
            for tuner in self.db().getTuners():
                self.tunersById[tuner.tunerId] = tuner
    
    @window_busy  
    @inject_conn           
    def refresh(self):
        self.cacheChannels()
        self.cacheTuners()
        self.programs = self.conn().getUpcomingRecordings()
        self.render()
        
    @inject_conn
    @ui_locked
    def render(self):
        self.listItemsByProgram.clear()
        listItems = []
        
        log.debug('Rendering %d upcoming recordings...' % len(self.programs))
        
        @ui_locked2
        def buildListItems():
            previous = None
            for i, program in enumerate(self.programs):
                listItem = xbmcgui.ListItem()
                airdate = self.formattedAirDate(previous, program)
                self.setListItemProperty(listItem, 'airdate', airdate)    
                self.setListItemProperty(listItem, 'title', program.title())
                self.setListItemProperty(listItem, 'description', program.formattedDescription())
                self.setListItemProperty(listItem, 'category', program.category())
                self.setListItemProperty(listItem, 'startTime', program.formattedStartTime())
                self.setListItemProperty(listItem, 'duration', program.formattedDuration())
                self.setListItemProperty(listItem, 'channelName', program.getChannelName())
                self.setListItemProperty(listItem, 'channelNumber', program.getChannelNumber())
                self.setListItemProperty(listItem, 'callSign', program.getCallSign())
                self.setListItemProperty(listItem, 'poster', 'loading.gif')
                
                tuner = self.tunersById[program.getTunerId()]
                self.setListItemProperty(listItem, 'tuner', '%s %s' % (tuner.tunerType, tuner.tunerId))
                
                listItems.append(listItem)
                self.listItemsByProgram[program] = listItem
                previous = program

        buildListItems()
        self.programsListBox.reset()
        self.programsListBox.addItems(listItems)
        self.renderChannelIcons()
        self.renderPosters()        

    @run_async
    @timed
    @catchall
    @coalesce
    def renderChannelIcons(self):
        for i, (program, listItem) in enumerate(self.listItemsByProgram.items()):
            if self.closed: return
            channel = self.channelsById[program.getChannelId()]
            if channel and channel.getIconPath() and len(listItem.getProperty('airdate')) == 0:
                self.setListItemProperty(listItem, 'channelIcon', self.mythChannelIconCache.get(channel))
        
    @run_async
    @timed
    @catchall
    @coalesce
    def renderPosters(self):
        for (program, listItem) in self.listItemsByProgram.items():
            if self.closed: return
            posterPath = self.fanArt.getRandomPoster(program)
            if posterPath:
                self.setListItemProperty(listItem, 'poster', posterPath)
            elif self.channelsById[program.getChannelId()].getIconPath():
                self.setListItemProperty(listItem, 'poster', self.mythChannelIconCache.get(self.channelsById[program.getChannelId()]))
            else:
                self.setListItemProperty(listItem, 'poster', 'mythbox.png')

    @staticmethod
    def formattedAirDate(previous, current):
        result = u''
        airDate = current.starttimeAsTime().date()
        if not previous or previous.starttimeAsTime().date() < airDate:
            today = datetime.date.today()
            if airDate == today:
                result = u'Today'
            elif today + ONE_DAY == airDate:
                result = u'Tomorrow'
            else:
                result = datetime.date.strftime(airDate, '%a, %b %d')
        return result
