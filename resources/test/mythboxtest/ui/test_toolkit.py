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
import unittest
import xbmc

from mockito import Mock, when, verify, any, verifyZeroInteractions
from mythbox.ui.toolkit import enterText

log = logging.getLogger('mythbox.unittest')

# =============================================================================
class ModuleTest(unittest.TestCase):
    
    def test_enterText_Should_UpdateModelAndControl_When_UserInputIsValid(self):
        # Setup
        xbmc.Keyboard.stubConfirmed = True
        xbmc.Keyboard.stubText = "Bubba"
        
        control = Mock()
        when(control).getLabel().thenReturn('Name')
        validator = Mock()
        updater = Mock()
        
        # Test
        enterText(control=control, validator=validator.validate, updater=updater.update)
        
        # Verify
        verify(validator, 1).validate('Bubba')
        # TODO: type(xbmc.ControlButton) fails for Mock
        #verify(control, 1).setLabel(any(str), any(str)) 
        verify(updater, 1).update('Bubba')

    def test_enterText_Should_DoNothing_When_UserCancelsOperation(self):
        # Setup
        xbmc.Keyboard.stubConfirmed = False
        control = Mock()
        validator = Mock()
        updater = Mock()
        
        # Test
        enterText(control=control, validator=validator.validate, updater=updater.update)
        
        # Verify
        verifyZeroInteractions(validator)
        verifyZeroInteractions(updater)

    def test_enterText_Should_NotUpdateControlAndModel_When_UserEnteredTextFailsValidation(self):
        # Setup
        xbmc.Keyboard.stubConfirmed = True
        xbmc.Keyboard.stubText = 'Bubba'
        control = Mock()
        updater = Mock()
        validator = Mock()
        when(validator).validate(any()).thenRaise(Exception('Invalid name'))        
        
        # Test
        enterText(control=control, validator=validator.validate, updater=updater.update)
        
        # Verify
        verifyZeroInteractions(updater)
        verify(control, 0).setLabel(any(str), any(str))
        # TODO: type(xbmc.ControlButton) fails for Mock
        #verify(control, 1).getLabel()  
        
    def test_try_loading_gui_screens(self):
        log.debug('Trying to import gui screens....')
        import mythbox.bootstrapper
        import mythbox.ui.home
        import mythbox.ui.uisettings
        import mythbox.ui.schedules
        import mythbox.ui.livetv
        import mythbox.ui.recordings
        import mythbox.ui.recordingdetails
        import mythbox.ui.tvguide
        import mythbox.ui.upcoming
        log.debug('Trying to import gui screens done')
        
# =============================================================================
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
