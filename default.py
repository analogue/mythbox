#
#  MythBox for XBMC
#
#  Copyright (C) 2009 analogue@yahoo.com 
#  http://mythbox.googlecode.com
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

__scriptname__ = "MythBox for XBMC"
__author__     = "analogue@yahoo.com"
__url__        = "http://mythbox.googlecode.com"
__svn_url__    = "http://mythbox.googlecode.com/svn/trunk"
__credits__    = "bunch of ppl"
__svn_revision__ = 1505
__version__    = "[Beta SVN %d]" % __svn_revision__

if __name__ == '__main__':
    import os, sys
    sys.path.append(os.path.join(os.getcwd(), 'resources', 'src'))
    from mythbox.bootstrapper import BootStrapper
    BootStrapper().run()

#        @run_async
#        @catchall
#        @inject_conn
#        def refresh(self):
#            tuners = self.conn().getTuners()
#            maxVisibleCards = 3
#            cnt = 0
#            for tuner in tuners:
#                if cnt < maxVisibleCards:
#                    tunerStatus = tuner.formattedTunerStatus()
#                    self.controls['encoder_status' + str(cnt)].control.reset()
#                    self.controls['encoder_status' + str(cnt)].control.addLabel(tunerStatus)
#                    cnt += 1
#
#            space = self.conn().getFreeSpace()
#            self.controls['space_free'].control.setLabel(space[0])
#            self.controls['space_total'].control.setLabel(space[1])
#            self.controls['space_used'].control.setLabel(space[2])
#
#            loads = self.conn().getLoad()
#            self.controls['load_avg_1min'].control.setLabel(str(loads[0]))
#            self.controls['load_avg_5min'].control.setLabel(str(loads[1]))
#            self.controls['load_avg_15min'].control.setLabel(str(loads[2]))
#            
#            self.controls['mythfilldatabase'].control.reset()
#            self.controls['mythfilldatabase'].control.addLabel(self.conn().getMythFillStatus())
#
#            pendingRecordings = [] # TODO: uncomment - self.conn.getPendingRecordings()
#            ctl = self.controls['schedule'].control
#            ctl.reset()
#            try:
#                ctl.setPageControlVisible(False)
#            except:
#                pass
#            
#            now = datetime.now().strftime("%Y%m%d%H%M%S")
#            totRecs = 0
#            for s in pendingRecordings:
#                if s.endtime() >= now:
#                    totRecs += 1 
#                    ctl.addItem( "%s - Encoder %s - %s - %s-%s" % (
#                        time.strftime("%a %d/%m %I:%M%p",time.localtime(float(s.recstarttime()))),
#                        s.cardid(),
#                        s.getChannelName(),
#                        s.title(), 
#                        s.subtitle()))
#            
#            self.controls['schedule_lbl'].control.setLabel('TODO: Put something useful in this box')    
#            #self.controls['schedule_lbl'].control.setLabel(self.translator.get(84) % totRecs)
#            self.controls['guidedata'].control.reset()
#            self.controls['guidedata'].control.addLabel(self.conn().getGuideData())
#