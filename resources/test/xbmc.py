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
import socket
import time

"""
Mock xbmc module used by unit tests
"""

log = logging.getLogger('mythtv.unittest')

# =============================================================================
def getIPAddress():
    return socket.gethostbyname(socket.gethostname())

def getLanguage():
    return 'English'

def getSkinDir():
    return os.getcwd()

def sleep(millis):
    secs = float(millis) / float(1000)
    time.sleep(secs)
    
def executebuiltin(command):
    pass

def translatePath(path):
    return path

# =============================================================================
class Language(object):

    def __init__(self, scriptPath, defaultLanguage, *args, **kwargs):
        """
        Language class.

        Language(scriptPath, defaultLanguage) -- Creates a new Language class.

        scriptPath      : string - path to script. (eg os.getcwd())
        defaultLanguage : [opt] string - default language to fallback to. (default=English)

        *Note, language folder structure is eg(language/English/strings.xml)

        You can use the above as keywords for arguments and skip certain optional arguments.
        Once you use a keyword, all following arguments require the keyword.

        example:
         - self.Language = xbmc.Language(os.getcwd())
        """
        pass
        
    def getLocalizedString(self, id):
        """
        Returns a localized 'unicode string'.
        id : integer - id# for string you want to localize.
        
        *Note, getLocalizedString() will fallback to XBMC strings if no string found.
        
        You can use the above as keywords for arguments and skip certain optional arguments"
        Once you use a keyword, all following arguments require the keyword."
        
        example:
        locstr = self.Language.getLocalizedString(id=6)
        """
        return 'TODO'
    
# =============================================================================
class PlayList(object):
    
    def __init__(self, someInt):
        pass
    
# =============================================================================    
class Player(object):
    
    def __init__(self):
        self._playing = False
        self._time = 0
        
    def getMusicInfoTag(self):
        """
        returns the MusicInfoTag of the current playing 'Song'.
        Throws: Exception, if player is not playing a file or current file is not a music file.
        """
        pass
     
    def getPlayingFile(self):
        """
        getPlayingFile() -- returns the current playing file as a string.
        Throws: Exception, if player is not playing a file.
        """
        pass

    def getTime(self):
        """
        getTime() -- Returns the current time of the current playing media as fractional seconds.
        Throws: Exception, if player is not playing a file.
        """
        self._time += 1
        return self._time


    def getTotalTime(self):
        """
        getTotalTime() -- Returns the total time of the current playing media in
                          seconds.  This is only accurate to the full second.
        Throws: Exception, if player is not playing a file.
        """
        pass 
    
    def getVideoInfoTag(self):
        """
        getVideoInfoTag() -- returns the VideoInfoTag of the current playing Movie.
        Throws: Exception, if player is not playing a file or current file is not a movie file.
        Note, this doesnt work yet, it's not tested
        """
        pass

    def isPlaying(self):
        """
        isPlayingAudio() -- returns True is xbmc is playing a file.
        """
        return self._playing

    def isPlayingAudio(self):
        """
        isPlayingAudio() -- returns True is xbmc is playing an audio file.
        """
        return self._playing
    
    def isPlayingVideo(self):
        """
        isPlayingVideo() -- returns True if xbmc is playing a video.
        """
        return self._playing
    
    def onPlayBackEnded(self):
        """
        onPlayBackEnded() -- onPlayBackEnded method.
        Will be called when xbmc ends playing a file
        """
        pass

    def onPlayBackStarted(self):
        """
        onPlayBackStarted() -- onPlayBackStarted method.
        Will be called when xbmc starts playing a file
        """
        pass

    def onPlayBackStopped(self):
        """
        onPlayBackStopped() -- onPlayBackStopped method.
        Will be called when user stops xbmc playing a file
        """
        pass

    def pause(self):
        """
        pause() -- Pause playing.
        """
        pass

    def play(self, item = None, listItem = None):
        """
        play([item, listitem]) -- Play this item.
     
        item           : [opt] string - filename, url or playlist.
        listitem       : [opt] listitem - used with setInfo() to set different infolabels.
     
        *Note, If item is not given then the Player will try to play the current item
               in the current playlist.
     
        example:
        - listitem = xbmcgui.ListItem('Ironman')
        - listitem.setInfo('video', {'Title': 'Ironman', 'Genre': 'Science Fiction'})
        - xbmc.Player( xbmc.PLAYER_CORE_MPLAYER ).play(url, listitem)
        """
        log.debug("> play")
        self._playing = True
        self._time = 1
        self.onPlayBackStarted()
        time.sleep(2)
        self.stop()
        self.onPlayBackEnded()
        log.debug("< play")
            
    def playnext(self):
        """
        playnext() -- Play next item in playlist.
        """
        pass

    def playprevious(self):
        """
        playprevious() -- Play previous item in playlist.
        """
        pass

    def playselected(self):
        """
        playselected() -- Play a certain item from the current playlist.
        """
        pass

    def seekTime(self, secs):
        """
        seekTime() -- Seeks the specified amount of time as fractional seconds.
                      The time specified is relative to the beginning of the
                      currently playing media file.
        Throws: Exception, if player is not playing a file.
        """
        self._time = secs
    
    def stop(self):
        """
        stop() -- Stop playing.
        """
        self._playing = False
        self._time = 0
        self.onPlayBackStopped()
        
# =============================================================================
class Keyboard(object):

    stubConfirmed = True
    stubText = ""
    
    def __init__(self, default="", heading="", hidden=False):
        """
        Keyboard([default, heading, hidden]) -- Creates a new Keyboard object with default text
                                        heading and hidden input flag if supplied.
         
        default        : [opt] string - default text entry.
        heading        : [opt] string - keyboard heading.
        hidden         : [opt] boolean - True for hidden text entry.
        """
        log.debug('xbmc.KeyBoard created')
    
    def doModal(self):
        pass
    
    def isConfirmed(self):
        return Keyboard.stubConfirmed
    
    def getText(self):
        return Keyboard.stubText