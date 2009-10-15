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
import logging

try:
    import MySQLdb
    cursorArgs = [MySQLdb.cursors.DictCursor]
except:
    import mysql.connector as MySQLdb
    cursorArgs = []
    
import string
import pool
        
from decorator import decorator
from util import timed, threadlocals
        
log = logging.getLogger('mythtv.core')
ilog = logging.getLogger('mythtv.inject')

# =============================================================================
def mythtime2dbtime(mythtime):
    """
    Turn 001122 -> 00:11:22
    """
    return mythtime[0:2] + ':' + mythtime[2:4] + ':' + mythtime[4:6]

# =============================================================================
def mythdate2dbdate(mythdate):
    """
    Turn 20080102 -> 2008-01-02
    """
    return mythdate[0:4] + '-' + mythdate[4:6] + '-' + mythdate[6:8]

# =============================================================================
def quote(someValue):
    if someValue is None:
        return 'None'
    else:
        return "'" + str(someValue) + "'"

# =============================================================================
class MythDatabaseFactory(pool.PoolableFactory):
    
    def __init__(self, *args, **kwargs):
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
    
    def create(self):
        db = MythDatabase(self.settings, self.translator)
        return db
    
    def destroy(self, db):
        db.close()
        del db

# =============================================================================
class MythDatabase(object):

    def __init__(self, settings, translator):
        self.settings = settings
        self.translator = translator
        self.conn = None
        self.initialise()
    
    @timed        
    def initialise(self):
        log.debug("Initializing myth database connection")
        self.conn = MySQLdb.connect(
            host = self.settings.get("mysql_host").encode('utf-8'), 
            db = self.settings.get("mysql_database").encode('utf-8'),
            user = self.settings.get("mysql_user").encode('utf-8'),
            #passwd = self.settings.get("mysql_password"),
            password = self.settings.get("mysql_password").encode('utf-8'),
            port = int(self.settings.get("mysql_port")),
            #connect_timeout = 30)
            connection_timeout = 30)
        
        # TODO: Only set converter if using pure python mysql connector
        #self.conn.set_converter_class(CustomMySQLConverter)
        
    def close(self):
        if self.conn:
            log.debug('Closing myth db connection')
            self.conn.close()
            del self.conn

    @timed
    def getChannels(self):
        """
        Return viewable channels across all tuners.
        
        @return: Channel[]
        """
        # TODO: Consider caching since channels aren't likely to change 
        sql = """
            select
                ch.chanid, 
                ch.channum, 
                ch.callsign, 
                ch.name, 
                ch.icon, 
                ci.cardid
            from 
                channel ch,
                cardinput ci 
            where 
                ch.channum is not null
                and ch.channum != ''
                and ch.visible = 1
                and ch.sourceid = ci.sourceid
            order by 
                ch.chanid
            """
            
        channels = []
        cursor = self.conn.cursor(*cursorArgs)
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            for r in rows:
                r = self.toDict(cursor, r)
                channels.append(domain.Channel(r))
        finally:
            cursor.close()
        return channels
    
    @timed            
    def getRecordingGroups(self):
        """
        @return: List of [recording group name, # recordings]
        """
        sql = """
            select  
                distinct recgroup, 
                count(recgroup) as cnt 
            from 
                recorded 
            group by 
                recgroup asc
            """
        recordingGroups = []
        cursor = self.conn.cursor(*cursorArgs)
        try:
            cursor.execute(sql)
            recordingGroups.append(["All Groups", 0])
            grpcnt = 0
            for row in cursor.fetchall():
                row = self.toDict(cursor, row)
                thisRow = ["",0]
                for k in row.keys():
                    if k.find("cnt") >= 0:
                        grpcnt += int(row[k])
                        thisRow[1] = int(row[k])
                    else:
                        thisRow[0] = str(row[k])
                recordingGroups.append(thisRow)
            recordingGroups[0][1] = grpcnt
        finally:
            cursor.close()
        return recordingGroups
          
    @timed            
    def getRecordingTitles(self, recordingGroup):
        """
        @param recordingGroup: 'All Groups' or any valid recording group.
        @type recordingGroup: string
        @rtype: list[0] = ('All Shows', total # of shows)
                list[1..n] = (title, # recordings) 
        @return: for the given string recording group ['All Shows', total # of shows] 
                 is always the first index of the returned list regardless of the 
                 recording group.
        """

        sql = """
          select  
              distinct title, 
              count(title) as cnt 
          from 
              recorded
          """
          
        if string.upper(recordingGroup) != "ALL GROUPS":
            sql += " where recgroup='%s' " % str(recordingGroup)
        
        sql += " group by title asc"

        # TODO: What a mess! This is now NOT to do it... 
        titlegroups = []
        cursor = self.conn.cursor(*cursorArgs)
        try:
            cursor.execute(sql)
            titlegroups.append(['All Shows', 0])
            grpcnt = 0
            for row in cursor.fetchall():
                row = self.toDict(cursor, row)
                thisRow = ['', 0]
                for k in row.keys():
                    if k == 'cnt':
                        grpcnt += int(row[k])
                        thisRow[1] = int(row[k])
                    else:
                        thisRow[0] = row[k]
                titlegroups.append(thisRow)
            titlegroups[0][1] = grpcnt
        finally:
            cursor.close()
        return titlegroups

    @timed
    def getTuners(self):
        """
        @rtype: Tuner[] 
        @return: Tuners ordered by cardid 
        """
        # TODO: Consider caching after first invocation - data is static for the most part
        sql = \
            """
            select 
                cardid, 
                hostname, 
                signal_timeout, 
                channel_timeout, 
                cardtype
            from   
                capturecard
            order by 
                cardid
            """
        tuners = []
        cursor = self.conn.cursor(*cursorArgs)
        
        try:
            cursor.execute(sql)
            import injected
            for row in cursor.fetchall():
                row = self.toDict(cursor, row)
                tuners.append(injected.InjectedTuner(
                    int(row['cardid']),
                    row['hostname'],
                    int(row['signal_timeout']),
                    int(row['channel_timeout']),
                    row['cardtype']))
        finally:
            cursor.close()
        return tuners

    @staticmethod
    def toDict(cursor, row):
        if isinstance(row, dict):
            return row
        elif isinstance(row, list) or isinstance(row, tuple):
            #log.debug('%s' % type(row))
            rowDict = dict()
            # cursor.description is a list(tuple(columnName, other crap))
            for i, field in enumerate(cursor.description):
                rowDict[field[0]] = row[i] 
            #    log.debug('%s %s' % (type(r),r))
            return rowDict
        else:
            raise Exception, 'Unknown row type: %s' % type(row)
        
    @timed
    def getProgramListings(self, startTime, endTime, startChanId=None, endChanId=None):
        """
        Get tv listings for given time period and channel range.
        
        @type startTime: datetime.datetime 
        @type endTime: datetime.datetime 
        @param startChanId: Starting channel id as int
        @param endChanId: Ending channel id as int
        @rtype: TVProgram[]
        
        TODO: Rename to getTVListings() or getProgramGuideListings() ?
        """
        strStartTime = startTime.strftime("%Y%m%d%H%M%S")
        strEndTime = endTime.strftime("%Y%m%d%H%M%S")
        
        sql = """
            select
                channel.chanid,
                channel.channum,
                channel.callsign,
                channel.icon,
                channel.name as channame,                
                program.starttime,
                program.endtime,
                program.title,
                program.subtitle,
                program.description,
                program.showtype,
                program.originalairdate,
                program.category,
                program.category_type,
                program.seriesid,
                program.programid
            from 
                channel,
                program
            where
                channel.visible = 1
                and channel.chanid = program.chanid
                and program.starttime != program.endtime
                and 
                (   
                       (program.endtime   >  %s and program.endtime   <= %s) 
                    or (program.starttime >= %s and program.starttime <  %s) 
                    or (program.starttime <  %s and program.endtime   >  %s) 
                    or (program.starttime =  %s and program.endtime   =  %s)
                )
                """ % (strStartTime, strEndTime,
                       strStartTime, strEndTime,
                       strStartTime, strEndTime,
                       strStartTime, strEndTime)
        
        if startChanId and endChanId:
            sql += """
                and channel.chanid >= '%d'
                and channel.chanid <= '%d'
                """%(startChanId, endChanId)
        sql += " order by channel.chanid, program.starttime"

        programs = []
        cursor = self.conn.cursor(*cursorArgs)
        try:
            cursor.execute(sql)
            for row in cursor.fetchall():
                #log.debug(str(type(row)) + " " + str(row))
                programs.append(domain.TVProgram(self.toDict(cursor, row), self.translator))
        finally:
            cursor.close()
        return programs

    @timed
    def getMythSetting(self, key, hostname=None):
        """Returns the value from the Settings Table for the given key and hostname, None otherwise"""
        sql = """
            select
                data
            from
                settings 
            where
                value = "%s"
            """%(str(key))
            
        if hostname is not None:
            sql += ' and hostname = "%s"' % hostname
                   
        result = None
        cursor = self.conn.cursor(*cursorArgs)
        try:
            cursor.execute(sql)
            for row in cursor.fetchall():
                row = self.toDict(cursor, row)
                result = str(row["data"])
        finally:
            cursor.close()
        log.debug("<= mythsettings['%s', %s] = %s"%(key, hostname, result))
        return result
        
    @timed
    def getRecordingSchedules(self, chanId="", scheduleId=-1):
        """
        Returns all recording schedules unless a specific channel or recording
        schedule ID is specified.
        
        Return Type: RecordingSchedule[]
        """
        log.debug("getting schedule for scheduleId = %s"%scheduleId)
        sql = """
            SELECT
                r.recordid,
                r.type,
                r.chanid,
                r.starttime,
                r.startdate,
                r.endtime,
                r.enddate,
                r.title,
                r.subtitle,
                r.description,
                r.category,
                r.profile,
                r.recpriority,
                r.autoexpire,
                r.maxepisodes,
                r.maxnewest,
                r.startoffset,
                r.endoffset,
                r.recgroup,
                r.dupmethod,
                r.dupin,
                r.station,
                r.seriesid,
                r.programid,
                r.search,
                r.autotranscode,
                r.autocommflag,
                r.autouserjob1,
                r.autouserjob2,
                r.autouserjob3,
                r.autouserjob4,
                r.findday,
                r.findtime,
                r.findid,
                r.inactive,
                r.parentid,
                c.channum,
                c.callsign,
                c.name as channame,
                c.icon
            FROM
                record r
            LEFT JOIN channel c ON r.chanid = c.chanid
            """
            
        if chanId != "":
            sql += "WHERE r.chanid = '%s' "%chanId
            
        if scheduleId != -1:
            if chanId == "":
                sql+="WHERE "
            else:
                sql +="AND "
            sql += "r.recordid = %d "%scheduleId
            
        sql += """
            ORDER BY
                r.recordid
                DESC
            """
        schedules = []
        cursor = self.conn.cursor(*cursorArgs)
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                row = self.toDict(cursor, row)
                schedules.append(domain.RecordingSchedule(row, self.translator))
        finally:
            cursor.close()
        return schedules

    def updateJobScheduledRunTime(self, job):
 
        sql = "update jobqueue set schedruntime = %(scheduledRunTime)s where id = %(jobId)s and starttime = %(startTime)s"
            
        log.debug("sql = %s"%sql)

        cursor = self.conn.cursor()
        try:
            # args that need escaping
            args = {
                'scheduledRunTime': job.scheduledRunTime,
                'jobId' : job.id,
                'startTime' : job.startTime
            }
            
            cursor.execute(sql, args)
            log.debug('Row count = %s' % cursor.rowcount)
        finally:
            cursor.close()
        
    def getJobs(self, program=None, jobType=None, jobStatus=None):
        """
        Get jobs from the MythTV job queue matching a program, job type, and/or job status.
        
        @type program: RecordedProgram
        @type jobType: int from enums.JobTye
        @type jobStatus: int from enums.JobStatus
        @rtype: Job[]
        """
        
        sql = """
            select
                id, 
                chanid, 
                starttime, 
                inserttime, 
                type, 
                cmds, 
                flags, 
                status,
                statustime,
                hostname, 
                comment,
                schedruntime 
            from   
                jobqueue
            """
        
        where = ''
        if program is not None:
            where += "chanid = %s " % program.getChannelId()
            where += "and "
            where += "starttime = '%s' " % program.starttimeAsTime()
            
        if jobType is not None:
            if program is not None:
                where += " and "
            where += "type = %d " % jobType
        
        if jobStatus is not None:
            if program is not None or jobType is not None:
                where += " and "
            where += "status = %d " % jobStatus
                
        if where != '':
            sql += " where " + where
            
        sql += " order by schedruntime, id"
        
        log.debug('%s' % sql)
        
        jobs = []
        cursor = self.conn.cursor(*cursorArgs)
        try:
            cursor.execute(sql)
            import injected
            for row in cursor.fetchall():
                row = self.toDict(cursor, row)
                jobs.append(
                    injected.InjectedJob(
                        id=int(row['id']), 
                        channelId=int(row['chanid']), 
                        startTime=row['starttime'], 
                        insertTime=row['inserttime'], 
                        jobType=row['type'], 
                        cmds=row['cmds'], 
                        flags=row['flags'], 
                        jobStatus=row['status'],
                        statusTime=row['statustime'],
                        hostname=row['hostname'],
                        comment=row['comment'],
                        scheduledRunTime=row['schedruntime'],
                        translator=self.translator))
        finally:
            cursor.close()
        return jobs

    def setRecordingAutoexpire(self, program, shouldExpire):
        """
        Set the autoexpire setting for a recorded program.
        
        @param param: RecordedProgram
        @param shouldExpire: boolean
         
        chanid, starttime, shouldExpire = 0
        """
        raise NotImplementedError("TODO setRecordingAutoexpire")
        # TODO: Convert impl to mysql native client
        #sql = """
        #    update recorded set
        #        autoexpire = "%d",
        #        starttime = '%s'
        #    where
        #        chanid = '%s'
        #        and starttime = '%s'
        #"""%(shouldExpire, starttime, chanid, starttime)
        #
        #log.debug("sql = %s"%sql)
        #
        #rc = self.conn.executeSQL(sql)
        #if rc != 1:
        #    raise ClientException, self.conn.getErrorMsg()

    @timed
    def deleteSchedule(self, schedule):
        """
        Delete a recording schedule.
        
        @type schedule: Schedule 
        @return: Number of rows deleted from the 'record' table
        """
        sql = "DELETE FROM record WHERE recordid = %d" % schedule.getScheduleId()
        log.debug(sql)

        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            return cursor.rowcount
        finally:
            cursor.close()
    
    @timed
    def saveSchedule(self, schedule):
        """
        Method to save a schedule to the database. If getScheduleId() is None in the
        passed in schedule, then it will be populated with an id and returned from
        database (i.e. a new one will be created).

        Connection.rescheduleNotify() must be called after scheduling changes
        have been made so that the backend will apply the changes.

        @param schedule: Schedule
        @return: 0 on success
        @raise ClientException: On error
        """
        s = schedule
        
        recordid = s.getScheduleId()
        if not recordid:
            recordid = 'NULL'
            
        programid = s.programid()
        if not programid:
            programid = ""

        seriesid = s.seriesid()
        if not seriesid:
            seriesid = ""
            
#        sql = """
#            REPLACE INTO record (
#                recordid, 
#                type,
#                chanid, 
#                starttime,
#                startdate, 
#                endtime,
#                enddate, 
#                title,
#                subtitle, 
#                description,
#                category, 
#                profile,
#                recpriority, 
#                autoexpire,
#                maxepisodes, 
#                maxnewest,
#                startoffset, 
#                endoffset,
#                recgroup, 
#                dupmethod,
#                dupin, 
#                station,
#                seriesid, 
#                programid,
#                search, 
#                autotranscode,
#                autocommflag, 
#                autouserjob1,
#                autouserjob2, 
#                autouserjob3,
#                autouserjob4, 
#                findday,
#                findid,
#                inactive, 
#                parentid) 
#            VALUES (
#                %s, %s, %s, %s, %s, %s, %s, 
#                %%(title)s, %%(subtitle)s, %%(description)s, 
#                %s, %s, %s, %s, %s, %s, 
#                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
#                %s, %s, %s)""" % (
#                recordid, 
#                s.getScheduleType(),
#                s.getChannelId(), 
#                quote(mythtime2dbtime(s.starttime())),
#                quote(mythdate2dbdate(s.startdate())), 
#                quote(mythtime2dbtime(s.endtime())),
#                quote(mythdate2dbdate(s.enddate())), 
#                quote(s.category()),
#                quote(s.profile()),
#                s.getPriority(), 
#                int(s.isAutoExpire()),
#                s.getMaxEpisodes(), 
#                int(s.isRecordNewAndExpireOld()),
#                s.getStartOffset(), 
#                s.getEndOffset(),
#                quote(s.getRecordingGroup()), 
#                s.getCheckForDupesUsing(),
#                s.getDupin(), 
#                quote(s.station()),
#                quote(seriesid),  
#                quote(programid),
#                int(s.search()), 
#                int(s.isAutoTranscode()),
#                int(s.isAutoCommFlag()), 
#                int(s.isAutoUserJob1()),
#                int(s.isAutoUserJob2()), 
#                int(s.isAutoUserJob3()),
#                int(s.isAutoUserJob4()), 
#                int(s.findday()),
#                int(s.findid()),
#                int(not s.isEnabled()), 
#                int(s.parentid()))

        sql = """
            REPLACE INTO record (
                recordid, 
                type,
                chanid, 
                starttime,
                startdate, 
                endtime,
                enddate, 
                title,
                subtitle, 
                description,
                category, 
                profile,
                recpriority, 
                autoexpire,
                maxepisodes, 
                maxnewest,
                startoffset, 
                endoffset,
                recgroup, 
                dupmethod,
                dupin, 
                station,
                seriesid, 
                programid,
                search, 
                autotranscode,
                autocommflag, 
                autouserjob1,
                autouserjob2, 
                autouserjob3,
                autouserjob4, 
                findday,
                findid,
                inactive, 
                parentid) 
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, 
                %%s, %%s, %%s, 
                %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s)""" % (
                recordid, 
                s.getScheduleType(),
                s.getChannelId(), 
                quote(mythtime2dbtime(s.starttime())),
                quote(mythdate2dbdate(s.startdate())), 
                quote(mythtime2dbtime(s.endtime())),
                quote(mythdate2dbdate(s.enddate())), 
                #quote(s.title()),            #
                #quote(s.subtitle()),         #
                #quote(s.description()),      #
                quote(s.category()),
                quote(s.profile()),
                s.getPriority(), 
                int(s.isAutoExpire()),
                s.getMaxEpisodes(), 
                int(s.isRecordNewAndExpireOld()),
                s.getStartOffset(), 
                s.getEndOffset(),
                quote(s.getRecordingGroup()), 
                s.getCheckForDupesUsing(),
                s.getDupin(), 
                quote(s.station()),
                quote(seriesid),  
                quote(programid),
                int(s.search()), 
                int(s.isAutoTranscode()),
                int(s.isAutoCommFlag()), 
                int(s.isAutoUserJob1()),
                int(s.isAutoUserJob2()), 
                int(s.isAutoUserJob3()),
                int(s.isAutoUserJob4()), 
                int(s.findday()),
                int(s.findid()),
                int(not s.isEnabled()), 
                int(s.parentid()))

        log.debug("sql = %s"%sql)

        cursor = self.conn.cursor()
        try:
            # args that need escaping
            args = {
                'title': s.title(),
                'subtitle' : s.subtitle(),
                'description' : s.description()
            }
            
            args = (s.title(), s.subtitle(), s.description())
            cursor.execute(sql, args)
            #cursor.execute(sql)
            
            log.debug('Row count = %s' % cursor.rowcount)
        finally:
            cursor.close()
 
        # INSERT INTO `record` (
        # `recordid`,       241,  
        # `type`,           5, 
        # `chanid`,         1051, 
        # `starttime`,      '19:00:00',  
        # `startdate`,      '2008-10-06',  
        # `endtime`,        '20:00:00',  
        # `enddate`,        '2008-10-06',  
        # `title`,          'Chuck',  
        # `subtitle`,       'Chuck Versus the Seduction', 
        # `description`,    'Chuck must learn the art of seduction so he can retrieve the cipher from a sultry female spy known as the Black Widow (Melinda Clarke); Morgan gives Capt. Awesome advice for a romantic night with Ellie.',  
        # `category`,       'Comedy',   
        # `profile`,        'Default',  
        # `recpriority`,    0,  
        # `autoexpire`,     1,  
        # `maxepisodes`,    0,  
        # `maxnewest`,      1,  
        # `startoffset`,    0,  
        # `endoffset`,      0,  
        # `recgroup`,       'Default',  
        # `dupmethod`,      6,  
        # `dupin`,          15,  
        # `station`,        'NBC5-DT',  
        # `seriesid`,       'EP00930779',  
        # `programid`,      'EP009307790016',  
        # `search`,         0,  
        # `autotranscode`,  0,  
        # `autocommflag`,   1,  
        # `autouserjob1`,   0,  
        # `autouserjob2`,   0,  
        # `autouserjob3`,   0,  
        # `autouserjob4`,   0,  
        # `findday`,        2,  
        # `findtime`,       '19:00:00',  
        # `findid`,         733687,  
        # `inactive`,       0,  
        # `parentid`,       0,  
        #
        # New ======
        # `transcoder`,     0,  
        # `tsdefault`,      1,  
        # `playgroup`,      'Default',  
        # `prefinput`,      0,  
        # `next_record`,    '0000-00-00 00:00:00',  
        # `last_record`,    '2008-12-15 19:00:03',  
        # `last_delete`,    '2008-10-06 23:29:08',  
        # `storagegroup`,   'Default', 
        # `avg_delay`)      76)
        
# =============================================================================
class CustomMySQLConverter(MySQLdb.conversion.MySQLConverter):

    def __init__(self, charset=None, use_unicode=True):
        MySQLdb.conversion.MySQLConverter.__init__(self, charset, use_unicode)

    def _DATE_to_python(self, v, dsc=None):
        """
        Override default impl to gracefully handle invalid dates (ex: '0000-00-00')
        and just pass None back instead.
        
        Someone's db had a program.originalairdate = 0000-00-00 which the
        mysql-connector pure python impl choked on.
        """
        pv = None
        try:
            pv = datetime.date(*[ int(s) for s in v.split('-')])
        except ValueError: # , ve:
            pass #raise ValueError, "Could not convert %s to python datetime.date with error %s" % (v, ve)
        return pv
    
