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

from mythbox.mythtv.enums import TVState, TVState44, TVState58

# MythTV Protcol Constants
initVersion = 8
separator = "[]:[]"
serverVersion = None


class ProtocolException(Exception):
    """
    Thrown on protcol version mismatch between frontend and backend or
    general protocol related errors.
    """ 
    pass


class BaseProtocol(object):
    
    def version(self):
        raise Exception, 'Abstract method'
    
    def recordSize(self):
        raise Exception, 'Abstract method'
    
    def tvState(self):
        raise Exception, 'Abstract method'
    
    def buildAnnounceFileTransferCommand(self, hostname, filePath):
        raise Exception, 'Abstract method'
    
    def getLiveTvBrain(self, settings, translator):
        raise Exception, 'Abstract method'

    def recordFields(self):
        return Exception, 'Abstract method'

    def emptyRecordFields(self):
        return []
    def protocolToken(self):
        return ""

class Protocol40(BaseProtocol):
    
    def version(self):
        return 40
    
    def recordSize(self):
        return 46
    
    def tvState(self):
        return TVState
    
    def buildAnnounceFileTransferCommand(self, hostname, filePath):
        return ["ANN FileTransfer %s" % hostname, filePath]        

    def getLiveTvBrain(self, settings, translator):
        from mythbox.ui.livetv import MythLiveTvBrain
        return MythLiveTvBrain(settings, translator)


class Protocol41(Protocol40):
    
    def version(self):
        return 41


class Protocol42(Protocol41):
    
    def version(self):
        return 42


class Protocol43(Protocol42):

    def version(self):
        return 43
    
    def recordSize(self):
        return 47


class Protocol44(Protocol43):
    
    def version(self):
        return 44
    
    def tvState(self):
        return TVState44


class Protocol45(Protocol44):
    
    def version(self):
        return 45

    def buildAnnounceFileTransferCommand(self, hostname, filePath):
        # TODO: Storage group should be non-empty for recordings
        storageGroup = ''
        return ['ANN FileTransfer %s' % hostname, filePath, storageGroup]        


class Protocol46(Protocol45):
    
    def version(self):
        return 46


class Protocol47(Protocol46):
    
    def version(self):
        return 47


class Protocol48(Protocol47):
    
    def version(self):
        return 48


class Protocol49(Protocol48):
    
    def version(self):
        return 49


class Protocol50(Protocol49):
    
    def version(self):
        return 50


class Protocol56(Protocol50):
    
    def version(self):
        return 56


class Protocol57(Protocol56):
    
    def version(self):
        return 57

    def recordSize(self):
        return 41

    def recordFields(self):
        return ['title','subtitle','description','category','chanid','channum','callsign','channame','filename','filesize','starttime','endtime','findid','hostname','sourceid','cardid','inputid','recpriority','recstatus','recordid','rectype','dupin','dupmethod','recstartts','recendts','programflags','recgroup','outputfilters','seriesid','programid','lastmodified','stars','airdate','playgroup','recpriority2','parentid','storagegroup','audio_props','video_props','subtitle_type','year']
    
    def buildAnnounceFileTransferCommand(self, hostname, filePath):
        return ["ANN FileTransfer %s 0" % hostname, filePath, 'Default']

class Protocol23056(Protocol57):
    
    def version(self):
        return 23056
    
class Protocol58(Protocol57):
    def tvState(self):
        return TVState58

    def version(self):
        return 58
    
class Protocol59(Protocol58):
   def version(self):
        return 59    

class Protocol60(Protocol59):
   def version(self):
        return 60
   def buildAnnounceFileTransferCommand(self, hostname, filePath):
        return ["ANN FileTransfer %s 0 1 10000" % hostname, filePath, 'Default']

class Protocol61(Protocol60):
   def version(self):
        return 61

class Protocol62(Protocol61):
    def version(self):
        return 62
    def protocolToken(self):
        return "78B5631E"

class Protocol63(Protocol62):
    def version(self):
        return 63
    def protocolToken(self):
        return "3875641D"
    
# Current rev in mythversion.h
protocols = {
    40: Protocol40(),
    41: Protocol41(),
    42: Protocol42(),
    43: Protocol43(),
    44: Protocol44(),
    45: Protocol45(),
    46: Protocol46(),
    47: Protocol47(),
    48: Protocol48(),
    49: Protocol49(),
    50: Protocol50(),  # 0.22
    56: Protocol56(),  # 0.23
    57: Protocol57(),  # 0.23.1
    58: Protocol58(),  # 0.24
    59: Protocol59(),  # 0.24
    60: Protocol60(),  # 0.24
    61: Protocol61(),  # 0.24
    62: Protocol62(),  # 0.24
    63: Protocol63(),  # 0.24
    23056: Protocol23056()  # mythbuntu weirdness
}    