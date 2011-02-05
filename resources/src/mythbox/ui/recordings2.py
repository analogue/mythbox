#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2011 analogue@yahoo.com
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
import time
import xbmc
import xbmcgui
import mythbox.msg as m

from mythbox.mythtv.conn import inject_conn
from mythbox.ui.recordingdetails import RecordingDetailsWindow
from mythbox.ui.toolkit import window_busy, BaseWindow, Action
from mythbox.util import catchall_ui, run_async, lirc_hack, timed, catchall, ui_locked, ui_locked2, coalesce,\
    safe_str
from mythbox.util import CyclingBidiIterator

log = logging.getLogger('mythbox.ui')

ID_GROUPS_LISTBOX = 700
ID_PROGRAMS_LISTBOX = 600
ID_REFRESH_BUTTON = 250
ID_SORT_BY_BUTTON = 251
ID_SORT_ASCENDING_TOGGLE = 252
ID_RECORDING_GROUP_BUTTON = 253

SORT_BY = odict.odict([
    ('Date',           {'translation_id': m.DATE, 'sorter' : lambda x: x.starttimeAsTime() }), 
    ('Title',          {'translation_id': m.TITLE, 'sorter' : lambda x: '%s%s' % (x.title(), x.originalAirDate())}), 
    ('Orig. Air Date', {'translation_id': m.ORIG_AIR_DATE, 'sorter' : lambda x: x.originalAirDate()})])


class Group(object):
    
    def __init__(self, title=None):
        self.title = title
        self.programs = []
        self.listItems = []
        self.programsByListItem = odict.odict()
        self.listItemsByProgram = odict.odict()
        
    def add(self, program):
        if self.title is None:
            self.title = program.title()
        self.programs.append(program)
        
    def remove(self, program):
        self.programs.remove(program)


    def __str__(self):
        s = """title = %s
        num programs = %d 
        num listiems = %d
        num li map   = %d 
        num pr map   = %d""" % (safe_str(self.title), len(self.programs), len(self.listItems), len(self.programsByListItem), len(self.listItemsByProgram))
        return s
    
class RecordingsWindow(BaseWindow):
        
    def __init__(self, *args, **kwargs):
        BaseWindow.__init__(self, *args, **kwargs)
        [setattr(self,k,v) for k,v in kwargs.iteritems()]
        [setattr(self,k,v) for k,v in self.cachesByName.iteritems()]

        self.programs = []                       # [RecordedProgram]
        self.closed = False
        
        self.lastSelected = int(self.settings.get('recordings_last_selected'))
        self.sortBy = self.settings.get('recordings_sort_by')
        self.sortAscending = self.settings.getBoolean('recordings_sort_ascending')
        self.group = self.settings.get('recordings_recording_group')
        self.activeRenderToken = None
        self.groupsByTitle = odict.odict()       # {unicode:Group}
        self.activeGroup = None
        self.allGroupTitle = self.translator.get(m.ALL_RECORDINGS)
        
    @catchall_ui
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.groupsListbox = self.getControl(ID_GROUPS_LISTBOX)
            self.programsListBox = self.getControl(ID_PROGRAMS_LISTBOX)
            self.refresh()

    def onFocus(self, controlId):
        self.lastFocusId = controlId
        if controlId == ID_GROUPS_LISTBOX:
            log.warn('groups focus')
        else:
            log.warn('uncaught focus %s' % controlId)
            
    @catchall_ui
    @lirc_hack    
    def onClick(self, controlId):
        if controlId == ID_GROUPS_LISTBOX:
            log.warn('groups clicked!')
        elif controlId == ID_PROGRAMS_LISTBOX: 
            self.goRecordingDetails()
        elif controlId == ID_REFRESH_BUTTON:
            self.lastSelected = self.programsListBox.getSelectedPosition()
            self.refresh()
        elif controlId == ID_SORT_BY_BUTTON:
            keys = SORT_BY.keys()
            self.sortBy = keys[(keys.index(self.sortBy) + 1) % len(keys)] 
            self.applySort()
        elif controlId == ID_SORT_ASCENDING_TOGGLE:
            self.sortAscending = not self.sortAscending
            self.applySort()
        else:
            log.warn('uncaught onClick %s' % controlId)
                             
    @catchall_ui
    @lirc_hack            
    def onAction(self, action):
        if action.getId() in (Action.PREVIOUS_MENU, Action.PARENT_DIR):
            self.closed = True
            self.settings.put('recordings_last_selected', '%d'%self.programsListBox.getSelectedPosition())
            self.settings.put('recordings_sort_by', self.sortBy)
            self.settings.put('recordings_sort_ascending', '%s' % self.sortAscending)
            self.settings.put('recordings_recording_group', self.group)
            self.close()
        elif action.getId() in (Action.UP, Action.DOWN, Action.PAGE_UP, Action.PAGE_DOWN, Action.HOME, Action.END):
            if self.lastFocusId == ID_GROUPS_LISTBOX:
                log.warn('groups select!')
                self.onGroupSelect()
        elif action.getId() == ID_GROUPS_LISTBOX:
            log.warn('groups action!')
        else:
            log.warn('uncaught action id %s' % action.getId())
    
    def onGroupSelect(self):
        self.activeGroup = self.groupsByTitle[self.groupsListbox.getSelectedItem().getProperty('title')]
        self.renderPrograms()
        self.activeRenderToken = time.clock()
        self.renderPosters(self.activeRenderToken)
        self.renderEpisodeColumn(self.activeRenderToken)
        
    @run_async
    @coalesce
    def preCacheThumbnails(self):
        if self.programs:
            log.debug('Precaching %d thumbnails' % len(self.programs))
            for program in self.programs[:]:
                if self.closed or xbmc.abortRequested: 
                    return
                try:
                    self.mythThumbnailCache.get(program)
                except:
                    log.exception('Thumbnail generation for recording %s failed' % safe_str(program.fullTitle()))

    @run_async
    @coalesce
    def preCacheCommBreaks(self):
        if self.programs:
            log.debug('Precaching %d comm breaks' % len(self.programs))
            for program in self.programs[:]:
                if self.closed or xbmc.abortRequested: 
                    return
                try:
                    if program.isCommFlagged():
                        #program.getCommercials()
                        program.getFrameRate()
                except:
                    log.exception('Comm break caching for recording %s failed' % safe_str(program.fullTitle()))

    @window_busy
    @inject_conn
    def refresh(self):
        self.programs = self.conn().getAllRecordings()
        if not self.programs:
            xbmcgui.Dialog().ok(self.translator.get(m.INFO), self.translator.get(m.NO_RECORDINGS_FOUND))
            self.close()
            return
        
        # TODO: Recording group filter
        #self.programs = filter(lambda p: p.getRecordingGroup() == self.group, self.programs)
        
        # NOTE: No aggressive caching on windows since spawning the ffmpeg subprocess
        #       launches an annoying window
        self.programs.sort(key=SORT_BY[self.sortBy]['sorter'], reverse=self.sortAscending)
        self.preCacheThumbnails()
        
        if self.platform.getName() in ('unix','mac') and self.settings.isAggressiveCaching(): 
            self.preCacheCommBreaks()
            
        self.render()
    
    def applySort(self):
        self.programs.sort(key=SORT_BY[self.sortBy]['sorter'], reverse=self.sortAscending)
        self.render()
        
    @ui_locked
    def render(self):
        log.debug('Rendering....')
        self.renderNav()
        self.renderGroups()
        #self.renderPrograms()
        #self.activeRenderToken = time.clock()
        #self.renderPosters(self.activeRenderToken)
        #self.renderEpisodeColumn(self.activeRenderToken)
        
    def renderNav(self):
        self.setWindowProperty('sortBy', self.translator.get(m.SORT) + ': ' + self.translator.get(SORT_BY[self.sortBy]['translation_id']))
        self.setWindowProperty('sortAscending', ['false', 'true'][self.sortAscending])

    def renderGroups(self):
        self.groupsByTitle.clear()
        self.groupsByTitle[self.allGroupTitle] = allGroup = Group(self.allGroupTitle)
        for p in self.programs:
            if not p.title() in self.groupsByTitle:
                self.groupsByTitle[p.title()] = Group()
            self.groupsByTitle[p.title()].add(p)
            allGroup.add(p)
            
        for title,group in self.groupsByTitle.iteritems():
            group.listItem = xbmcgui.ListItem()
            self.setListItemProperty(group.listItem, 'title', title)
            self.setListItemProperty(group.listItem, 'date', str(len(group.programs)))  # TODO: rename 'date'
            self.groupsListbox.addItem(group.listItem)
        
        self.groupsListbox.selectItem(0)
        self.onGroupSelect()
        
    @timed
    def renderPrograms(self):        
        self.activeGroup.listItems = []
        self.activeGroup.programsByListItem = odict.odict()
        self.activeGroup.listItemsByProgram = odict.odict()
        
        @timed 
        def constructorTime(): 
            for p in self.activeGroup.programs:
                listItem = xbmcgui.ListItem()
                self.activeGroup.listItems.append(listItem)
                self.activeGroup.programsByListItem[listItem] = p
                self.activeGroup.listItemsByProgram[p] = listItem
        
        @timed 
        @ui_locked2
        def propertyTime(): 
            for i, p in enumerate(self.activeGroup.programs):
                try:
                    listItem = self.activeGroup.listItems[i]
                    self.setListItemProperty(listItem, 'title', p.fullTitle())
                    self.setListItemProperty(listItem, 'date', p.formattedAirDate())
                    self.setListItemProperty(listItem, 'time', p.formattedStartTime())
                    self.setListItemProperty(listItem, 'index', str(i+1))
                    if self.fanArt.hasPosters(p):
                        p.needsPoster = False
                        self.lookupPoster(listItem, p)
                    else:
                        p.needsPoster = True
                        self.setListItemProperty(listItem, 'poster', 'loading.gif')
                except:
                    log.exception('Program = %s' % safe_str(p.fullTitle()))
        
        @timed
        def othertime():
            self.programsListBox.reset()
            self.programsListBox.addItems(self.activeGroup.listItems)
            self.programsListBox.selectItem(self.lastSelected)

        constructorTime()
        propertyTime()
        othertime()

    def lookupPoster(self, listItem, p):
        posterPath = self.fanArt.getRandomPoster(p)
        if not posterPath:
            posterPath = self.mythThumbnailCache.get(p)
            if not posterPath:
                posterPath = 'mythbox-logo.png'
        self.setListItemProperty(listItem, 'poster', posterPath)

    def renderProgramDeleted2(self, deletedProgram, selectionIndex):
        title = deletedProgram.title()
        self.programs.remove(deletedProgram)
        for group in [self.groupsByTitle[title], self.groupsByTitle[self.allGroupTitle]]:
            log.debug('Removing %s from %s' % (safe_str(deletedProgram.fullTitle()), safe_str(group.title)))
            log.debug(group)
            group.programs.remove(deletedProgram)
            
            # update count in group
            self.setListItemProperty(group.listItem, 'date', str(len(group.programs)))
            group.listItem.setThumbnailImage('OverlayHD.png')  # HACK: to force lisitem update 

            # if not rendered before, listItems will not have been realized
            if group.listItemsByProgram.has_key(deletedProgram):
                listItem = group.listItemsByProgram[deletedProgram]
                group.listItems.remove(listItem)
                del group.programsByListItem[listItem]
                del group.listItemsByProgram[deletedProgram]
            else:
                log.debug('Not fixing up group %s' % safe_str(title))

        self.programsListBox.reset()
        self.programsListBox.addItems(self.activeGroup.listItems)
        self.programsListBox.selectItem(selectionIndex)
        for i, listItem in enumerate(self.activeGroup.listItems[selectionIndex:]):
            self.setListItemProperty(listItem, 'index', str(i + selectionIndex + 1))
                
        # if last program in group, nuke group
        if len(self.groupsByTitle[title].programs) == 0:
            log.debug('Group %s now empty -- removing' % safe_str(title))
            del self.groupsByTitle[title]
            self.groupsListbox.reset()
            self.groupsListbox.addItems([group.listItem for group in self.groupsByTitle.values()])
        
    @run_async
    @catchall
    def renderPosters(self, myRenderToken):
        for (listItem, program) in self.activeGroup.programsByListItem.items()[:]:
            if self.closed or xbmc.abortRequested or myRenderToken != self.activeRenderToken: 
                return
            try:
                self.lookupPoster(listItem, program)
            except:
                log.exception('Program = %s' % safe_str(program.fullTitle()))

    @run_async
    @catchall
    def renderEpisodeColumn(self, myRenderToken):
        results = odict.odict()
        for (listItem, program) in self.activeGroup.programsByListItem.items()[:]:
            if self.closed or xbmc.abortRequested or myRenderToken != self.activeRenderToken:
                return
            try:
                season, episode = self.fanArt.getSeasonAndEpisode(program)
                if season and episode:
                    results[listItem] = '%sx%s' % (season, episode)
                    self.setListItemProperty(listItem, 'episode', results[listItem])
                    listItem.setThumbnailImage('OverlayHD.png')  # HACK: to force lisitem update 
            except:
                log.exception('Rendering season and episode for program %s' % safe_str(program.fullTitle()))
        
    def goRecordingDetails(self):
        self.lastSelected = self.programsListBox.getSelectedPosition()
        selectedItem = self.programsListBox.getSelectedItem()
        if not selectedItem:
            return
        
        selectedProgram = self.activeGroup.programsByListItem[selectedItem]
        if not selectedProgram:
            return
        
        programIterator = CyclingBidiIterator(self.activeGroup.programs, self.lastSelected)
        
        win = RecordingDetailsWindow(
            'mythbox_recording_details.xml', 
            self.platform.getScriptDir(), 
            forceFallback=True,
            programIterator=programIterator,
            settings=self.settings,
            translator=self.translator,
            platform=self.platform,
            mythThumbnailCache=self.mythThumbnailCache,
            mythChannelIconCache=self.mythChannelIconCache,
            fanArt=self.fanArt)
        win.doModal()

        if win.isDeleted:
            self.renderProgramDeleted2(programIterator.current(), programIterator.index())
        elif programIterator.index() != self.lastSelected:
            self.programsListBox.selectItem(programIterator.index())
                
        del win
