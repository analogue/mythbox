# -*- coding: utf-8 -*-
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
import unittest2 as unittest
#from mythbox.log import SafeLogger

log = logging.getLogger('mythbox.unittest')

#class SafeLoggerTest(unittest.TestCase):
#    
#    def test_messages_sanitized_before_passing_up_the_chain(self):
#        safe_logger = SafeLogger(log)
#        safe_logger.debug('debug hellow world')
#        safe_logger.info('info hello world')
#        safe_logger.warning('warn hello world')
#        safe_logger.error('error hello world')
#        us = u'madeleine (Grabación Manual)'
#        safe_logger.error(us)
#        u2 = u'Königreich der Himmel'
#        safe_logger.error(u2)
#        # what asserts?

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
