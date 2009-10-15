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
import domain
import enums
import filecache
import logging
import md5
import mythdb
import mythprotocol
import os
import mythbox
import socket
import sre
import time
import util

from util import timed
from xml.dom import minidom

log     = logging.getLogger('mythtv.core')     # mythtv core logger
wirelog = logging.getLogger('mythtv.wire')     # wire level protocol logger
slog    = logging.getLogger('mythtv.settings') # settings from xml file log

# =============================================================================
def createChainID():
    """Return a new chainID as a string suitable for spawning livetv"""
    # Based on livetvchain.cpp:InitializeNewChain(...)
    # Match format: live-zeus-2008-12-04T11:41:52
    return "live-%s-%s" % (socket.gethostname(), time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()))

# =============================================================================
class Connection(object):
    """
    Connection to MythTV Backend.
    
    TODO: Update to support multiple storage groups - getFreeSpace()
    TODO: What is difference between MONITOR and PLAYBACK in mythtv protocol?
    TODO: Rename to MythSession
    """
    
    def __init__(self, settings, db, translator, platform):
        """
        @param settings: Mythbox settings
        @param db: mysql db connection
        @param translator: localized strings
        @param platform: Platform instance 
        """
        self._db = db
        self.settings = settings
        self.translator = translator
        self.platform = platform
        self.host = self.settings.getMythTvHost()
        self.port = self.settings.getMythTvPort()
        self._initialise()
        
    def db(self):
        return self._db
    
    @timed
    def _initialise(self):
        """
        Initializes this connection and attempts to connect to the master
        myth backend server.
        """
        try:
            # Command socket used to talk to the backend
            self.cmdSock = self.connect()
            self.isConnected = True
        except:
            self.isConnected = False
            raise

    def connect(self, Playback=False, Monitor=True, slaveBackend=None):
        """ 
        Return a socket after successfully connecting to the myth master backend.
        Specify backendHost to connect to a slave backend.
        
        Used in three scenarios:
            - connect to server as Player
            - connect to server as Monitor
            - connect to server as raw socket connection
        
        @param server: mythv backend hostname as string
        @todo: fix to support slave backends
        """
        log.debug("Connection.connect(%s,%s)"%(Playback, Monitor))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if slaveBackend == None:
            slaveBackend = self.host
        s.connect((slaveBackend, self.port))
        
        if Monitor or Playback:
            log.debug('Getting server version...')
            mythprotocol.serverVersion = self.getServerVersion()
            log.debug('Server version = %d' % mythprotocol.serverVersion)
            serverVersion = self.negotiateProtocol(s, mythprotocol.serverVersion)
            try:
                self.protocol = mythprotocol.protocols[serverVersion]
            except KeyError:
                raise util.ProtocolException('Unsupported protocol: %s' % serverVersion)
            
        # TODO: These are mutually exclusive but both can be true when 
        #       sent in as arguments to this method. Check w/ assertion   
        if Monitor:
            self.annMonitor(s)
        elif Playback:
            self.annPlayback(s)
            
        return s

    def getServerVersion(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.settings.getMythTvHost() , self.settings.getMythTvPort()))
        try:
            # induce reject
            reply = self._sendRequest(sock, ["MYTH_PROTO_VERSION %d" % mythprotocol.initVersion])
            serverResponse = reply[0]
            serverVersion  = int(reply[1])
            log.debug('getServerVersion: %s %s' % (serverResponse, serverVersion))
        finally:
            sock.close()
        return serverVersion
        
    def close(self):
        if self.cmdSock:
            if self.isConnected:
                self._sendMsg(self.cmdSock, ['DONE'])
                self.isConnected = False
            self.cmdSock.shutdown(socket.SHUT_RDWR)
            self.cmdSock.close()
            self.cmdSock = None
            
        if self._db:
            self._db.close()
                
    @timed            
    def negotiateProtocol(self, s, clientVersion):
        """ 
        @return: version of the MythTV protocol the server supports
        @rtype: int 
        @raise ProtocolException: when clientVersion is less than serverVersion
        """
        msg = "MYTH_PROTO_VERSION %s" % clientVersion
        reply = self._sendRequest(s, [msg])
        
        serverResponse = reply[0]
        serverVersion  = int(reply[1])
        wirelog.debug('negotiateProtocol: %s => %s %s' % (msg, serverResponse, serverVersion))
        
        if (serverVersion < clientVersion):
            pe = util.ProtocolException("Protocol mismatch - Server protocol version: %s  Client protocol version: %s"%(serverVersion, clientVersion))
            pe.protocolVersion = serverVersion
            raise pe   
        return serverVersion

    @timed
    def annPlayback(self, cmdSock):
        reply = self._sendRequest(cmdSock, ["ANN Playback %s 0" % self.platform.getHostname()])
        if not self._isOk(reply):
            raise util.ServerException, "Backend playback refused: %s" % reply
    
    @timed
    def annMonitor(self, cmdSock):
        reply = self._sendRequest(cmdSock, ["ANN Monitor %s 0" % self.platform.getHostname()])
        if not self._isOk(reply):
            raise util.ServerException, "Backend monitor refused: %s" % reply

    @timed
    def annFileTransfer(self, backendHost, filePath):
        """
        Announce file transfer to backend.
        
        @param backendHost : Hostname of backend that recorded the file to transfer
        @param filePath    : Myth style URL of file to tranfer. Ex: myth://somehost:port/blah.mpg
        @return            : list[reply[], socket] 
        """
        s = self.connect(False, False, backendHost)
        self._sendMsg(s, self.protocol.buildAnnounceFileTransferCommand(self.platform.getHostname(),  filePath))
        reply = self._readMsg(s)
        if not self._isOk(reply):
            raise util.ServerException("Backend filetransfer refused: %s" % reply)
        del reply[0]    # remove OK
        return [reply,s]
        
    def checkFile(self, rec):
        # TODO: Whats this for? Not used currently
        msg = rec.data()[:]
        msg.insert(0,'QUERY_CHECKFILE')
        reply = self._sendRequest(msg)
        return reply[0]

    def getSetting(self, key, hostname):
        """
        @return: MythSetting for the given key and hostname
        """
        command = 'QUERY_SETTING %s %s' %(key, hostname)
        reply = self._sendRequest(self.cmdSock, [command])
        return reply
        # TODO: Unfinished!
    
    def getChannels(self):
        """
        @return: Viewable channels across all tuners.
        @rtype: Channel[]
        """
        return self.db().getChannels()
    
    @timed
    def getTuners(self):
        """
        Get all available tuners (aka encoder, recorder, capturecard, cardinput)
        @return: Tuner[]
        """
        tuners = self.db().getTuners()
        # inject each tuner w/ this session before returning
        for t in tuners:
            t.conn = self
        return tuners
    
    @timed
    def getFramesWritten(self, tuner):
        """For a tuner that is recording, return the number of frames written as an int"""
        reply = self._sendRequest(self.cmdSock, ['QUERY_RECORDER %d' % tuner.tunerId, 'GET_FRAMES_WRITTEN'])
        return util.decodeLongLong(int(reply[1]), int(reply[0]))

    @timed
    def getTunerFrameRate(self, tuner):
        """For a tuner that is recording, return the framerate as a float"""
        reply = self._sendRequest(self.cmdSock, ['QUERY_RECORDER %d' % tuner.tunerId, 'GET_FRAMERATE'])
        return float(reply[0])

    @timed 
    def getCurrentRecording(self, tuner):
        """
        @return: For a tuner that is recording, return the current Program
        @rtype: RecordedProgram
        """
        reply = self._sendRequest(self.cmdSock, ['QUERY_RECORDER %d' % tuner.tunerId, 'GET_CURRENT_RECORDING'])
        import injected
        program = injected.InjectedRecordedProgram(reply, self.settings, self.translator, self.platform)
        return program
        
    @timed
    def getTunerShowing(self, showName):
        """ 
        @type showName: str
        @return: tunerId of the first tuner either recording or watching the given showname, otherwise returns -1
        @rtype: int
        @todo: Change return type to Tuner or None
        @todo: Rename to getTunerWatchingOrRecording(...)
        """ 
        tuners = self.db().getTuners()
        from enums import TVState
        for tuner in tuners:
            tvState = int(self._sendRequest(self.cmdSock, ["QUERY_REMOTEENCODER %d"%tuner.tunerId, "GET_STATE" ])[0])
            
            if tvState == TVState.OK:  # not busy
                break
            elif tvState == TVState.Error:
                log.warning('QUERY_REMOTEENCODER::GET_STATE = Error')
                break
            elif tvState in [TVState.WatchingLiveTV, TVState.RecordingOnly, TVState.WatchingPreRecorded, TVState.WatchingRecording]:
                recording = self.getCurrentRecording(tuner)
                if showName == recording.title():
                    return tuner.tunerId
            else:
                break
        return -1

    @timed
    def getTunerStatus(self, tuner):
        """
        @rtype: TVSTate enum
        """
        reply = self._sendRequest(self.cmdSock, ['QUERY_REMOTEENCODER %d' % tuner.tunerId, 'GET_STATE'])
        return int(reply[0])

    @timed
    def getNumFreeTuners(self):
        return int(self._sendRequest(self.cmdSock, ['GET_FREE_RECORDER_COUNT'])[0])

    @timed
    def getNextFreeTuner(self, afterRecorderID):
        """ 
        Returns the (int recorderID, string IP, int port) of the next free recorder after the passed in int recorderID
        """
        # TODO: Write unit test
        command = 'GET_NEXT_FREE_RECORDER'
        reply = self._sendRequest(self.cmdSock, [command, str(afterRecorderID)])
        recorderID = int(reply[0])
        if reply[0] == -1:
            # No recorders available
            return None, None, None
        else:
            # Success
            backendServer = reply[1]
            backendPort = reply[2]
            return (recorderID, backendServer, int(backendPort))

    @timed
    def spawnLiveTV(self, tuner, channelNumber):
        """
        Instructs myth backend to start livetv on the given tuner and channelNumber. 
        A unique chainID is generated and returned if successful. 
        
        @type tuner: Tuner
        @type channelNumber: string 
        @return: generated chainID
        @rtype: string
        @raise ProtocolException: error 
        """
        # void SpawnLiveTV(QString chainid, bool pip, QString startchan);
        chainID = createChainID()
        pip = str(int(False))
        reply = self._sendRequest(self.cmdSock, ["QUERY_RECORDER %s" % tuner.tunerId, "SPAWN_LIVETV", chainID, pip, channelNumber])
        log.debug('spawnLiveTV response = %s' % reply)
        if not self._isOk(reply):
            raise util.ServerException('Error spawning live tv on tuner %s with reply %s' % (tuner, reply))
        return chainID
        
    @timed
    def stopLiveTV(self, tuner):
        """
        Stops live tv. Throws ServerException on error. 
        
        @param tuner: Tuner on which livetv has already been started
        """
        reply = self._sendRequest(self.cmdSock, ["QUERY_RECORDER %s" % tuner.tunerId, "STOP_LIVETV"])
        log.debug('stopLiveTV response = %s' % reply)
        if not self._isOk(reply):
            raise util.ServerException('Error stopping live tv on tuner %s with reply %s' % (tuner, reply))
                
    @timed
    def getFreeTuner(self):
        """
        Returns the (int recorderID, str IP address, int port) of a recorder that is not busy, tuple of -1 otherwise
        """
        command = 'GET_FREE_RECORDER'
        reply = self._sendRequest(self.cmdSock, [command])
        if reply[0] == "-1":
            # No recorders available
            return (-1, '', -1)
        else:
            recorderID = reply[0]
            backendServer = reply[1]
            backendPort = reply[2]
            return (int(recorderID), backendServer, int(backendPort))
               
    def finishRecording(self, tunerId):
        # TODO: Not used - consider deleting
        try:
            reply = self._sendRequest( self.cmdSock, ["QUERY_RECORDER %s"%tunerId, "FINISH_RECORDING"])
            log.debug( "FINISH RECORDING: %s" % reply)
            return self._isOk(reply)
        except:
            # TODO: Raise instead?
            log.exception('finishRecording: tunerId = %s'%tunerId)
            
    def cancelNextRecording(self, tunerId):
        # TODO: Not used - consider deleting
        try:
            reply = self._sendRequest(self.cmdSock, ["QUERY_RECORDER %s"%tunerId, "CANCEL_NEXT_RECORDING"])
            log.debug ( "CANCEL NEXT RECORDING: %s"%reply)
            return reply.upper() == "OK"
        except:
            # TODO: Raise instead?
            log.exception('cancelNextRecording: tunerId = %s'%str(tunerId))
    
    @timed                 
    def isTunerRecording(self, tunerId):
        command = ['QUERY_RECORDER %d'%tunerId, 'IS_RECORDING']
        reply = self._sendRequest(self.cmdSock, command)
        if reply[0] == "0":
            return False
        elif reply[0] == "1":
            return True
        else:
            raise util.ProtocolException, "Invalid response '%s' received for command '%s'"%(reply[0], command)
        
    def isPendingRecording(self, encID,  minutesNotice=1):
        """ Check if there is a Recording Pending on this encoder (Used by OSD) """
        # TODO: Not used - consider deleting
        try:
            ## Get the seconds till the NEXT recording on this Encoder in the next 5 minutes!
            recordings = self.getUpcomingRecordings(6)
            for r in recordings:
                # Might be inputid() or sourceid() ???
                if str(r.getTunerId()) == str(encID):
                    stTime = r.recstarttime()
                    ## If the rec start time isn't set use the normal start time!
                    if int(stTime) == 0:
                        stTime = r.starttimets()

                    nxtTime = int(stTime) - int(time.time())
                    if nxtTime < ( 60 * minutesNotice ) and nxtTime > 0:
                        log.debug("Found pending recording for Encoder %s and it starts in %s seconds" % ( str(encID), str(nxtTime) ) )
                        return [r.title(),r.subtitle(),nxtTime]
        except:
            # TODO: Raise instead?
            log.exception('isPendingRecording: encID = %d  minutesNotice = %s'%(encID, minutesNotice))
        return None
                    
    def getTunerFilePosition(self, tuner):
        """For a tuner that is recording, return the current position in the file as an int"""
        reply = self._sendRequest(self.cmdSock, ["QUERY_RECORDER %d" % tuner.tunerId, "GET_FILE_POSITION"])
        return util.decodeLongLong(int(reply[1]), int(reply[0]))

    @timed
    def deleteRecording(self, program):
        """
        @type program: RecordedProgram
        @return: 1 on success, 0 on failure
        """
        msg = program.data()[:]
        msg.insert(0, 'DELETE_RECORDING')
        msg.append('0')
        reply = self._sendRequest(self.cmdSock, msg)
        if sre.match('^-?\d+$', reply[0]):
            rc = int(reply[0])
        else:
            raise util.ServerException, reply[0]
        log.debug("deleted recording %s with response %s" % (program.title(), rc))
        return rc

    @timed
    def rerecordRecording(self, program):
        """
        Deletes a program and allows it to be recorded again. 
        
        @type program: RecordedProgram
        @return: 1 on success, 0 on failure
        """
        rc1 = self.deleteRecording(program)
        
        msg = program.data()[:]
        msg.insert(0, 'FORGET_RECORDING')
        msg.append('0')
        reply = self._sendRequest(self.cmdSock, msg)
        if sre.match('^-?\d+$', reply[0]):
            rc2 = int(reply[0])
        else:
            raise util.ServerException, reply[0]
        log.debug("allowed re-record of %s with response %s" %(program.title(), rc2))
        return rc1

    @timed
    def generateThumbnail(self, program, backendHost):
        """
        Request the backend generate a thumbnail for a program. The backend generates 
        the thumbnail and persists it do the filesystem regardless of whether a 
        thumbnail existed or not. Thumbnail filename = recording filename + '.png'  
        
        @type program: Program
        @param backendHost: hostname of the myth backend which recorded the program
        @type backendHost: string
        @return: True if successful, False otherwise 
        """
        msg = program.data()[:]
        
        # clear out fields - this is based on what mythweb does
        # mythtv-0.16
        msg[0] = ' '    # title
        msg[1] = ' '    # subtitle
        msg[2] = ' '    # description
        msg[3] = ' '    # category
                        # chanid
        msg[5] = ' '    # channum
        msg[6] = ' '    # chansign
        msg[7] = ' '    # channame
                        # filename
        msg[9] = '0'    # upper 32 bits
        msg[10] = '0'   # lower 32 bits
                        # starttime
                        # endtime
        msg[13] = '0'   # conflicting
        msg[14] = '1'   # recording
        msg[15] = '0'   # duplicate
                        # hostname
        msg[17] = '-1'  # sourceid
        msg[18] = '-1'  # cardid
        msg[19] = '-1'  # inputid
        msg[20] = ' '   # recpriority
        msg[21] = ' '   # recstatus  - really int
        msg[22] = ' '   # recordid
        msg[23] = ' '   # rectype
        msg[24] = '15'  # dupin
        msg[25] = '6'   # dupmethod
                        # recstarttime
                        # recendtime
        msg[28] = ' '   # repeat
        msg[29] = ' '   # program flags
        msg[30] = ' '   # recgroup
        msg[31] = ' '   # commfree
        msg[32] = ' '   # chanoutputfilters
                        # seriesid
                        # programid
                        # dummy lastmodified
                        
        msg[36] = '0'   # dummy stars
                        # dummy org airdate
        msg[38] = '0'   # hasAirDate
        msg[39] = '0'   # playgroup
        msg[40] = '0'   # recpriority2
        msg[41] = '0'   # parentid
                        # storagegroup
        msg.append('')  # trailing separator
        msg.insert(0, 'QUERY_GENPIXMAP')

        # if a slave backend, establish a new connection otherwise reuse existing connection to master backend.        
        if backendHost != self.settings.getMythTvHost():
            s = self.connect(Playback=False, Monitor=True, slaveBackend=backendHost)
            reply = self._sendRequest(s, msg)
            result = self._isOk(reply)
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        else:
            reply = self._sendRequest(self.cmdSock, msg)
            result = self._isOk(reply)
        return result

    @timed
    def getThumbnailCreationTime(self, program, backendHost):
        """
        Get the time at which the thumbnail for a program was generated.
    
        @type program: Program
        @type backendHost: string
        @return: datetime of thumbnail generation or None if never generated or error
        """
        msg = program.data()[:]
        
        # clear out fields - this is based on what mythweb does
        # mythtv-0.16
        msg[0] = ' '    # title
        msg[1] = ' '    # subtitle
        msg[2] = ' '    # description
        msg[3] = ' '    # category
                        # chanid
        msg[5] = ' '    # channum
        msg[6] = ' '    # chansign
        msg[7] = ' '    # channame
                        # filename
        msg[9] = '0'    # upper 32 bits
        msg[10] = '0'   # lower 32 bits
                        # starttime
                        # endtime
        msg[13] = '0'   # conflicting
        msg[14] = '1'   # recording
        msg[15] = '0'   # duplicate
                        # hostname
        msg[17] = '-1'  # sourceid
        msg[18] = '-1'  # getTunerId
        msg[19] = '-1'  # inputid
        msg[20] = ' '   # recpriority
        msg[21] = ' '   # recstatus - really int
        msg[22] = ' '   # recordid
        msg[23] = ' '   # rectype
        msg[24] = '15'  # dupin
        msg[25] = '6'   # dupmethod
                        # recstarttime
                        # recendtime
        msg[28] = ' '   # repeat
        msg[29] = ' '   # program flags
        msg[30] = ' '   # recgroup
        msg[31] = ' '   # commfree
        msg[32] = ' '   # chanoutputfilters
                        # seriesid
                        # programid
                        # dummy lastmodified
                        
        msg[36] = '0'   # dummy stars
                        # dummy org airdate
        msg[38] = '0'   # hasAirDate
        msg[39] = '0'   # playgroup
        msg[40] = '0'   # recpriority2
        msg[41] = '0'   # parentid
                        # storagegroup
        msg.append('')  # trailing separator
        msg.insert(0, 'QUERY_PIXMAP_LASTMODIFIED')

        if backendHost == self.settings.getMythTvHost():
            reply = self._sendRequest(self.cmdSock, msg)
        else: 
            s = self.connect(Playback=False, Monitor=True, slaveBackend=backendHost)
            reply = self._sendRequest(s, msg)
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        
        if reply == None or len(reply) == 0 or reply[0] == 'BAD':
            dt = None
        else:
            dt = datetime.datetime.fromtimestamp(float(reply[0]))
        return dt
    
    @timed
    def getScheduledRecordings(self):
        """
        @return: RecordedProgram[] (even though not yet recorded) ordered by title. 
                 Not much else of the returned data is of any use. The good stuff is in
                 getUpcomingRecordings()
        """
        scheduledRecordings = []
        reply = self._sendRequest(self.cmdSock, ['QUERY_GETALLSCHEDULED'])
        cnt = int(reply[0])
        offset = 1
        import injected
        for i in range(0, cnt):
            scheduledRecordings.append(
                injected.InjectedRecordedProgram(
                    reply[offset:(offset+self.protocol.recordSize())],
                    self.settings, 
                    self.translator,
                    self.platform))
            offset += self.protocol.recordSize()
        return scheduledRecordings
        
    # TODO: Verify MANUAL_OVERRIDE == ForceRecord from mythweb
    UPCOMING_SCHEDULED = (enums.RecordingStatus.WILL_RECORD, enums.RecordingStatus.MANUAL_OVERRIDE)
    # TODO: MythWeb has 'NeverRecord' ... what is the equivalent enum?
    UPCOMING_DUPLICATES = (enums.RecordingStatus.PREVIOUS_RECORDING, enums.RecordingStatus.CURRENT_RECORDING)
    UPCOMING_CONFLICTS = (enums.RecordingStatus.CONFLICT, enums.RecordingStatus.OVERLAP)
    # TODO: All else...
    UPCOMING_DEACTIVATED = () 
    
    @timed
    def getUpcomingRecordings(self, filter=UPCOMING_SCHEDULED):
        """
        @type filter: UPCOMING_*
        @rtype: RecordedProgram[]
        
        From mythweb:
        
       // Skip scheduled shows?
        if (in_array($show->recstatus, array('WillRecord', 'ForceRecord'))) {
            if (!$_SESSION['scheduled_recordings']['disp_scheduled'] || $_GET['skip_scheduled'])
                continue;
        }
        // Skip conflicting shows?
        elseif (in_array($show->recstatus, array('Conflict', 'Overlap'))) {
            if (!$_SESSION['scheduled_recordings']['disp_conflicts'] || $_GET['skip_conflicts'])
                continue;
        }
        // Skip duplicate or ignored shows?
        elseif (in_array($show->recstatus, array('NeverRecord', 'PreviousRecording', 'CurrentRecording'))) {
            if (!$_SESSION['scheduled_recordings']['disp_duplicates'] || $_GET['skip_duplicates'])
                continue;
        }
        // Skip deactivated shows?
        elseif ($show->recstatus != 'Recording') {
            if (!$_SESSION['scheduled_recordings']['disp_deactivated'] || $_GET['skip_deactivated'])
                continue;
        }
        // Show specific recgroup only
        if (($_SESSION['scheduled_recordings']['disp_recgroup'] && $show->recgroup != $_SESSION['scheduled_recordings']['disp_recgroup'])
            || ($_GET['recgroup'] && $show->recgroup != $_GET['recgroup']))
            continue;
        // Show specific title only
        if (($_SESSION['scheduled_recordings']['disp_title'] && $show->title != $_SESSION['scheduled_recordings']['disp_title'])
            || ($_GET['title'] && $show->title != $_GET['title']))
            continue;
        // Assign a reference to this show to the various arrays
        $all_shows[] =& $Scheduled_Recordings[$callsign][$starttime][$key];
        }
        """
        upcoming = []
        reply = self._sendRequest(self.cmdSock, ['QUERY_GETALLPENDING', '2'])
        numRows = int(reply[1])
        offset = 2

        import injected
        for i in range(0, numRows):
            program = injected.InjectedRecordedProgram(
                    reply[offset:(offset+self.protocol.recordSize())],
                    self.settings, 
                    self.translator,
                    self.platform)
            if program.getRecordingStatus() in filter:
                upcoming.append(program)
            offset += self.protocol.recordSize()
        return upcoming

    @timed
    def getAllRecordings(self):
        """
        @return: RecordedProgram[]
        """
        query='QUERY_RECORDINGS Delete' # Delete implies order recordings newest to oldest
        programs = []
        reply = self._sendRequest(self.cmdSock, [query])   
        numPrograms = int(reply[0])
        offset = 1
        recordSize = self.protocol.recordSize()
        import injected
        for i in range(0, numPrograms):
            programs.append(injected.InjectedRecordedProgram(reply[offset:offset+recordSize], self.settings, self.translator, self.platform))
            offset += recordSize
        return programs
    
    @timed
    def getRecordings(self, recordingGroup='default', title='all shows'):
        """
        Returns a list of RecordedProgram for the given recording group and show title (both case insensetive).
        
        @param recordingGroup: Recording group name or 'All Groups'
        @type recordingGroup: string
        @param title: Title of program or 'All Shows'
        @type title: string
        @rtype: RecordedProgram[]
        """
        # TODO: Optimize so it doesn't get all recordings and filters locally
        query='QUERY_RECORDINGS Delete' # Delete implies order recordings newest to oldest
        log.debug("getting recordings matching (%s, %s, %s)" % (query, recordingGroup, title))
 
        retRows = []
        offset = 0
        reply = self._sendRequest(self.cmdSock, [query])   
        numRows = int(reply[0])
        offset += 1
        
        recordingGroup = recordingGroup.upper()
        title = title.upper()
        
        import injected
        for i in range(0, numRows):
            tmpArray = reply[offset:offset+self.protocol.recordSize()]
            if ((tmpArray[30].upper() == recordingGroup or recordingGroup == "ALL GROUPS") and 
                (tmpArray[0].upper() == title or title == "ALL SHOWS")):
                retRows.append(injected.InjectedRecordedProgram(tmpArray, self.settings, self.translator, self.platform))
            offset += self.protocol.recordSize()
        return retRows

    @timed
    def getBookmark(self, program):
        """
        Return the frame number of the bookmark as a long for the passed in program or 
        zero if no bookmark is found.
        """
        command = 'QUERY_BOOKMARK %s %s' %(program.getChannelId(), program.starttimets())
        reply = self._sendRequest(self.cmdSock, [command])
        bookmarkFrame = util.decodeLongLong(int(reply[1]), int(reply[0])) 
        log.debug('bookmarkFrame = int %s int %s => long %s' %(reply[0], reply[1], bookmarkFrame))
        return bookmarkFrame
    
    @timed
    def setBookmark(self, program, frameNumber):
        """
        Sets the bookmark for the given program to frameNumber. 
        Raises ServerException on failure.
        """
        lowWord, highWord = util.encodeLongLong(frameNumber)
        command = 'SET_BOOKMARK %s %s %s %s' %(program.getChannelId(), program.starttimets(), highWord, lowWord)
        reply = self._sendRequest(self.cmdSock, [command])
        
        if reply[0] == 'OK':
            log.debug("Bookmark frameNumber set to %s" % frameNumber)
        elif reply[0] == 'FAILED':
            raise util.ServerException(
                "Failed to save position in program '%s' to frame %s. Server response: %s" %(
                program.title(), frameNumber, reply[0]))
        else:
            raise util.ProtocolException('Unexpected return value: %s' % reply[0])
    
    @timed
    def getCommercialBreaks(self, program):
        """
        @type program: RecordedProgram
        @return: List of commercial breaks for the given recording in chronological order
        @rtype: CommercialBreak[]
        """
        COMM_START = 4
        COMM_END   = 5
        
        command = 'QUERY_COMMBREAK %s %s' %(program.getChannelId(), program.starttimets())
        reply = self._sendRequest(self.cmdSock, [command])
        numRecs = int(reply[0])
        commBreaks = []
        
        if numRecs == -1:
            return commBreaks
        
        if numRecs % 2 != 0:
            raise util.ClientException, 'Expected an even number of comm break records but got %s instead' % numRecs
        
        fps = program.getFrameRate()
        recSize = 3
        for i in xrange(0, numRecs, 2):  # skip by 2's -- 1 for start + 1 for end
            baseIndex = i * recSize
            #log.debug('baseIndex = %s'%baseIndex)
            commFlagStart = int(reply[baseIndex + 1])
            if commFlagStart != COMM_START:
                raise util.ProtocolException, 'Expected COMM_START for record %s but got %s instead' % ((i+1), commFlagStart)
            else:
                frameHigh = int(reply[baseIndex + 2])
                frameLow  = int(reply[baseIndex + 3])
                frameStart = util.decodeLongLong(frameLow, frameHigh)
                commFlagEnd = int(reply[baseIndex + 4])
                if commFlagEnd != COMM_END:
                    raise util.ProtocolException, 'Expected COMM_END for record %s but got %s instead' %((i+2), commFlagEnd)
                else:
                    frameHigh = int(reply[baseIndex + 5])
                    frameLow  = int(reply[baseIndex + 6])
                    frameEnd = util.decodeLongLong(frameLow, frameHigh)
                    commBreaks.append(domain.CommercialBreak(util.frames2seconds(frameStart, fps), util.frames2seconds(frameEnd, fps)))
                        
        log.debug('%s commercials in %s' %(len(commBreaks), program.title()))
        return commBreaks
        
    @timed
    def getRecording(self, channelId, startTime):
        """
        @type channelId: int
        @type startTime: str or datetime.datetime
        @return: RecordedProgram or None if not found 
        """
        if isinstance(startTime, datetime.datetime):
            startTime = domain.dbTime2MythTime(startTime)
        query = 'QUERY_RECORDING TIMESLOT %s %s' % (channelId, startTime) 
        reply = self._sendRequest(self.cmdSock, [query])
        import injected
        if self._isOk(reply):
            return injected.InjectedRecordedProgram(reply[1:], self.settings, self.translator, self.platform)
        else:
            log.debug('Program not found')
            return None
    
    def getFreeSpace(self):
        """
        @return: [free space, total space, used space] as formatted strings
        @rtype: list[str * 3]
        @todo: Update so support multiple storage groups. For now, just return the stats on the first storage group
        """
        space = []
        try:
            reply = self._sendRequest( self.cmdSock, ["QUERY_FREE_SPACE"])

            # Reply indices:
            # 0 hostname,
            # 1 directory,
            # 2 1,
            # 3 -1,
            # 4 total size high
            # 5 total size low
            # 6 used size high
            # 7 used size low
            
            totalSpace = util.decodeLongLong(int(reply[6]), int(reply[5]))
            usedSpace = util.decodeLongLong(int(reply[8]), int(reply[7]))
            freeSpace = int(totalSpace) - int(usedSpace)
            space.append(util.formatSize(freeSpace, True))
            space.append(util.formatSize(totalSpace, True))
            space.append(util.formatSize(usedSpace, True))
        except:
            log.exception('getFreeSpace')
            space.append("")
            space.append("")
            space.append("")
        return space

    def getLoad(self):
        """
        Returns list of cpu loads for the last 1, 5, and 15 minutes
        """
        reply = self._sendRequest( self.cmdSock, ["QUERY_LOAD"])
        log.debug('Load = %s' % reply)
        load = []
        load.append(reply[0])
        load.append(reply[1])
        load.append(reply[2])
        return load

    def getUptime(self):
        """
        Returns a list (one element) with the uptime of the backend in seconds.
        If a non-unix based host, returns the string 'Could not determine uptime.'
        """
        # TODO: Not used - consider deleting
        reply = self._sendRequest(self.cmdSock, ["QUERY_UPTIME"])
        log.debug ('Uptime = %s' % reply)
        return reply

    @timed
    def getMythFillStatus(self):
        start = self.db().getMythSetting("mythfilldatabaseLastRunStart")
        end = self.db().getMythSetting("mythfilldatabaseLastRunEnd")
        status = self.db().getMythSetting("mythfilldatabaseLastRunStatus")
        fillStatus = "Programming guide info retrieved on %s" % start
        if end > start:
            fillStatus += " and ended on %s" % end
        fillStatus += ". %s" % status
        return fillStatus

    @timed
    def getGuideData(self):
        # TODO: Implement db.getLastShow()
        return ''
#        lastShow = self.db().getLastShow()
#        dataStatus = ""
#        if lastShow == None:
#            dataStatus = "There's no guide data available! Have you run mythfilldatabase?"
#        else:
#            timeDelt = lastShow - datetime.datetime.now()
#            daysOfData = timeDelt.days + 1
#            log.debug("days of data: %s" % daysOfData)
#            log.debug("End Date: %s Now: %s Diff: %s" % (lastShow, datetime.datetime.now(), str(lastShow - datetime.datetime.now())))
#            dataStatus = "There's guide data until %s (%s" % (lastShow.strftime("%Y-%m-%d %H:%M"), daysOfData)
#            if daysOfData == 1:
#                dataStatus += "day"
#            else:
#                dataStatus += "days"
#            dataStatus += ")."
#        if daysOfData <= 3:
#            dataStatus += "WARNING: is mythfilldatabase running?"
#        return dataStatus

    def getFileSize(self, backendPath, theHost):
        """
        Method to retrieve remote file size.  The backendPath is in the format
        described by the transferFile method.
        """
        # TODO: Not used - consider deleting
        rc = 0
        ft,s = self.annFileTransfer(theHost, backendPath)
        log.debug("ft=<%s>" % ft)
        rc = long(ft[2])
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        s = None
        return rc
    
    @timed
    def saveSchedule(self, schedule):
        """
        Saves a new schedule or updates an existing schedule and notifies
        the backend.
        
        @type schedule: Schedule
        """
        new = schedule.getScheduleId() is None
        self.db().saveSchedule(schedule)
        self.rescheduleNotify(schedule)

    @timed  
    def deleteSchedule(self, schedule):
        """
        Deletes an existing schedule and notifies the backend.
        
        @type schedule: Schedule
        """
        self.db().deleteSchedule(schedule)
        self.rescheduleNotify()
   
    @timed    
    def rescheduleNotify(self, schedule=None):
        """
        Method to instruct the backend to reschedule recordings.  If the
        schedule is not specified, all recording schedules will be rescheduled
        by the backend.
        """
        log.debug("rescheduleNotify(schedule= %s)" % schedule)
        scheduleId = 0
        if schedule:
            scheduleId = schedule.getScheduleId()
            if scheduleId is None:
                scheduleId = 0
        reply = self._sendRequest(self.cmdSock, ["RESCHEDULE_RECORDINGS %s" % scheduleId])
        if int(reply[0]) < 0:
            raise util.ServerException, "Reschedule notify failed: %s" % reply

    def transferFile(self, backendPath, destPath, backendHost):
        """
        Copy a file from the remote myththv backend to destPath on the local filesystem. 
        Valid files include recordings, thumbnails, and channel icons. 
        
        @param backendPath: myth url to file. Ex: myth://<host>:<port>/<path>
        @param destPath: path of destination file on the local filesystem. Ex: /tmp/somefile.mpg
        @param backendHost: The backend that recorded the file. When None, defaults to master backend
        @return:  0 on success, -1 on failure
        """
        rc = 0

        # TODO: Don't know if not getting the thumbnail from the master backend
        #       instead of the backend that the recording originated from
        #       works correctly.
        if backendHost ==  None:
            backendHost = self.settings.getMythTvHost()
            
        commandSocket = self.connect(False, True, backendHost)
        reply,dataSocket = self.annFileTransfer(backendHost, backendPath)
        filesize = util.decodeLongLong(reply[2], reply[1])
        log.debug("file = %s reply[0] = %s filesize = %s" % (backendPath, reply[0], filesize))
        
        maxBlockSize = 2000000 # 2MB
        remainingBytes = filesize
        fh = file(destPath, "w+b")
        maxReceived = 0
        
        while remainingBytes > 0:
            blockSize = min(remainingBytes, maxBlockSize)
            requestBlockMsg = ['QUERY_FILETRANSFER ' + reply[0], 'REQUEST_BLOCK', '%s' % blockSize]
            self._sendMsg(commandSocket, requestBlockMsg)
            
            blockTransferred = 0
            while blockTransferred < blockSize:
                expectedBytes = blockSize - blockTransferred
                log.debug("waiting for %d bytes" % expectedBytes)
                data = dataSocket.recv(expectedBytes)
                actualBytes = len(data)
                maxReceived = max(maxReceived, actualBytes)
                log.debug("received %d bytes" % actualBytes)
                blockTransferred += actualBytes
                if actualBytes > 0:
                    fh.write(data)
                    log.debug("wrote %d bytes" % actualBytes)
            
            reply = self._readMsg(commandSocket)
            log.debug("reply = %s"%reply)
            remainingBytes = remainingBytes - blockSize
            
        fh.close()
        dataSocket.shutdown(socket.SHUT_RDWR)
        dataSocket.close()
        commandSocket.shutdown(socket.SHUT_RDWR)
        commandSocket.close()
        log.debug("transferFile rc=%d" % rc)
        log.debug('max rcz size = %d' % maxReceived)
        return rc

    def _buildMsg(self, msg):
        msg = mythprotocol.separator.join(msg)
        return "%-8d%s" % (len(msg), msg)

    def _readMsg(self, s):
        retMsg = ""
        try:
            retMsg = s.recv(8)
            #wirelog.debug("REPLY: %s"%retMsg)
            reply = ""
            if retMsg.upper() == "OK":
                return "OK"
            wirelog.debug("retMsg: [%d] %s"% (len(retMsg), retMsg))
            n = int(retMsg)
            #wirelog.debug("reply len: %d" % n)
            i = 0
            while i < n:
                #wirelog.debug (" i=%d n=%d " % (i,n))
                reply += s.recv(n - i)
                i = len(reply)

            wirelog.debug("read  <- %s" % reply)
            return reply.split(mythprotocol.separator)
        except:
            log.exception("Error reading message: %s" % retMsg)
            raise

    def _sendMsg(self, s, req):
        try: 
            msg = self._buildMsg(req)
            wirelog.debug("write -> %s" % msg)
            s.send(msg)
        except:
            # TODO: Raise instead?
            wirelog.exception('Error sending msg over socket')
            
    def _sendRequest(self, s, msg):
        # TODO: should we arbitrarily re-est the conn?
        if s == None:
            s = self.connect(self.host, False, False)
            log.warn('Re-connected in _sendRequest()')
            
        self._sendMsg(s, msg)
        reply = self._readMsg(s)
        return reply
        
    def _sendRequestAndCheckReply(self, msg, errorMsg="Unexpected reply from server: "):
        """
        @todo: Unused - consider deleting
        """
        wirelog.debug( "> sendRequestAndCheckReply: %s" % msg) 
        reply = self._sendRequest(msg)
        if not self._isOk(reply):
            wirelog.debug("reply = %s" % reply)
            raise util.ServerException, errorMsg + str(reply)
        else: 
            wirelog.debug("< sendRequestAndCheckReply") 

    def _isAccept(self, msg, protocolVersion):
        """
        @todo: Unused - consuder deleting
        """
        return msg[0] == "ACCEPT" and msg[1] == str(protocolVersion)

    def _isOk(self, msg):
        """
        @type msg: str[]
        @return: True if myth response message indicates request completed OK, false otherwise
        """
        if msg == None or len(msg) == 0:
            return False
        else:
            return msg[0].upper() == "OK"

# =============================================================================
class MythSettings(object):
    """
    Settings reside in $HOME/.xbmc/userdata/script_data/MythBox/settings.xml
    """
    
    settingsTags = [
        'mythtv_host',
        'mythtv_port',
        'mythtv_minlivebufsize',
        'mythtv_tunewait',
        'mysql_host',
        'mysql_port',
        'mysql_database',
        'mysql_user',
        'mysql_password',
        'paths_recordedprefix',
        'paths_ffmpeg',
        'recorded_view_by',
        'upcoming_view_by',
        'confirm_on_delete',
        'fanart_tvdb',
        'fanart_tmdb',
        'fanart_imdb',
        'fanart_google',
        'lirc_hack',
        'logging_enabled']

    def __init__(self, platform, translator, filename='settings.xml'):
        self.platform = platform
        self.translator = translator
        self.settingsFilename = filename
        self.settingsPath = os.path.join(self.platform.getScriptDataDir(), self.settingsFilename)
        self.listeners = []
        try:
            self.load()
            self.loadMergedDefaults()
        except util.SettingsException:
            self.dom = self.loadDefaults()

    def getFFMpegPath(self): return self.get('paths_ffmpeg')
    def setFFMpegPath(self, ffmpegPath): self.put('paths_ffmpeg', ffmpegPath, True)
 
    def setLiveTvBuffer(self, sizeKB): self.put('mythtv_minlivebufsize', '%s' % sizeKB, True)
    def getLiveTvBuffer(self): return int(self.get('mythtv_minlivebufsize'))

    def setLiveTvTimeout(self, seconds): self.put('mythtv_tunewait', '%s' % seconds, True)
    def getLiveTvTimeout(self): int(self.get('mythtv_tunewait'))
     
    def isConfirmOnDelete(self): return self.getBoolean('confirm_on_delete')
    def setConfirmOnDelete(self, b): self.put('confirm_on_delete', ['False', 'True'][b], True)
            
    def getMySqlHost(self): return self.get('mysql_host')
    def setMySqlHost(self, host): self.put('mysql_host', host, True)

    def setMySqlPort(self, port): self.put('mysql_port', '%s' % port, True)
    def getMySqlPort(self): return int(self.get('mysql_port'))

    def getMySqlDatabase(self): return self.get('mysql_database')
    def setMySqlDatabase(self, db): self.put('mysql_database', db, True)
    
    def getMySqlUser(self): return self.get('mysql_user')
    def setMySqlUser(self, user): self.put('mysql_user', user, True)

    def getMySqlPassword(self): return self.get('mysql_password')
    def setMySqlPassword(self, password): self.put('mysql_password', password, True)

    def getMythTvHost(self): return self.get('mythtv_host')
    def setMythTvHost(self, host): self.put('mythtv_host', host, True)
    
    def getMythTvPort(self): return int(self.get('mythtv_port'))
    def setMythTvPort(self, port): self.put('mythtv_port', '%s' % port, True)

    def addListener(self, listener):
        self.listeners.append(listener)
        
    def setRecordingDirs(self, dirs):
        """
        @type dirs: str  - one or more separated by os.pathsep      
        @type dirs: str[] 
        """
        if type(dirs) == str:
            self.put('paths_recordedprefix', dirs)
        elif type(dirs) == list:
            self.put('paths_recordedprefix', os.pathsep.join(dirs))
        else:
            raise Exception("unsupported param type for dirs: %s" + type(dirs))
        
    def getRecordingDirs(self):
        """
        @return: MythTV recording directories on the local filesystem
        @rtype: str[]
        """
        return self.get('paths_recordedprefix').split(os.pathsep)
        
    def get(self, tag, dom=None):
        value = ""
        if not dom:
            dom = self.dom
        tmpNode = dom.getElementsByTagName(tag)[0]
        for n in tmpNode.childNodes:
            value += n.nodeValue
            
        if slog.isEnabledFor(log.debug):
            pvalue = value
            if 'password' in tag:
                pvalue = '*secret*'
            slog.debug("<= settings['%s'] = %s" % (tag, pvalue))

        return value

    def put(self, tag, value, shouldCreate=0, dom=None):
        tmpNode = None
        if not dom:
            dom = self.dom
        try:
            tmpNode = dom.getElementsByTagName(tag)[0]
        except IndexError:
            if shouldCreate != 1:
                raise
            
        if not tmpNode:
            tmpNode = dom.getElementsByTagName("mythtv")[0]
            n = dom.createElement(tag)
            tmpNode.appendChild(n)
            tmpNode = n
            
        if not tmpNode.firstChild:
            n = dom.createTextNode(value)
            tmpNode.appendChild(n)
        else:
            old = tmpNode.firstChild.nodeValue
            tmpNode.firstChild.nodeValue = value
            
            # Only notify of changes if the new value is different
            if old != value:
                for listener in self.listeners:
                    listener.settingChanged(tag, old, value)
            
        if slog.isEnabledFor(log.debug):
            pvalue = value
            if 'password' in tag:
                pvalue = '*secret*'
            slog.debug("=> settings['%s'] = %s" % (tag, pvalue))

    def loadDefaults(self):
        slog.debug('loading defaults...')
        defaultsXml = """
<mythtv>
  <mythtv_host>localhost</mythtv_host>
  <mythtv_port>6543</mythtv_port>
  <mythtv_minlivebufsize>4096</mythtv_minlivebufsize>
  <mythtv_tunewait>60</mythtv_tunewait>
  <mysql_host>localhost</mysql_host>
  <mysql_port>3306</mysql_port>
  <mysql_database>mythconverg</mysql_database>
  <mysql_user>mythtv</mysql_user>
  <mysql_password>change_me</mysql_password>
  <mysql_encoding_override>latin1</mysql_encoding_override>
  <paths_recordedprefix>""" + self.platform.getDefaultRecordingsDir() + """</paths_recordedprefix>
  <paths_ffmpeg>""" + self.platform.getFFMpegPath() + """</paths_ffmpeg>
  <recorded_view_by>2</recorded_view_by>
  <upcoming_view_by>2</upcoming_view_by>
  <confirm_on_delete>True</confirm_on_delete>
  <fanart_tvdb>True</fanart_tvdb>
  <fanart_tmdb>True</fanart_tmdb>
  <fanart_imdb>True</fanart_imdb>
  <fanart_google>True</fanart_google>
  <lirc_hack>False</lirc_hack>
  <logging_enabled>True</logging_enabled>
</mythtv>"""
        
        dom = minidom.parseString(defaultsXml)
        return dom

    def loadMergedDefaults(self):
        filePath = self.settingsPath
        dom = self.loadDefaults()
        if os.path.exists(filePath):
            for tag in self.settingsTags:
                try:
                    value = self.get(tag)
                except IndexError:
                    value = ""
                    pass
                if len(value) == 0:
                    self.put(tag, self.get(tag, dom), shouldCreate=1)

    def load(self):
        """
        @raise SettingsException: when settings file not found
        """
        filePath = self.settingsPath
        slog.debug("Loading settings from %s" % filePath)
        if not os.path.exists(filePath):
            raise util.SettingsException('File %s does not exist.' % filePath)
        else:
            # use existing configuration
            self.dom = minidom.parse(filePath)

    def save(self):
        filePath = self.settingsPath
        settingsDir = self.platform.getScriptDataDir()
        
        if not os.path.exists(settingsDir):
            slog.debug('Creating mythbox settings dir %s' % self.platform.getScriptDataDir())
            os.makedirs(settingsDir)
            
        if self.dom is not None:
            slog.debug("Saving settings to %s" % filePath)
            fh = file(filePath, 'w')
            fh.write(self.dom.toxml())
            fh.close()
        else:
            slog.error('Could not save settings. XML dom not set')

    def getBoolean(self, tag):
        return self.get(tag) in ('True', 'true', '1')
    
    def verify(self):
        """
        @raise SettingsException: on invalid settings
        """
        for tag in self.settingsTags:
            try:
                self.get(tag)
            except IndexError:
                raise util.SettingsException('%s %s' % (self.translator.get(34), tag))
        
        MythSettings.verifyMythTVHost(self.getMythTvHost())
        MythSettings.verifyMythTVPort(self.get('mythtv_port'))
        MythSettings.verifyMySQLHost(self.get('mysql_host'))
        MythSettings.verifyMySQLPort(self.get('mysql_port'))
        MythSettings.verifyMySQLDatabase(self.get('mysql_database'))
        MythSettings.verifyString(self.get('mysql_user'), 'Enter MySQL user. Hint: mythtv is the MythTV default')
        MythSettings.verifyLiveTVBufferSize(self.get('mythtv_minlivebufsize'))
        MythSettings.verifyRecordingDirs(self.get('paths_recordedprefix'))
        MythSettings.verifyFFMpeg(self.get('paths_ffmpeg'), self.platform)
        MythSettings.verifyBoolean(self.get('confirm_on_delete'), 'Confirm on delete must be True or False')
        self.verifyMySQLConnectivity()
        self.verifyMythTVConnectivity()
        slog.debug('verified settings')

    def verifyMythTVConnectivity(self):
        try:
            session = Connection(self, db=None, translator=self.translator, platform=self.platform)
            session.close()
        except Exception, ex:
            log.exception(ex)
            raise util.SettingsException("Connection to MythTV failed: %s" % ex)
    
    def verifyMySQLConnectivity(self):
        try:
            db = mythdb.MythDatabase(self, self.translator)
            db.close()
            del db
        except Exception, ex:
            raise util.SettingsException("Connect to MySQL failed: %s" % ex)
    
    def __repr__(self):
        sb = ''
        for tag in self.settingsTags:
            try:
                sb += '%s = %s\n' % (tag, self.get(tag)) 
            except IndexError:
                sb += '%s = <EMPTY>\n' % tag
        return sb
            
    @staticmethod
    def verifyFFMpeg(filepath, p): # =platform.getPlatform()
        MythSettings.verifyString(filepath, "Enter the absolute path of your ffmpeg executable")
        
        if not os.path.exists(filepath):
            raise util.SettingsException("ffmpeg executable '%s' does not exist." % filepath)
        
        if not os.path.isfile(filepath):
            raise util.SettingsException("ffmpeg executable '%s' is not a file" % filepath)
        
        ptype = type(p)
        if ptype in (mythbox.WindowsPlatform, mythbox.MacPlatform):
            pass
        elif ptype == mythbox.UnixPlatform:
            if not os.access(filepath, os.X_OK):
                raise util.SettingsException("ffmpeg executable '%s' is not chmod +x" % filepath)
        else:
            raise util.SettingsException('Verifying FFMPEG - unsupported platform: %s' % ptype)
    
    @staticmethod    
    def verifyRecordingDirs(recordingDirs):
        MythSettings.verifyString(recordingDirs, "Enter one or more '%s' separated MythTV recording directories" % os.pathsep)
        for dir in recordingDirs.split(os.pathsep):
            if not os.path.exists(dir):
                raise util.SettingsException("Recording directory '%s' does not exist." % dir)
            if not os.path.isdir(dir):
                raise util.SettingsException("Recording directory '%s' is not a directory." % dir)
    
    @staticmethod        
    def verifyMythTVHost(host):
        MythSettings.verifyString(host, 'Enter MythTV master backend hostname or IP address')
        MythSettings.verifyHostnameOrIPAddress(host, "Hostname '%s' cannot be resolved to an IP address."%host)
    
    @staticmethod
    def verifyMythTVPort(port):
        errMsg = 'Enter MythTV master backend port. Hint: 6543 is the MythTV default'
        MythSettings.verifyString(port, errMsg)
        MythSettings.verifyNumberBetween(port, 1, 65536, errMsg)
        
    @staticmethod    
    def verifyMySQLHost(host):
        MythSettings.verifyString(host, 'Enter MySQL server hostname or IP address')
        MythSettings.verifyHostnameOrIPAddress(host, "Hostname '%s' cannot be resolved to an IP address." % host)

    @staticmethod
    def verifyMySQLPort(port):
        errMsg = 'Enter MySQL server port. Hint: 3306 is the MySQL default'
        MythSettings.verifyString(port, errMsg)
        MythSettings.verifyNumberBetween(port, 0, 65336, errMsg)

    @staticmethod
    def verifyMySQLUser(user):
        errMsg = 'Enter MySQL user name for MythTV database'
        MythSettings.verifyString(user, errMsg)
        
#    @staticmethod
#    def verifyTuneWait(numSeconds):
#        errMsg = 'Enter time to wait for tuning in seconds (1-60)'
#        MythSettings.verifyString(numSeconds, errMsg)
#        MythSettings.verifyNumberBetween(numSeconds, 1, 60, errMsg)
    
    @staticmethod    
    def verifyMySQLDatabase(dbName):
        MythSettings.verifyString(dbName, 'Enter MySQL database name. Hint: mythconverg is the MythTV default')
    
    @staticmethod    
    def verifyLiveTVBufferSize(numKB):
        MythSettings.verifyString(numKB, 'Live TV buffer size must be between 1,000 and 20,000 KB')
        MythSettings.verifyNumberBetween(numKB, 1000, 20000, 'Live TV buffer size must be between 1,000 and 20,000 KB')

    @staticmethod    
    def verifyLiveTVTimeout(numSecs):
        MythSettings.verifyString(numSecs, 'Live TV timeout must be between 10 and 180 seconds')
        MythSettings.verifyNumberBetween(numSecs, 10, 180, 'Live TV timeout must be between 10 and 180')
        
    @staticmethod    
    def verifyHostnameOrIPAddress(host, errMsg):
        try:
            socket.gethostbyname(host)
        except Exception:
            raise util.SettingsException("%s %s" % (errMsg, ''))

    @staticmethod
    def verifyBoolean(s, errMsg):
        MythSettings.verifyString(s, errMsg)
        if not s in ('True', 'False', '0', '1'):
            raise util.SettingsException(errMsg)
            
    @staticmethod
    def verifyString(s, errMsg):
        """
        @param s: string to verify
        @param errMsg: Error message
        @raise util.SettingsException: if passed in string is None or blank. 
        """
        if s is None or s.strip() == '':
            raise util.SettingsException(errMsg)
    
    @staticmethod    
    def verifyNumberBetween(num, min, max, errMsg):
        n = None
        try:
            n = int(num)
        except Exception:
            raise util.SettingsException("%s %s" % (errMsg, ''))
        if not min <= n <= max:
            raise util.SettingsException(errMsg)

# =============================================================================
class MythThumbnailResolver(filecache.FileResolver):
    
    def __init__(self, conn=None):
        self._conn = conn
            
    def conn(self):
        return self._conn
    
    def store(self, program, dest):
        """
        @type program : RecordedProgram  
        @param dest: file to save downloaded program thumbnail to
        """
        if self.conn().getThumbnailCreationTime(program, program.hostname()) is None:
            self.conn().generateThumbnail(program, program.hostname())
        self.conn().transferFile(program.getRemoteThumbnailPath(), dest, program.hostname())
            
    def hash(self, program):
        return md5.new(program.getRemoteThumbnailPath()).hexdigest()
        
# =============================================================================
class MythChannelIconResolver(filecache.FileResolver):
    
    def __init__(self, conn=None):
        self._conn = conn
            
    def conn(self):
        return self._conn
    
    def store(self, channel, dest):
        """
        @type channel : Channel 
        @param dest: file to save downloaded chanel icon to
        """
        if channel.getIconPath():
            # TODO: Can channel icons be requested from slave backend? Replace None with backend hostname 
            #       if this turns out to be true.
            self.conn().transferFile(channel.getIconPath(), dest, None)
        else:
            log.debug('Channel %s has no icon' % channel.getChannelName())
            
    def hash(self, channel):
        if channel.getIconPath():
            return md5.new(channel.getIconPath()).hexdigest()
                    