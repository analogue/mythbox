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

import os
import socket
import time
import tempfile 

abortRequested = False

def getIPAddress():
    return socket.gethostbyname(socket.gethostname())


def getLanguage():
    return 'English'


def getSkinDir():
    return os.getcwd()


def executebuiltin(command):
    """
    Execute a built in XBMC function.
     
    function       : string - builtin function to execute.
     
    List of functions - http://xbmc.org/wiki/?title=List_of_Built_In_Functions 
     
    example:
      - xbmc.executebuiltin('XBMC.RunXBE(c:\\avalaunch.xbe)')
    """
    pass


def dashboard():
    """
    Boot to dashboard as set in My Pograms/General.
     
    example:
      - xbmc.dashboard()
    """
    pass


def enableNavSounds(yesNo):
    """
    Enables/Disables nav sounds
     
    yesNo          : integer - enable (True) or disable (False) nav sounds
     
    example:
      - xbmc.enableNavSounds(True)
    """
    pass


def executehttpapi(httpcommand):
    """
    Execute an HTTP API command.
     
    httpcommand    : string - http command to execute.
     
    List of commands - http://xbmc.org/wiki/?title=WebServerHTTP-API#The_Commands 
     
    example:
      - response = xbmc.executehttpapi('TakeScreenShot(special://temp/test.jpg,0,false,200,-1,90)')
    """
    pass


def executescript(script):
    """
    Execute a python script.
     
    script         : string - script filename to execute.
     
    example:
      - xbmc.executescript('special://home/scripts/update.py')
    """
    pass


def getCacheThumbName(path):
    """
    Returns a thumb cache filename.
     
    path           : string or unicode - path to file
     
    example:
      - thumb = xbmc.getCacheThumbName('f:\\videos\\movie.avi')
    """
    pass


def getCondVisibility(condition):
    """
    Returns True (1) or False (0) as a bool.
     
    condition      : string - condition to check.
     
    List of Conditions - http://xbmc.org/wiki/?title=List_of_Boolean_Conditions 
     
    *Note, You can combine two (or more) of the above settings by using "+" as an AND operator,
    "|" as an OR operator, "!" as a NOT operator, and "[" and "]" to bracket expressions.
     
    example:
      - visible = xbmc.getCondVisibility('[Control.IsVisible(41) + !Control.IsVisible(12)]')
    """
    pass


def getDVDState():
    """
    Returns the dvd state as an integer.
     
    return values are:
       1 : xbmc.DRIVE_NOT_READY
      16 : xbmc.TRAY_OPEN
      64 : xbmc.TRAY_CLOSED_NO_MEDIA
      96 : xbmc.TRAY_CLOSED_MEDIA_PRESENT
     
    example:
      - dvdstate = xbmc.getDVDState()
    """
    pass


def getFreeMem():
    """
    Returns the amount of free memory in MB as an integer.
     
    example:
      - freemem = xbmc.getFreeMem()
    """
    pass


def getGlobalIdleTime():
    """
    Returns the elapsed idle time in seconds as an integer.
    example:
      - t = xbmc.getGlobalIdleTime()
    """
    pass


def getInfoImage(infotag):
    """
    Returns a filename including path to the InfoImage's thumbnail as a string.
     
    infotag        : string - infotag for value you want returned.
     
    List of InfoTags - http://xbmc.org/wiki/?title=InfoLabels 
     
    example:
      - filename = xbmc.getInfoImage('Weather.Conditions')
    """
    pass


def getInfoLabel(infotag):
    """
    Returns an InfoLabel as a string.
     
    infotag        : string - infoTag for value you want returned.
     
    List of InfoTags - http://xbmc.org/wiki/?title=InfoLabels 
     
    example:
      - label = xbmc.getInfoLabel('Weather.Conditions')
    """
    pass


def getLocalizedString(id):
    """
    Returns a localized 'unicode string'.
     
    id             : integer - id# for string you want to localize.
     
    *Note, See strings.xml in \language\{yourlanguage}\ for which id
           you need for a string.
     
    example:
      - locstr = xbmc.getLocalizedString(6)
    """
    return 'TODO'


def getRegion(id):
    """
    Returns your regions setting as a string for the specified id.
     
    id             : string - id of setting to return
     
    *Note, choices are (dateshort, datelong, time, meridiem, tempunit, speedunit)
     
           You can use the above as keywords for arguments.
     
    example:
      - date_long_format = xbmc.getRegion('datelong')
    """
    pass


def getSupportedMediaa(media):
    """
    Returns the supported file types for the specific media as a string.
     
    media          : string - media type
     
    *Note, media type can be (video, music, picture).
     
           The return value is a pipe separated string of filetypes (eg. '.mov|.avi').
     
           You can use the above as keywords for arguments.
     
    example:
      - mTypes = xbmc.getSupportedMedia('video')
    """
    pass


def log(msg, level):
    """Write a string to XBMC's log file.
     
    msg            : string - text to output.
    level          : [opt] integer - log level to ouput at. (default=LOGNOTICE)
     
     
    *Note, You can use the above as keywords for arguments and skip certain optional arguments.
           Once you use a keyword, all following arguments require the keyword.
     
           Text is written to the log for the following conditions.
             XBMC loglevel == -1 (NONE, nothing at all is logged)         XBMC loglevel == 0 (NORMAL, shows LOGNOTICE, LOGERROR, LOGSEVERE and LOGFATAL)         XBMC loglevel == 1 (DEBUG, shows all)       See pydocs for valid values for level.
     
    example:
      - xbmc.log(msg='This is a test string.', level=xbmc.LOGDEBUG)
    """
    pass


def makeLegalFilename(filename, fatX):
    """Returns a legal filename or path as a string.
     
    filename       : string or unicode - filename/path to make legal
    fatX           : [opt] bool - True=Xbox file system(Default)
     
    *Note, If fatX is true you should pass a full path. If fatX is false only pass
           the basename of the path.
     
           You can use the above as keywords for arguments and skip certain optional arguments.
           Once you use a keyword, all following arguments require the keyword.
     
    example:
      - filename = xbmc.makeLegalFilename('F:\Trailers\Ice Age: The Meltdown.avi')
    """
    pass


def output(msg, level):
    """
    Write a string to XBMC's log file and the debug window.
     
    msg            : string - text to output.
    level          : [opt] integer - log level to ouput at. (default=LOGNOTICE)
     
    *Note, You can use the above as keywords for arguments and skip certain optional arguments.
           Once you use a keyword, all following arguments require the keyword.
     
           Text is written to the log for the following conditions.
             XBMC loglevel == -1 (NONE, nothing at all is logged)         XBMC loglevel == 0 (NORMAL, shows LOGNOTICE, LOGERROR, LOGSEVERE and LOGFATAL)         XBMC loglevel == 1 (DEBUG, shows all)       See pydocs for valid values for level.
     
    example:
      - xbmc.output(msg='This is a test string.', level=xbmc.LOGDEBUG)
    """
    pass


def playSFX(filename):
    """
    Plays a wav file by filename
     
    filename       : string - filename of the wav file to play.
     
    example:
      - xbmc.playSFX('special://xbmc/scripts/dingdong.wav')
    """
    pass


def restart():
    """
    Restart the xbox.
     
    example:
      - xbmc.restart()
    """
    pass


def shutdown():
    """
    Shutdown the xbox.
     
    example:
      - xbmc.shutdown()
    """
    pass


def skinHasImage(image):
    """
    Returns True if the image file exists in the skin.
     
    image          : string - image filename
     
    *Note, If the media resides in a subfolder include it. (eg. home-myfiles\\home-myfiles2.png)
     
           You can use the above as keywords for arguments.
     
    example:
      - exists = xbmc.skinHasImage('ButtonFocusedTexture.png')
    """
    pass


def sleep(millis):
    """
    Sleeps for 'time' msec.
     
    millis           : integer - number of msec to sleep.
     
    *Note, This is useful if you have for example a Player class that is waiting
           for onPlayBackEnded() calls.
     
    Throws: PyExc_TypeError, if time is not an integer.
     
    example:
      - xbmc.sleep(2000) # sleeps for 2 seconds
    """
    secs = float(millis) / float(1000)
    time.sleep(secs)


def translatePath(path):
    """
    Returns the translated path.
     
    path           : string or unicode - Path to format
     
    *Note, Only useful if you are coding for both Linux and the Xbox.
           e.g. Converts 'special://masterprofile/script_data' -> '/home/user/XBMC/UserData/script_data'
           on Linux. Would return 'special://masterprofile/script_data' on the Xbox.
     
    example:
      - fpath = xbmc.translatePath('special://masterprofile/script_data')
    """
    return tempfile.mkdtemp()

    
class PlayList(object):
    
    def __init__(self, someInt):
        pass
    

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
        self._playing = True
        self._time = 1
        self.onPlayBackStarted()
        time.sleep(2)
        self.stop()
        self.onPlayBackEnded()
            
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
        pass
    
    def doModal(self):
        pass
    
    def isConfirmed(self):
        return Keyboard.stubConfirmed
    
    def getText(self):
        return Keyboard.stubText


class Settings(object):
 
    def __init__(self, path):
        """
        Creates a new Settings class.
        path            : string - path to script. (eg special://home/scripts/Apple Movie Trailers)
        *Note, settings folder structure is eg(resources/settings.xml)
               You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
        example:
         - self.Settings = xbmc.Settings(path=os.getcwd())
        """
        pass

    def getSetting(self, id):
        """
        Returns the value of a setting as a string.
         
        id        : string - id of the setting that the module needs to access.
         
        *Note, You can use the above as a keyword.
         
        example:
          - apikey = self.Settings.getSetting('apikey')
        """
        pass
    
    def openSettings(self):
        """
        openSettings() -- Opens this scripts settings dialog.
         
        example:
          - self.Settings.openSettings()
        """
        pass
    
    def setSetting(self, id, value):
        """
        Sets a script setting.
         
        id        : string - id of the setting that the module needs to access.
        value     : string or unicode - value of the setting.
         
        *Note, You can use the above as keywords for arguments.
         
        example:
          - self.Settings.setSetting(id='username', value='teamxbmc')
        """
        pass    
