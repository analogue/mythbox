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
import datetime
import logging
import odict
import player
import threading
import ui
import util
import xbmcgui
import xbmc

from ui import window_busy
from util import catchall, catchall_ui, timed, ServerException, run_async, lirc_hack
from injected import inject_db, inject_conn

log = logging.getLogger('mythtv.ui')
    
# =============================================================================
class BaseLiveTvBrain(object):

    def __init__(self, settings):
        self.settings = settings          
        self.tuner = None

    def watchLiveTV(self, channel):
        raise Exception, 'Subclass should implement'
        
    @inject_conn
    def _findAvailableTunerWithChannel(self, channel):
        """
        @param channel: Channel to find a tuner for
        @return: Tuner that is availble for livetv, None otherwise
        @raise ServerException: If a tuner is not currently available
        """
        # 1. Check at least one tuner available
        numFreeTuners = self.conn().getNumFreeTuners()
        if numFreeTuners <= 0:
            raise util.ServerException('All tuner(s) are busy.')
        
        # 2. Make sure available tuner can watch requested channel
        tuners = self.conn().getTuners()
        for tuner in tuners:
            if not tuner.isRecording() and tuner.hasChannel(channel):
                log.debug("Found tuner %s to view channel %s" % (tuner.tunerId, channel.getChannelNumber()))
                return tuner
            
        raise util.ServerException('A tuner capable of viewing channel %s is not available.' % channel.getChannelNumber())
        
# =============================================================================
class MythLiveTvBrain(BaseLiveTvBrain):
    """
    Orchestrates live tv using XBMC's built in myth:// URL support
    """

    def __init__(self, settings):
        BaseLiveTvBrain.__init__(self, settings)

    def watchLiveTV(self, channel):
        try:
            self.tuner = self._findAvailableTunerWithChannel(channel)
        except util.ServerException, se:
            xbmcgui.Dialog().ok('Error', str(se))
        
        livePlayer = MythLiveTvPlayer()
        livePlayer.watchChannel(self.settings, channel)
        del livePlayer # induce GC so on* callbacks unregistered
        return self.tuner

# ==============================================================================
class MythLiveTvPlayer(xbmc.Player):
    """
    Plays live tv using XBMC's built in myth:// URL support
    """
    
    def __init__(self):
        xbmc.Player.__init__(self)    
        self._active = True
    
    def watchChannel(self, settings, channel):
        # This player doesn't care about on* callbacks, so no need to wait for playback
        # completion. 

        # url must not be unicode!
        url = 'myth://%s:%s@%s/channels/%s.ts' % (
            str(settings.get('mysql_user')),
            str(settings.get('mysql_password')),
            str(settings.get('mysql_host')),
            str(channel.getChannelNumber()))
        self.play(url)

# =============================================================================
class FileLiveTvBrain(BaseLiveTvBrain):
    """
    Orchestrates live tv using the livetv recording available on the filesystem
    """
    def __init__(self, settings):
        BaseLiveTvBrain.__init__(self, settings)
            
    def watchLiveTV(self, channel):
        """
        Starts watching LiveTV for the given channel. Blocks until stopped, LiveTV ends, or error occurs.
        
        @param channel: Channel the couch potato would like to watch
        @return: Tuner picked to watch live tv
        @raise ServerException: When tuner not available
        """
        liveBuffer = max(int(self.settings.get('mythtv_minlivebufsize')), 1024)
        liveTimeout = max(int(self.settings.get('mythtv_tunewait')), 60)
        
        progress = xbmcgui.DialogProgress()
        progress.create('Watch TV', 'Finding tuner...')
        self.tuner = self._findAvailableTunerWithChannel(channel)
        
        progress.update(20, '', 'Tuning channel...')
        self.tuner.startLiveTV(channel.getChannelNumber())
        
        try:
            progress.update(40, '', 'Starting recording...')
            self.tuner.waitForRecordingToStart(timeout=liveTimeout)

            # callback to update progress dialog
            def updateBuffered(kb):
                progress.update(70, '', 'Buffering %sKB ...' % kb)
                
            progress.update(60, '', 'Buffering...')
            self.tuner.waitForRecordingWritten(numKB=liveBuffer, timeout=liveTimeout, callback=updateBuffered)
            
            progress.update(80, '', 'Starting player...')
            whatsPlaying = self.tuner.getWhatsPlaying()
            log.debug('Currently playing = %s' % whatsPlaying.getLocalPath())
            
            progress.close()
            livePlayer = FileLiveTvPlayer()
            livePlayer.addListener(self)
            livePlayer.playRecording(whatsPlaying, player.NoOpCommercialSkipper(player, whatsPlaying))
            del livePlayer # induce GC so on* callbacks unregistered
        except:
            # If things went south after starting livetv, attempt to stop livetv
            try:
                if self.tuner.isRecording():
                    log.info('Stopping LiveTV because start live TV failed...')
                    self.tuner.stopLiveTV()
            except:
                log.exception('Trying to clean up after start liveTV failed')
            raise  # propagate
                
        return self.tuner
    
    def getLiveTVStatus(self):
        return self.tuner.getLiveTVStatus()

    #
    # Callbacks initiated by LiveTVPlayer
    # 
    def onPlayBackStarted(self):
        pass
    
    def onPlayBackStopped(self):
        self.tuner.stopLiveTV()
            
    def onPlayBackEnded(self):
        self.tuner.stopLiveTV()
    
# =============================================================================
class FileLiveTvPlayer(player.MythPlayer):
    """
    Play live tv using the livetv recording available on the filesystem
    """
    
    # TODO: Callback listener registration needs to be pushed down to player.MythPlayer
    #       eventually making this class obsolete.
    
    def __init__(self):
        player.MythPlayer.__init__(self)
        self.listeners = []  
    
    def addListener(self, listener):
        self.listeners.append(listener)
    
    @catchall    
    def onPlayBackStarted(self):
        log.debug('> onPlayBackStarted')
        if self._active:
            try:
                for listener in self.listeners:
                    try: 
                        listener.onPlayBackStarted()
                    except:
                        log.exception('listener %s callback blew up' % listener)
            finally:
                log.debug('< onPlayBackStarted')

    @catchall
    def onPlayBackStopped(self):
        log.debug('> onPlayBackStopped')
        if self._active:
            try:
                for listener in self.listeners:
                    try: 
                        listener.onPlayBackStopped()
                    except:
                        log.exception('listener %s callback blew up' % listener)
            finally:
                self._playbackCompletedLock.set()
                log.debug('< onPlayBackStopped')
            
    @catchall
    def onPlayBackEnded(self):
        log.debug('> onPlayBackEnded')
        if self._active:
            try:
                for listener in self.listeners:
                    try: 
                        listener.onPlayBackEnded()
                    except:
                        log.exception('listener %s callback blew up' % listener)
            finally:
                self._playbackCompletedLock.set()
                log.debug('< onPlayBackEnded')

    def _reset(self, program):
        """
        Overrides super impl
        """
        self._program = program
        self._playbackCompletedLock = threading.Event()
        self._playbackCompletedLock.clear()

# ==============================================================================
class LiveTvWindow(ui.BaseWindow):
    
    def __init__(self, *args, **kwargs):
        ui.BaseWindow.__init__(self, *args, **kwargs)
        
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
        self.mythChannelIconCache = kwargs['mythChannelIconCache']
        self.platform = kwargs['platform']
        self.fanArt = kwargs['fanArt']

        self.channels = None                     # Channels sorted and merged (if multiple tuners)
        self.channelsById = None                 # {int channelId:Channel}
        self.programs = None                     # [TVProgram]
        self.listItemsByChannel = odict.odict()  # {Channel:ListItem}
        self.closed = False
        
    @catchall_ui
    def onInit(self):
        if not self.win:
            self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self.channelsListBox = self.getControl(600)
            self.refreshButton = self.getControl(250)
        self.refresh()

    @window_busy
    def refresh(self):
        self.loadPrograms()
        self.render()
        self.renderPosters()
        
    @catchall    
    def onClick(self, controlId):
        source = self.getControl(controlId)
        if source == self.channelsListBox: 
            self.watchSelectedChannel()
        elif source == self.refreshButton:
            self.refresh()
             
    def onFocus(self, controlId):
        pass
            
    @catchall_ui
    @lirc_hack            
    def onAction(self, action):
        if action.getId() in (ui.ACTION_PREVIOUS_MENU, ui.ACTION_PARENT_DIR):
            self.closed = True
            self.close()

    @window_busy
    @inject_conn
    def watchSelectedChannel(self):
        listItem = self.channelsListBox.getSelectedItem()
        channelId = int(listItem.getProperty('channelId'))
        channel = self.channelsById[channelId]
        
        # Use myth:// based player for 0.21
        # Use file based player for 0.22 until myth:// supports 0.22 
        brain = self.conn().protocol.getLiveTvBrain(self.settings)
        
        try:
            try:
                brain.watchLiveTV(channel)
            except ServerException, se:
                xbmcgui.Dialog().ok('Error', '', str(se))
        finally:    
            del brain

    def mergeChannels(self):
        """
        With multiple tuners, the same channel may be available more than once. 
        Consolidates duplicate channels (based on unique channel number)
        into a single channel. The channel chosen is from an arbitrary tuner.
        """
        bucket = {}
        for channel in reversed(self.channels):
            bucket[channel.getChannelNumber()] = channel
        self.channels = bucket.values()

    @timed
    @inject_db
    def loadChannels(self):
        """
        @attention: Cached after initial invocation
        @postcondition: self.channels contains list of channels in presentation order
        @postcondition: self.channelsById contains channels keyed on channelId
        """
        if self.channels == None:

            def channelComparator(c1, c2):
                return cmp(c1.getSortableChannelNumber(), c2.getSortableChannelNumber())

            self.channels = self.db().getChannels()
            self.mergeChannels()
            self.channels.sort(channelComparator)
            self.channelsById = odict.odict()
            for c in self.channels:
                self.channelsById[c.getChannelId()] = c

    @timed
    @inject_db
    def loadPrograms(self):
        self.loadChannels()
        now = datetime.datetime.now()
        self.programs = self.db().getProgramListings(now, now)
        programsByChannelId = odict.odict()
        
        for p in self.programs:
            programsByChannelId[p.getChannelId()] = p
        
        # make TVProgram accessible as Channel.currentProgram    
        for channelId, channel in self.channelsById.items():
            if programsByChannelId.has_key(channelId):
                channel.currentProgram = programsByChannelId[channelId]
            else:
                channel.currentProgram = None

    @timed
    def render(self):
        log.debug('Rendering....')
        self.listItemsByChannel.clear()
        listItems = []
        
        for i, channel in enumerate(self.channels):
            #log.debug('Working channel: %d' %i)
            listItem = xbmcgui.ListItem('Row %d' % i)
            self.setListItemProperty(listItem, 'channelId', str(channel.getChannelId()))
            
            if channel.getIconPath():
                cachedIcon = self.mythChannelIconCache.get(channel)
                if cachedIcon:
                    self.setListItemProperty(listItem, 'channelIcon', cachedIcon)
                
            self.setListItemProperty(listItem, 'channelName', channel.getChannelName())
            self.setListItemProperty(listItem, 'channelNumber', channel.getChannelNumber())
            self.setListItemProperty(listItem, 'callSign', channel.getCallSign())
            
            if channel.currentProgram:
                self.setListItemProperty(listItem, 'title', channel.currentProgram.title())
                self.setListItemProperty(listItem, 'description', channel.currentProgram.formattedDescription())
                self.setListItemProperty(listItem, 'category', channel.currentProgram.category())
            else:
                self.setListItemProperty(listItem, 'title', 'No Data')
                
            listItems.append(listItem)
            self.listItemsByChannel[channel] = listItem
        self.channelsListBox.addItems(listItems)
    
    def renderPosters(self):
        # split up poster lookup to run in parallel
        for channels in util.slice(self.listItemsByChannel.keys(), 4):
            self.renderPostersThread(channels)
            
    @run_async
    @catchall
    def renderPostersThread(self, channels):
        for i, channel in enumerate(channels):
            if self.closed: 
                return
            if channel.currentProgram:
                listItem = self.listItemsByChannel[channel]
                # Lookup poster if available
                log.debug('Poster %d/%d for %s' % (i+1, len(channels), channel.currentProgram.title()))
                posterPath = self.fanArt.getRandomPoster(channel.currentProgram)
                if posterPath:
                    self.setListItemProperty(listItem, 'poster', posterPath)
                elif channel.getIconPath():
                    self.setListItemProperty(listItem, 'poster', self.mythChannelIconCache.get(channel))
            