#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
#  Copyright (C) 2005 Tom Warkentin <tom@ixionstudios.com>
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
import ui
import util
import xbmcgui

from datetime import datetime, timedelta
from domain import ScheduleFromProgram
from schedules import ScheduleDialog
from util import catchall_ui, timed, ui_locked, lirc_hack 
from injected import inject_db

log = logging.getLogger('mythtv.ui')
elog = logging.getLogger('mythbox.event')

def showWindow(progressDialog, settings, translator, platform):
    win = Window(settings=settings, translator=translator, platform=platform)
    win.loadGuide()
    win.doModal()
    del win

# =============================================================================
class ProgramCell(object):
    
    def __init__(self, *args, **kwargs):
        self.chanid    = None   # string
        self.program   = None   # Program 
        self.nodata    = None   # boolean 
        self.starttime = None   # ??? 
        self.title     = None   # string 
        self.start     = None   # int - starting x coordinate 
        self.end       = None   # int - ending x coord 
        self.control   = None   # ControlButton 
        self.label     = None   # ControlLabel

# =============================================================================
class ChannelCell(object):
    
    def __init__(self, *args, **kwargs):
        self.icon    = None   # ControlImage if channel has icon, otherwise None
        self.label   = None   # ControlLabel of channel name and callsign
        self.shade   = None   # ControlImage of background shade 

# =============================================================================
class Window(ui.LegacyBaseWindow):

    # Mapping of Myth TV category names to color names (used as a file prefix)
    # in the tv guide.
    categoryColors = {
        "Adults only"       : "red",
        "Basketball"        : "blue",
        "Children"          : "green",
        "Children-music"    : "green",
        "Children-special"  : "green",
        "Fishing"           : "blue",
        "Hockey"            : "blue",
        "News"              : "olive",
        "Newsmagazine"      : "olive",
        "Romance"           : "purple",
        "Romance-comedy"    : "purple",
        "Science"           : "cyan",
        "Science fiction"   : "orange",
        "Sitcom"            : "yellow",
        "Soap"              : "purple",
        "Sports"            : "blue",
        "Sports event"      : "blue",
        "Sports non-event"  : "blue",
        "Talk"              : "purple",
        "Travel"            : "cyan",
    }
    
    def __init__(self, *args, **kwargs):
        """
        @keyword settings: MythSettings
        @keyword translator: Translator
        """
        ui.LegacyBaseWindow.__init__(self, *args, **kwargs)
        self.gridCells = []    # ProgramCell[] for grid of visible programs
        self.startTime = None  # datetime - start time for visibile grid
        self.endTime   = None  # datetime - end time for visible grid
        
        self.startChan = None  # int - index into channels[] of starting channel in visible grid
        self.endChan = None    # int - index info channels[] of ending channel in visible grid
        self.channelSpan = 2   # int - number of channel TODO in visible grid 
        self.channels = None   # Channel[] for all tuners
        
        self.hourSpan = 2.0
        self.channelCells = [] # ChannelCell[] for column visible channels
        self.timeLabels = []   # ControlLabel[] for row of visible time
        self.topCtls = []
        self.bottomCtls = []
        self.leftCtls = []
        self.rightCtls = []
        
        self.prevFocus = None
        self.prevButtonInfo = None
        
        self.initialized = False
        self.loadskin("tvguide.xml")
        
    @catchall_ui
    @timed
    @inject_db
    def loadGuide(self):
        """
        Method to load and display the tv guide information.  If this is
        the first time being called, it initializes the tv guide
        parameters.
        """
        log.debug('tvguide.Window.loadGuide()')

        if self.prevFocus:
            for c in self.gridCells:
                if c.control == self.prevFocus:
                    self.prevButtonInfo = c
                    self.prevFocus = None
                    break

        if not self.initialized:
            # load variables from skin
            self.channel_x = int(self.getvalue(self.getoption("channel_x")))
            self.channel_h = int(self.getvalue(self.getoption("channel_h")))
            self.channel_w = int(self.getvalue(self.getoption("channel_w")))
            self.channel_dx = int(self.getvalue(self.getoption("channel_dx")))
            self.time_y = int(self.getvalue(self.getoption("time_y")))
            self.time_h = int(self.getvalue(self.getoption("time_h")))
            self.guide_x = int(self.getvalue(self.getoption("guide_x")))
            self.guide_y = int(self.getvalue(self.getoption("guide_y")))
            self.guide_dx = int(self.getvalue(self.getoption("guide_dx")))
            self.guide_dy = int(self.getvalue(self.getoption("guide_dy")))
            self.guide_w = int(self.getvalue(self.getoption("guide_w")))
            self.guide_h = int(self.getvalue(self.getoption("guide_h")))

            # calculate pixels per hour used repeatedly
            self.widthPerHour = self.guide_w / self.hourSpan 

            # calculate channel span that fits into guide height
            self.channelSpan = int(self.guide_h / (self.guide_dy+self.channel_h) )
            log.debug( "channelSpan=[%d]"%self.channelSpan )

            # allocate the remainder to vertical spacing between channels
            # TODO: Fix gaps betweek rows: 
            #remainder = self.guide_h // (self.guide_dy+self.channel_h)
            remainder = 0
            log.debug('remainder = ' + str(remainder))
            self.guide_dy += (remainder / self.channelSpan)

            # initialize channel range and time range
            self.channels = self.db().getChannels()
            self.setChannel(0)
            self.setTime(datetime.now() - timedelta(minutes=30))
            self.initialized = True

        self._render()

        if not self.prevButtonInfo:
            # set focus to the first control on the screen
            if len(self.gridCells) > 0:
                self.prevFocus = self.gridCells[0].control
                self.setFocus(self.prevFocus)
            else:
                raise Exception, "No program information available."

    @catchall_ui
    def onActionHook(self, action):
        elog.debug("tvguide onActionHook: %s" % ui.toString(action))
        
        ctl = None
        try:
            ctl = self.getFocus()
        except:
            pass
        
        actionConsumed = False

        if action == ui.ACTION_MOVE_DOWN:
            actionConsumed = self._checkPageDown(self.prevFocus)
        elif action == ui.ACTION_MOVE_UP:
            actionConsumed = self._checkPageUp(self.prevFocus)
        elif action == ui.ACTION_MOVE_LEFT:
            actionConsumed = self._checkPageLeft(self.prevFocus)
        elif action == ui.ACTION_MOVE_RIGHT:
            actionConsumed = self._checkPageRight(self.prevFocus)

        if not actionConsumed and ctl:
            self.prevFocus = ctl
            
        return actionConsumed

    @catchall_ui
    @lirc_hack
    def onControlHook(self, control):
        """Method called when a control is selected/clicked."""
        log.debug("tvguide onControlHook()")

        actionConsumed = True
        
        id = self.getcontrolid(control)
        program = None
        for c in self.gridCells:
            if c.control == control:
                program = c.program
                break
        
        if program:
#            if TODO: selected program is playing now:
#                log.debug( "launching livetv" )
#                rc = livetv.showWindow(None, program)
#            else:  # bring up schedule
            log.debug( "converting program to schedule" )
            schedule = ScheduleFromProgram(program, self.translator)
            log.debug( "launching schedule details window" )

            createScheduleDialog = ScheduleDialog(
                "mythbox_schedule_dialog.xml",
                os.getcwd(),
                forceFallback=True,
                schedule=schedule,
                translator=self.translator,
                platform=self.platform,
                settings=self.settings)
            createScheduleDialog.doModal()
            
            if createScheduleDialog.shouldRefresh:
                log.debug('schedule saved')
        return actionConsumed

    def _addGridCell(self, program, cell, relX, relY, width, height):
        """ 
        Adds a control (button overlayed with a label) for a program in the guide
        
        @param program: Program
        @param cell: dict with keys ('chanid')
        @param relX: relative x position as int
        @param relY: relative y position as int
        @return: ControlLabel created for the passed in program and cell.
        @postcondition: cell[] keys are
            'chanid'    is ???, 
            'program'   is Program, 
            'nodata'    is boolean, 
            'starttime' is ???, 
            'title'     is string, 
            'start'     is int starting x coord, 
            'end'       is int ending x coord, 
            'control'   is ControlButton, 
            'label'     is ControlLabel
        """
        cell.program = program
        
        if not program:
            cell.nodata = True
            cell.starttime = None
            cell.title = self.translator.get(108) # 'No data'
            category = None
        else:
            cell.nodata = False
            cell.starttime = program.starttime()
            cell.title = program.title()
            category = program.category()
            
        cell.start = relX
        cell.end = relX + width
        
        # Create a button for navigation and hilighting. For some reason, button labels don't get truncated properly.
        cell.control = xbmcgui.ControlButton(
            relX + self.guide_x, 
            relY + self.guide_y, 
            width, 
            height, 
            label='',      # Text empty on purpose. Label overlay responsible for this
            focusTexture=util.findMediaFile('button-focus.png'), 
            noFocusTexture=util.findMediaFile(self._getTexture(category, isFocus=False)), #util.findMediaFile(self._getTexture(category, isFocus=True)),
            #textXOffset=2,
            #textYOffset=0,
            alignment=ui.ALIGN_CENTER_Y|ui.ALIGN_TRUNCATED)

        if program:
            if program.endtimeAsTime() > self.endTime:
                cell.control.setLabel(label2='>')
            if program.starttimeAsTime() < self.startTime:
                cell.control.setLabel(label= '<')

        # Create a label to hold the name of the program with insets  
        # Label text seems to get truncated correctly...
        cell.label = xbmcgui.ControlLabel(
            relX + self.guide_x + 12, # indent 12 px for bumper 
            relY + self.guide_y, 
            width - 12 - 12,          # reverse-indent 12px for bumper
            height,
            cell.title,
            font='font11',
            alignment=ui.ALIGN_CENTER_Y|ui.ALIGN_TRUNCATED)

        #        cell.label = xbmcgui.ControlFadeLabel(
        #            relX + self.guide_x + 10, # indent 5 px 
        #            relY + self.guide_y, 
        #            width - 10 - 10,          # reverse-indent 5px
        #            height)
        #            #font='font11')
        #            #alignment=ui.ALIGN_CENTER_Y|ui.ALIGN_TRUNCATED)
        #        
        #        cell.label.reset()
        #        cell.label.addLabel(str(cell.title))
        
        self.addControl(cell.control)
        self.addControl(cell.label)
        self.gridCells.append(cell)

    def _checkPageUp(self, focusControl):
        """
        Method to check and to do a page up in the tv guide.

        Returns:
        - False if no page change was done.
        - True if a page change was done.
        """
        paged = False
        if focusControl in self.topCtls:
            log.debug( "page up detected" )
            paged = True
            if self.startChan == 0:
                # wrap around
                pages = len(self.channels) // self.channelSpan
                index = len(self.channels) - (len(self.channels) % self.channelSpan) - pages
                self.setChannel(index)
            else:
                self.setChannel(self.startChan - (self.channelSpan - 1))
            self.loadGuide()

            # check if we need to fix focus
            if not self.prevFocus:
                # find the control in the bottom row where previous button's
                # start falls within start/end range of control
                chanid = self.gridCells[-1].chanid
                start = self.prevButtonInfo.start
                for c in reversed(self.gridCells):
                    if chanid == c.chanid:
                        if start >= c.start and start < c.end:
                            self.prevFocus = c.control
                            self.setFocus(self.prevFocus)
                            break
                    else:
                        break
        return paged

    def _checkPageDown(self, focusControl):
        """
        Method to check and to do a page down in the tv guide.

        Returns:
        - False if no page change was done.
        - True if a page change was done.
        """
        paged = False
        if focusControl in self.bottomCtls:
            log.debug("page down detected")
            paged = True
            if self.endChan == len(self.channels) - 1:
                # wrap around
                self.setChannel(0)
            else:
                self.setChannel(self.startChan + (self.channelSpan - 1))
            self.loadGuide()

            # check if we need to fix focus
            if not self.prevFocus:
                # find the control in the top row where previous button's start
                # falls within start/end range of control
                chanid = self.gridCells[0].chanid
                start = self.prevButtonInfo.start
                for c in self.gridCells:
                    if chanid == c.chanid:
                        if start >= c.start and start < c.end:
                            self.prevFocus = c.control
                            self.setFocus(self.prevFocus)
                            break
                    else:
                        break
        return paged

    def _checkPageLeft(self, focusControl):
        """
        Method to check and to do a page left in the tv guide.

        Returns:
        - False if no page change was done.
        - True if a page change was done.
        """
        paged = False
        if focusControl in self.leftCtls:
            log.debug("page left detected")
            paged = True
            delta = self.hourSpan - 0.5
            startTime = self.startTime - timedelta(hours=delta)
            self.setTime(startTime)
            self.loadGuide()

            # check if we need to fix focus
            if not self.prevFocus:
                chanid = self.prevButtonInfo.chanid
                found = False
                prev = None
                # find the right most program on the same channel
                for c in self.gridCells:
                    if not found and c.chanid == chanid:
                        found = True
                    elif found and c.chanid != chanid:
                        break
                    prev = c
                self.prevFocus = prev.control
                self.setFocus(self.prevFocus)
                self.prevButtonInfo = None
        return paged

    def _checkPageRight(self, focusControl):
        """
        Method to check and to do a page right in the tv guide.

        Returns:
        - False if no page change was done.
        - True if a page change was done.
        """
        paged = False
        if focusControl in self.rightCtls:
            log.debug("page right detected")
            paged = True
            delta = self.hourSpan - 0.5
            startTime = self.startTime + timedelta(hours=delta)
            self.setTime(startTime)
            self.loadGuide()

            # check if we need to fix focus
            if not self.prevFocus:
                chanid = self.prevButtonInfo.chanid
                found = False
                prev = None
                # find the left most program on the same channel
                for c in reversed(self.gridCells):
                    if not found and c.chanid == chanid:
                        found = True
                    elif found and c.chanid != chanid:
                        break
                    prev = c
                self.prevFocus = prev.control
                self.setFocus(self.prevFocus)
                self.prevButtonInfo = None
        return paged

    def _doNavigation(self):
        """
        Method to do navigation between controls and store lists of top,
        bottom, left, and right controls to detect when page changes must
        occur.
        """
        count = 0
        self.topCtls = []
        self.bottomCtls = []
        self.leftCtls = []
        self.rightCtls = []
        topChanId = None
        prevChanId = None
        prevCtl = None
        
        #
        # Loop through all buttons doing left to right, right to left, and
        # top to bottom navigation. Also keep track of top, left, and right
        # controls that are used to detect page up, left, and right.
        #
        log.debug('Gridcell cnt1 = %s' % len(self.gridCells))
        
        for c in self.gridCells:
            
            #log.debug("title=%s"%c.title)
            if not topChanId:
                topChanId = c.chanid
                
            if c.chanid == topChanId:
                # first row of controls are top controls
                self.topCtls.append(c.control)
                #log.debug("top ctl=%s"%c.control)

            # do left to right and right to left navigation
            if not prevChanId:
                prevChanId = c.chanid
            elif prevChanId != c.chanid:
                # changed channel rows so previous control is a control on right edge
                self.rightCtls.append(prevCtl)
                prevCtl = None
                prevChanId = c.chanid
                
            if prevCtl:
                prevCtl.controlRight(c.control)
                c.control.controlLeft(prevCtl)
                prevCtl = c.control
                
            if not prevCtl:
                # control not set so this must be a control on left edge
                self.leftCtls.append(c.control)
                prevCtl = c.control

            # now find the appropriate control below current one
            chanid = None
            found = False
            for c2 in self.gridCells:
                if not found and c2.control == c.control:
                    found = True
                elif found and not chanid and c2.chanid != c.chanid:
                    chanid = c2.chanid
                    
                if found and chanid and chanid == c2.chanid:
                    if c.start >= c2.start and c.start < c2.end:
                        c.control.controlDown(c2.control)
                        #log.debug("%s VVV %s"%(c.title, c2.title))
                        count += 1
                        break
                elif found and chanid and chanid != c2.chanid:
                    break
                
        log.debug("down count=%d"%count)
        count = 0
        
        log.debug('Gridcell cnt2 = %s' % len(self.gridCells))
        #cells = list(self.gridCells)
        #cells = cells.reverse()
        bottomChanId = None

        #log.debug('Gridcell cnt3 = %s' % len(cells))
        
        #
        # Loop through all buttons in reverse to do bottom to top navigation.
        #
        for c in reversed(self.gridCells):
            
            #log.debug("title=%s"%c.title)
            if not bottomChanId:
                bottomChanId = c.chanid
                
            if c.chanid == bottomChanId:
                # first row of controls are bottom controls
                self.bottomCtls.append(c.control)
                #log.debug("bottom ctl=%s"%c.control)

            # now find the control that is above the current one
            chanid = None
            found = False
            
            for c2 in reversed(self.gridCells):
                if not found and c2.control == c.control:
                    found = True
                elif found and not chanid and c2.chanid != c.chanid:
                    chanid = c2.chanid
                    
                if found and chanid and chanid == c2.chanid:
                    if c.start >= c2.start and c.start < c2.end:
                        c.control.controlUp(c2.control)
                        #log.debug("%s ^^^ %s"%(c.title, c2.title))
                        count += 1
                        break
                elif found and chanid and chanid != c2.chanid:
                    break
        log.debug( "up count=%d"%count )

        # if we have any controls, then the very last control on right edge
        # was missed in first loop (right controls are detected by row changes
        # but the last row quits the loop before detecting the control)
        if len(self.gridCells) > 0:
            # Note: This grabs last control from the reverse list of controls.
            self.rightCtls.append(self.gridCells[-1].control)
        #log.debug("right ctl=%s"%cells[0].control)

        log.debug("top count    = %d" % len(self.topCtls))
        log.debug("bottom count = %d" % len(self.bottomCtls))
        log.debug("left count   = %d" % len(self.leftCtls))
        log.debug("right count  = %d" % len(self.rightCtls))

    def _getTexture(self, category, isFocus):
        """
        Method to figure out name of texture (png file) to use for the passed category.
        """
        # determine color
        if not category:
            color = "shade"
        else:
            if category in self.categoryColors:
                color = self.categoryColors[category]
            else:
                color = "shade"

        # determine alpha value
        if isFocus:
            alpha = "50"
        else:
            alpha = "25"

        # build texture file name
        return "%s_%s.png"%(color,alpha)

    @ui_locked
    def _render(self):
        """
        Method to draw all the dynamic controls that represent the program
        guide information.
        """
        title = self.translator.get(107)
        title += ": %s - %s" % (self.startTime.strftime("%x %X"), self.endTime.strftime("%x %X"))
        self.controls['title'].control.setLabel(title)
        self._renderChannels()
        self._renderTime()
        self._renderPrograms()
        self._doNavigation()

    def _renderChannels(self):
        """Method to draw the channel labels. """
        
        # free current channel cells
        for c in self.channelCells:
            if c.icon != None:
                self.removeControl(c.icon)
            if c.label != None:
                self.removeControl(c.label)
            if c.shade != None:
                self.removeControl(c.shade)
            del c
        self.channelCells = []
        
        x = self.channel_x
        y = self.guide_y
        h = (self.guide_h - self.channelSpan * self.guide_dy) / self.channelSpan
        iconW = h
        labelW = self.channel_w - iconW - self.guide_dx
        
        for i in range(self.startChan, self.endChan + 1):
            c = ChannelCell()
            
            # create shade image around channel label/icon
            c.shade = xbmcgui.ControlImage(
                x, 
                y, 
                self.channel_w, 
                h, 
                util.findMediaFile("shade_50.png"))
            
            self.addControl(c.shade)

            # create label control
            labelText = "%s %s" % (self.channels[i].getChannelNumber(), self.channels[i].getCallSign())
            c.label = xbmcgui.ControlLabel(
                x + iconW + self.channel_dx, 
                y, 
                labelW, 
                h,
                labelText, 
                self.getoption("channel_font"),
                alignment=ui.ALIGN_CENTER_Y)
            
            self.addControl(c.label)

            # create channel icon image if icon exists
            shost = str(self.settings.getMythTvHost())
            file = os.path.join(ui.picBase, 'channels', str(self.channels[i].getChannelNumber()) + ui.picType)
            
            if not os.path.exists(file):
                try:
                    file = self.iconCache.findFile(self.channels[i], shost)
                except:
                    log.debug(" renderChannels: nothing assigned to file")
                
            log.debug("channel icon file = %s"%file)
            if file:
                c.icon = xbmcgui.ControlImage(x, y, iconW, h, file)
                self.addControl(c.icon)

            self.channelCells.append(c)
            y += h + self.guide_dy
    
    @timed
    @inject_db
    def _renderPrograms(self):
        """
        Method to draw the program buttons.  This manufactures buttons for missing guide data.
        """
        
        programs = self.db().getProgramListings(
            self.startTime, 
            self.endTime,
            self.channels[self.startChan].getChannelId(),
            self.channels[self.endChan].getChannelId())
        
        log.debug("Num programs = %s" % len(programs))

        # dealloc existing grid cells...
        for cell in self.gridCells:
            self.removeControl(cell.control)
            del cell.control
            self.removeControl(cell.label)
            del cell.label
            del cell
        self.gridCells = []

        self.widthPerHour = self.guide_w / self.hourSpan 
        chanH = (self.guide_h - self.channelSpan * self.guide_dy) / self.channelSpan

        # Loop through each channel filling the tv guide area with cells.
        for i in range(self.startChan, self.endChan + 1):
            noData = False
            chanX = 0
            chanY = (i - self.startChan) * (chanH + self.guide_dy)
            chanid = self.channels[i].getChannelId()
        
            # loop until we've filled the row for the channel
            while chanX < self.guide_w:
                cell = ProgramCell()
                cell.chanid = chanid
                p = None
                if not noData:
                    # find the next program for the channel - this assumes
                    # programs are sorted in ascending time order for the channel
                    for prog in programs:
                        if prog.getChannelId() == chanid:
                            p = prog
                            programs.remove(prog)
                            break
                if not p:
                    # no program found - create a no data control for the rest of the row
                    noData = True
                    w = self.guide_w - chanX
                    self._addGridCell(
                        program=None,
                        cell=cell, 
                        relX=chanX, 
                        relY=chanY, 
                        width=w, 
                        height=chanH)
                    chanX += w
                else:
                    # found a program but we don't know if it starts at the current spot in the row for the channel

                    # trunc start time
                    start = p.starttimeAsTime()
                    if start < self.startTime:
                        start = self.startTime

                    # trunc end time
                    end = p.endtimeAsTime()
                    if end > self.endTime:
                        end = self.endTime

                    # calculate x coord and width of label
                    start = start - self.startTime
                    progX = start.seconds / (60.0*60.0) * self.widthPerHour
                    
                    end = end - self.startTime
                    progEndX = end.seconds / (60.0*60.0) * self.widthPerHour
                    progW = progEndX - progX

                    log.debug("cell startx=%s endx=%s"%(start,end))
                    
                    # check if we need no data before control 
                    if progX != chanX:
                        self._addGridCell(
                            program=None,
                            cell=cell,    # TODO: Doesn't make sense why setting info for 'no data' cell to cell
                            relX=chanX, 
                            relY=chanY,
                            width=(progX - chanX), 
                            height=chanH)
                        
                        chanX = progX
                        cell = ProgramCell()
                        cell.chanid = chanid

                    # add the control for the program
                    self._addGridCell(
                        program=p,
                        cell=cell,
                        relX=progX, 
                        relY=chanY, 
                        width=progW, 
                        height=chanH)
                    chanX += progW

    def _renderTime(self):
        """
        Method to draw the time labels for the tv guide.
        """
        doInit = False
        if len(self.timeLabels) == 0:
            doInit = True

        numCols = int(self.hourSpan * 2)
        x = self.guide_x
        y = self.time_y
        h = self.time_h
        w = (self.guide_w - numCols * self.guide_dx) / numCols
        t = self.startTime
        lastDay = t.day
        i = 0
        log.debug("numCols=%d guide_w=%d"%(numCols, self.guide_w))
        
        while i < numCols:
            if doInit:
                log.debug("time label: x=%d y=%d w=%d h=%d"%(x, y, w, h))
                c = xbmcgui.ControlLabel(x, y, w, h, "", self.getoption("time_font"))
                self.timeLabels.append(c)
                self.addControl(c)

            label = t.strftime("%I").lstrip('0') + t.strftime(":%M %p") 
            if i == 0:
                label = t.strftime("%a ") + label
                
            if t.day != lastDay:
                label += "+1"
                
            log.debug("time label = %s" % label)
            
            self.timeLabels[i].setLabel(label)
            t += timedelta(minutes=30)
            i += 1
            x = x + w + self.guide_dx
            lastDay = t.day
        
    def setTime(self, startTime):
        """
        Method to change the starting time of the tv guide.  This is used
        to change pages horizontally.
        """
        self.startTime = startTime - timedelta(seconds=startTime.second, microseconds=startTime.microsecond)
        min = self.startTime.minute
        if min != 0:
            if min > 30:
                delta = 60 - min
            else:
                delta = 30 - min
            self.startTime = self.startTime + timedelta(minutes=delta)
        self.endTime = self.startTime + timedelta(hours=self.hourSpan)
        log.debug("startTime = %s endTime = %s" % (self.startTime, self.endTime))
        
    def setChannel(self, chanIndex):
        """
        Method to change the starting channel index of the tv guide.
        This is used to change pages vertically.
        """
        self.startChan = chanIndex
        if self.startChan < 0:
            self.startChan = 0
        self.endChan = self.startChan + self.channelSpan - 1
        if self.endChan > len(self.channels)-1:
            self.endChan = len(self.channels)-1
        log.debug("start channel = %s" % self.channels[self.startChan].getChannelNumber())
        log.debug("end channel = %s" % self.channels[self.endChan].getChannelNumber())