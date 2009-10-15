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
import odict
import os
import recordingdetails
import sre
import string
import ui
import xbmcgui

from time import strftime, strptime
from ui import window_busy
from util import catchall_ui, run_async, ui_locked, lirc_hack
from injected import inject_conn, inject_db

log = logging.getLogger('mythtv.ui')
elog = logging.getLogger('mythbox.event')

def showWindow(progressDialog, settings, translator, mythThumbnailCache, platform):
    win = Window(settings=settings, translator=translator, mythThumbnailCache=mythThumbnailCache, platform=platform)
    if progressDialog:
        progressDialog.close()
    win.doModal()
    del win

# =============================================================================
class Window(ui.LegacyBaseWindow):
    
    VIEW_BY_MIN         = 0     # must be smallest sequential value
    VIEW_BY_DATE_ASC    = 1
    VIEW_BY_DATE_DESC   = 2
    VIEW_BY_TITLE_ASC   = 3
    VIEW_BY_TITLE_DESC  = 4
    VIEW_BY_MAX         = 5     # must be largest sequential value

    def __init__(self, *args, **kwargs):
        """
        @keyword settings: MythSettings
        @keyword translator: Translator
        @keyword mythThumbnailCache: FileCache(MythThumbnailResolver)
        """
        ui.LegacyBaseWindow.__init__(self, *args, **kwargs)
        self.platform = kwargs['platform']
        self.mythThumbnailCache = kwargs['mythThumbnailCache']
        self.recordings = []
        self.focusControl = None
        self.show_recording_groups = True
        self.updateEpisodesOnScroll = True
        try:
            self.recording_group = self.settings.get("recorded_default_group")
        except:
            self.recording_group = "default"
        
        self.current_title = "All Shows (x shows)"
        self.recording_groups = []
        self.show_titles = []

        self.viewByLabel = { 
            self.VIEW_BY_DATE_ASC: 38,
            self.VIEW_BY_TITLE_ASC: 39,
            self.VIEW_BY_DATE_DESC: 69,
            self.VIEW_BY_TITLE_DESC: 70 
        }

        try:
            self.viewBy = int(self.settings.get("recorded_view_by"))
        except IndexError:
            self.viewBy = self.VIEW_BY_DATE_DESC
            self.settings.put("recorded_view_by", "%d"%self.viewBy, shouldCreate=1)
        self.loadskin("recordedshows.xml")
        self._populate_recording_groups_combobox()
        self.preCacheThumbnails()  # NOTE: async

    @run_async
    def preCacheThumbnails(self):
        for recording in self.recordings:
            try:
                self.mythThumbnailCache.get(recording)
            except:
                log.exception('Thumbnail generation for %s failed' % recording)
        
    @ui_locked
    @inject_db
    def _populate_recording_groups_combobox(self):
        log.debug('Window._populate_recording_groups_combobox()')
        
        if self.show_recording_groups:        
            self.recording_groups = self.db().getRecordingGroups()
            log.debug ("Num Recording Groups = %d" % len(self.recording_groups))
            combobox = self.controls["recgroup_list"].control

            cnt = 0
            current_index = 0
            recg = self.recording_group

            log.debug(recg)
            
            combobox.reset()
            try:
                combobox.setPageControlVisible(False)
            except:
                pass
            
            for r in self.recording_groups:
                if string.upper(r[0]) == string.upper(recg):
                    current_index = cnt
                cnt += 1
                combobox.addItem("%s" % (r[0]))
                combobox.selectItem(current_index)
        else:
            try:
                combobox = self.controls["recgroup_list"].control
                combobox.setVisible(False)
            except:
                log.exception("Unable to remove recording groups combobox")
                
        self._populate_episode_groups_combobox()

    @inject_db
    def _populate_episode_groups_combobox(self):
        recg = self.recording_group # self.recording_group[:str(self.recording_group).rfind("(")-1]
        self.show_titles = self.db().getRecordingTitles(recg)
        log.debug ("Num programs found for recording group %s: %s" % (recg, len(self.show_titles)))
        combobox = self.controls["show_list"].control

        ## if rec group has no shows swap back to first group and reload
        if len(self.show_titles) == 1:
            self.recording_group = self.recording_groups[1][0]
            self._populate_recording_groups_combobox()
            return

        cnt = 0
        curIdx = 0
        curt = string.upper(self.current_title[:str(self.current_title).rfind("(")-1])

        log.debug(curt)        
        try:
            combobox.reset()
            try:
                combobox.setPageControlVisible(False)
            except:
                pass
      
            for r in self.show_titles:
                if string.upper(r[0]) == curt:
                    curIdx = cnt
                cnt += 1
                title = r[0]
                combobox.addItem("%s (%s shows)" % (title, r[1]))
            combobox.selectItem(curIdx)
            xbmcgui.unlock()
        except:
            log.exception('_populate_episode_groups_combobox')
        self._populate_episodes_listbox()
    
    @inject_conn
    def _populate_episodes_listbox(self):
        log.debug('Window._populate_episodes_listbox()')
        curt = self.current_title[:str(self.current_title).rfind("(")-1]
        recg = self.recording_group # self.recording_group[:str(self.recording_group).rfind("(")-1]
        log.debug ("%s - %s" % (recg, curt))
        self.recordings = self.conn().getRecordings(recg, curt)
        log.debug("%s Recordings Found for Title %s" % (len(self.recordings), curt))

        ## If current title has no recordings then swap back to all shows (current title has been deleted)
        if len(self.recordings) == 0 and string.upper(curt) != "ALL SHOWS":
            self.current_title = "All Shows (x shows)"
            self._populate_episode_groups_combobox()
            return

        def compareDateAsc(x, y):
            if x.starttime() == y.starttime():
                return cmp(x.endtime(), y.endtime())
            else:
                return cmp(x.starttime(), y.starttime())
        
        def compareDateDesc(y, x):
            if x.starttime() == y.starttime():
                return cmp(x.endtime(), y.endtime())
            else:
                return cmp(x.starttime(), y.starttime())
        
        def compareTitleAsc(x, y):
            if x.title() == y.title():
                return cmp(x.starttime(), y.starttime())
            else:
                return cmp(x.title(), y.title())
        
        def compareTitleDesc(y, x):
            if x.title() == y.title():
                return cmp(x.starttime(), y.starttime())
            else:
                return cmp(x.title(), y.title())

        try:   
            if self.viewBy == self.VIEW_BY_DATE_ASC:
                self.recordings.sort(compareDateAsc)
            elif self.viewBy == self.VIEW_BY_DATE_DESC:
                self.recordings.sort(compareDateDesc)
            elif self.viewBy == self.VIEW_BY_TITLE_ASC:
                self.recordings.sort(compareTitleAsc)
            elif self.viewBy == self.VIEW_BY_TITLE_DESC:
                self.recordings.sort(compareTitleDesc)
            ctl = self.controls["episode_list"].control
        except:
            log.exception('_populate_episodes_listbox/0')
            raise
        
        self.controls["view_by"].control.setLabel(self.translator.get(self.viewByLabel[self.viewBy]))

        ctl.reset()
        for r in self.recordings:
            ctl.addItem(self._build_episode_text(r))
        if len(self.recordings) > 0:
            self._render_episode_details(0)

    def _build_episode_text(self, program):
        start = strptime(program.starttime(), "%Y%m%d%H%M%S")
        text = strftime("%m/%d %I:%M %p", start) + "   "
        if program.title():
            text += program.title()
        if program.subtitle() and not sre.match( '^\s+$', program.subtitle()):
            text += " - " + program.subtitle()
        return text

    @catchall_ui
    @lirc_hack
    def onActionHook(self, action):
        elog.debug("onActionHook: %s" % ui.toString(action))
  
        # Remember last focused control
        try:
            self.focusControl = self.getFocus()
        except:
            pass
        
        if action in (ui.ACTION_PREVIOUS_MENU, ui.ACTION_PARENT_DIR):
            self.settings.save()
        
        return False

    @catchall_ui
    @ui_locked
    def onActionPostHook(self, action):
        elog.debug("onActionPostHook: %s" % ui.toString(action))
        
        # check if the action was to move up or down
        if action in (ui.ACTION_MOVE_UP, ui.ACTION_MOVE_DOWN, ui.ACTION_SCROLL_UP, ui.ACTION_SCROLL_DOWN):
            
            # check if the control in focus is the show list
            id = self.getcontrolid(self.focusControl)
            
            if id == "recgroup_list":
                if self.updateEpisodesOnScroll:
                    
                    # give gui time to update
                    #time.sleep(0.10)
                    
                    # Update episode list with new shows
                    rg = self.recording_groups[self.focusControl.getSelectedPosition()]
                    self.recording_group = "%s" % rg[0]
                    self.settings.put("recorded_default_group", "%s"%self.recording_group, shouldCreate=1)
                    self.current_title = "All Shows (0 shows)"
                    self._populate_episode_groups_combobox()
                    
            elif id == "episode_list":
                # give gui time to update
                #time.sleep(0.10)
                
                # get selected show and populate details
                self._render_episode_details(self.focusControl.getSelectedPosition())
                
            elif id == "show_list":
                if self.updateEpisodesOnScroll:
                    # give gui time to update
                    #time.sleep(0.10)
                    
                    # Update episode list with new shows
                    ct = self.show_titles[self.focusControl.getSelectedPosition()]
                    self.current_title = "%s (%s shows)" % (ct[0], ct[1])
                    self._populate_episodes_listbox()

    @catchall_ui
    @lirc_hack
    def onControlHook(self, control):
        id = self.getcontrolid(control)
        log.debug("onControlHook: %s" % id)

        if id == "view_by":
            self.viewBySelected()
        elif id == "episode_list":
            self._showRecordingDetails(control)
        elif id == "recgroup_list":
            if not self.updateEpisodesOnScroll:            
                rg = self.recording_groups[self.focusControl.getSelectedPosition()]
                self.recording_group = "%s" % (rg[0])
                self.current_title = "All Shows (0 shows)"
                self._populate_episode_groups_combobox()
        elif id == "show_list":
            if not self.updateEpisodesOnScroll:
                ct = self.show_titles[self.focusControl.getSelectedPosition()]
                self.current_title = "%s (%s shows)" % (ct[0], ct[1])
                self._populate_episodes_listbox()
        elif id == "refresh":
            self._populate_recording_groups_combobox()
        else:
            return False
        return True

    def _render_episode_details(self, list_index):
        if list_index < len(self.recordings):
            program = self.recordings[list_index]
            self.controls['show_title'].control.reset()
            self.controls['show_title'].control.addLabel(program.fullTitle())
            self.controls['show_air_date'].control.setLabel(program.formattedAirDateTime())
            self.controls['show_channel'].control.setLabel(program.formattedChannel())
            self.controls['show_orig_air'].control.setLabel(program.formattedOrigAirDate())
            self.controls['show_descr'].control.reset()
            self.controls['show_descr'].control.addLabel(program.formattedDescription())

    
    def _showRecordingDetails(self, programListBox):
        pos = programListBox.getSelectedPosition()
        log.debug('Showing details for show at index %s' % pos)
        
        if pos < len(self.recordings):
            
            win = recordingdetails.RecordingDetailsWindow(
                "mythbox_recording_details.xml", 
                os.getcwd(), 
                forceFallback=True,
                program=self.recordings[pos],
                settings=self.settings,
                translator=self.translator,
                platform=self.platform,
                mythThumbnailCache=self.mythThumbnailCache)
            
            win.doModal()
            
            # refresh list if show was deleted - fixup instead of requerying backend
            if win.isDeleted:
                del self.recordings[pos]
                programListBox.reset()
                for r in self.recordings:
                    programListBox.addItem(self._build_episode_text(r))
                try:
                    programListBox.setSelectedPosition(pos)
                except:
                    pass
            
            del win   

    def viewBySelected(self):
        # switch to next view by
        self.viewBy += 1
        if self.viewBy >= self.VIEW_BY_MAX:
            self.viewBy = self.VIEW_BY_MIN+1

        # store the setting change
        self.settings.put("recorded_view_by", "%d"%self.viewBy, shouldCreate=1)

        # refresh the listing
        self._populate_episodes_listbox()

# ==============================================================================
class RecordingsWindow(ui.BaseWindow):
    """
    All Groups | Programs By Recording Group v
    
    All Programs | Programs By Title v
    
    ListBox of Programs 
    """
    
    GROUP_ALL = "All Groups"
    GROUP_DEFAULT = "Default"
    GROUP_LIVETV = "Live TV"
    TITLE_ALL = "All Recordings"
    
    def __init__(self, *args, **kwargs):
        ui.BaseWindow.__init__(self, *args, **kwargs)
        
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
        self.platform = kwargs['platform']
        self.fanArt = kwargs['fanArt']
        self.mythChannelIconCache = kwargs['cachesByName']['mythChannelIconCache']
        self.mythThumbnailCache = kwargs['cachesByName']['mythThumbnailCache']

        self.activeGroup = self.GROUP_ALL
        self.activeTitle = self.TITLE_ALL
        
        self.programs = []                       # [RecordedProgram]
        self.activePrograms = []                 # [RecordedProgram]
        self.programsByListItem = odict.odict()  # {ListItem:RecordedProgram}
        self.closed = False
        
    @catchall_ui
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.refreshButton = self.getControl(250)
            self.groupButton = self.getControl(601)
            self.titleButton = self.getControl(602)
            self.programsListBox = self.getControl(600)
            self.refresh()

    def onFocus(self, controlId):
        pass
        
    @catchall_ui
    @lirc_hack    
    def onClick(self, controlId):
        source = self.getControl(controlId)
        if source == self.programsListBox: 
            self.goRecordingDetails()
        elif source == self.refreshButton:
            self.refresh()
                         
    @catchall_ui
    @lirc_hack            
    def onAction(self, action):
        if action.getId() in (ui.ACTION_PREVIOUS_MENU, ui.ACTION_PARENT_DIR):
            self.closed = True
            self.close()
        
#    def _getProgramsByGroup(self, programs):
#        programsByGroup = {}
#        programsByGroup[self.GROUP_ALL] = self.programs[:]
#        
#        for p in programs:
#            group = p.getRecordingGroup()
#            if programsByGroup.has_key(group):
#                programsByGroup[group].append(p)
#            else: 
#                programsByGroup[group] = [p]
#        return programsByGroup
#
#    def _getProgramsByTitle(self, programs):
#        programsByGroup = {}
#        programsByGroup[self.GROUP_ALL] = programs[:]
#        
#        for p in programs:
#            group = p.getRecordingGroup()
#            if programsByGroup.has_key(group):
#                programsByGroup[group].append(p)
#            else: 
#                programsByGroup[group] = [p]
#        return programsByGroup

    @window_busy
    @inject_conn
    def refresh(self):
        self.programs = self.conn().getAllRecordings()
        self.render()
        
    @window_busy
    def render(self):
        log.debug('Rendering....')
        self.programsListBox.reset()
        self.renderGroup()
        self.renderTitle()
        self.renderPrograms()
        
    def renderGroup(self):
        self.setWindowProperty('activeGroup', self.activeGroup)

    def renderTitle(self):
        self.setWindowProperty('activeTitle', self.activeTitle)

    def renderPrograms(self):
        del self.activePrograms[:]
        for p in self.programs:
            if self.activeGroup in (self.GROUP_ALL, p.getRecordingGroup()):
                if self.activeTitle in (self.TITLE_ALL, p.title()):
                    self.activePrograms.append(p)

        self.programsByListItem.clear()
        for i, ap in enumerate(self.activePrograms):
            listItem = xbmcgui.ListItem('Row %d' % i)
            self.setListItemProperty(listItem, 'title', ap.title())
            # TODO: Refactor to use addItems(...)
            self.programsListBox.addItem(listItem)
            self.programsByListItem[listItem] = ap

    def goRecordingDetails(self):
        selectedItem = self.programsListBox.getSelectedItem()
        if not selectedItem:
            return
        
        selectedProgram = self.programsByListItem[selectedItem]
        if not selectedProgram:
            return
        
        win = recordingdetails.RecordingDetailsWindow(
            "mythbox_recording_details.xml", 
            os.getcwd(), 
            forceFallback=True,
            program=selectedProgram,
            settings=self.settings,
            translator=self.translator,
            platform=self.platform,
            mythThumbnailCache=self.mythThumbnailCache)
        win.doModal()

        if win.isDeleted:
            self.programs.remove(selectedProgram)
            self.render()
        del win   

#    @run_async
#    @timed
#    @catchall
#    def renderPosters(self):
#        for i, (program, row) in enumerate(self.listItemsByProgram.items()):
#            if not self.closed:
#                # Lookup poster if available
#                log.debug('Poster %d/%d for %s' % (i+1, len(self.listItemsByProgram), program.title()))
#                posterPath = self.fanArt.getRandomPoster(program)
#                if posterPath:
#                    self.setListItemProperty(row, 'poster', posterPath)
#                elif self.channelsById[program.getChannelId()].getIconPath():
#                    self.setListItemProperty(row, 'poster', self.mythChannelIconCache.get(self.channelsById[program.getChannelId()]))
