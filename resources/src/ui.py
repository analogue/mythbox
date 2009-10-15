#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
#  Copyright (C) 2005 Tom Warkentin <tom@ixionstudios.com>
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
import skin
import string
import traceback
import util
import xbmc
import xbmcgui

from decorator import decorator

log = logging.getLogger('mythtv.ui')
elog = logging.getLogger('mythbox.event')

ACTION_MOVE_LEFT                    = 1
ACTION_MOVE_RIGHT                   = 2
ACTION_MOVE_UP                      = 3
ACTION_MOVE_DOWN                    = 4
ACTION_PAGE_UP                      = 5
ACTION_PAGE_DOWN                    = 6
ACTION_SELECT_ITEM                  = 7
ACTION_HIGHLIGHT_ITEM               = 8
ACTION_PARENT_DIR                   = 9
ACTION_PREVIOUS_MENU                = 10
ACTION_SHOW_INFO                    = 11
ACTION_PAUSE                        = 12
ACTION_STOP                         = 13
ACTION_NEXT_ITEM                    = 14
ACTION_PREV_ITEM                    = 15
ACTION_SCROLL_UP                    = 111
ACTION_SCROLL_DOWN                  = 112
ACTION_CONTEXT_MENU                 = 117

# from xbmc/guilib/common/xbfont.h
ALIGN_LEFT                          = 0
ALIGN_RIGHT                         = 1
ALIGN_CENTER_X                      = 2
ALIGN_CENTER_Y                      = 4
ALIGN_TRUNCATED                     = 8

picBase = os.getcwd() + os.sep + 'images' + os.sep

# channel icons should be placed in images\channel and named after channel id
picType = "_square.png"  # change to reflect you image type

# =============================================================================
def toString(action):
    """
    @type action: xbmcgui.Action
    """ 
    return "Action(id = %s, amount1=%s, amount2=%s, buttonCode=%s" % (
        action.getId(), action.getAmount1(), action.getAmount2(), action.getButtonCode())
         
# =============================================================================
def showPopup(title, text, millis=10000):
    # filter all commas out of text since they delimit args
    title = title.replace(',', ';')
    text = text.replace(',', ';')
    s = 'XBMC.Notification(%s,%s,%s)'  % (title, text, millis)
    log.debug('showPopup: %s' % s)
    xbmc.executebuiltin(s)

# =============================================================================
def enterText(control, validator=None, updater=None, heading=None, current=None):
    """
    Prompt user to enter a text string via xbmc's keyboard control and populate
    the associated text control.
    
    @param control: control to edit
    @param validator: method with a single param to validate text. should raise Exception on invald text
    @param updater: method with a single param to update the text in a domain object
    @param heading: Dialog title as str
    @param current: current value as str
    @return: tuple(ok=bool, value=str)
    """
    ok = False
    txt = None
    
    if heading is None:
        if True: # type(control) == xbmcgui.ControlButton:
            heading = control.getLabel()
        
    if current is None:
        if True: # type(control) == xbmcgui.ControlButton:
            current = control.getLabel2()
            
    log.debug('current=%s heading=%s' % (current, heading))
    
    kbd = xbmc.Keyboard(current, heading)
    kbd.doModal()
    if kbd.isConfirmed():
        txt = kbd.getText()
        
        valid = True
        if validator:
            try:
                log.debug('validating %s' % txt)
                validator(txt)
            except Exception, e:
                valid = False
                errMsg = str(e)  # TODO: Extract proper error message
                log.exception('validator')

        if valid:
            if True: #type(control) == xbmcgui.ControlButton:
                control.setLabel(label=heading, label2=txt)
                ok = True
                if updater: 
                    updater(txt)
        else:
            xbmcgui.Dialog().ok("Error", errMsg)
            
    return ok, txt
            
# =============================================================================
def enterNumeric(control, min=None, max=None, validator=None, updater=None, heading=None, current=None):
    """
    Prompt user to enter a number and update the associated control and/or domain object.
    
    @param heading: Dialog title as string
    @param current: current value as int
    """
    ok = False
    value = None
    
    if heading is None:
        if True: # type(control) == xbmcgui.ControlButton:
            heading = control.getLabel()
        
    if current is None:
        if True: #type(control) == xbmcgui.ControlButton:
            current = control.getLabel2()
    
    value = xbmcgui.Dialog().numeric(0, heading, current)
    result = int(value)
    valid = True
        
    if min is not None and result < min:
        valid = False
        errMsg = 'Value must be between %d and %d' % (min, max)
        
    if max is not None and result > max:
        valid = False
        errMsg = 'Value must be between %d and %d' % (min, max)
    
    if validator:
        try:
            log.debug('validating %s' % result)
            validator(str(result))
        except Exception, e:
            valid = False
            errMsg = str(e)  # TODO: Extract proper error message
            log.exception('validator')

    if valid:
        if True: #type(control) == xbmcgui.ControlButton:
            control.setLabel(label=heading, label2=str(result))
            ok = True
            if updater: 
                updater(result)
    else:
        xbmcgui.Dialog().ok("Error", errMsg)
        
    return ok, value

# =============================================================================
@decorator
def window_busy(func, *args, **kwargs):
    window = args[0]
    try:
        window.setBusy(True)
        result = func(*args, **kwargs)
    finally:
        window.setBusy(False)
    return result

# ==============================================================================
class BaseWindow(xbmcgui.WindowXML):
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXML.__init__(self, *args, **kwargs)
        self.win = None        
        
    def setBusy(self, busy):
        self.win.setProperty('busy', ('false', 'true')[busy])
        
    def isBusy(self):
        busy = self.win.getProperty('busy')
        return busy and busy == 'true'
    
    def setListItemProperty(self, listItem, name, value):
        """Convenience method to make sure None values don't make it to the UI"""
        if listItem and name and not value is None:
            listItem.setProperty(name, value)
        else:
            log.warn('Setting listitem with a None: listItem=%s name=%s value=%s' % (listItem, name, value))

    def setWindowProperty(self, name, value):
        """Convenience method to make sure None values don't make it to the UI"""
        if self.win and name and not value is None:
            self.win.setProperty(name, value)
        else:
            log.warn('Setting window property with a None: win=%s name=%s value=%s' % (self.win, name, value))
            
# =============================================================================        
class LegacyBaseWindow(skin.XBMC_SKIN):

    def __init__(self, *args, **kwargs):
        """
        @keyword conn: Connection
        @keyword db: MythDatabase
        @keyword settings: MythSettings
        @keyword translator: Translator
        @keyword thumbCache: ThumbIconCache
        """
        skin.XBMC_SKIN.__init__(self, *args, **kwargs)
        if 'conn' in kwargs:
            self.conn = kwargs['conn']
        if 'db' in kwargs:
            self.db = kwargs['db']
        if 'platform' in kwargs:
            self.platform = kwargs['platform']
        self.settings = kwargs['settings']
        self.translator = kwargs['translator']
        
        # Thumb cache optional for now...
        try:
            self.thumbCache = kwargs['thumbCache']
        except KeyError:
            self.thumbCache = None
                
        self.actionConsumed = 0
        self.lock = 0
        
    def onAction(self, action):
        elog.debug("LegacyBaseWindow.onAction: %s" % toString(action))

        try:
            # Lock out concurrent events - XBMC fires events in separate
            # threads.  Without the lock, two threads can be modifying window
            # objects at the same time corrupting data structures.
            if self.lock == 0:
                try:
                    self.lock += 1

                    # call subclass defined hook
                    actionConsumed = self.onActionHook(action)

                    # check if action was not consumed
                    if actionConsumed == 0:
                        # process help request - if subclass hook overrides
                        # this behavior then it should have consumed the event
                        if action in (ACTION_SHOW_INFO, ACTION_CONTEXT_MENU):
                            id = self.getcontrolid(self.getFocus())
                            if len(id) > 0:
                                help = self.controls[id].getoption('help')
                            else:
                                help = ""

                            if len(help) > 0:
                                xbmcgui.Dialog().ok(self.translator.get(26), help)
                                actionConsumed = 1

                    # check if event was consumed
                    if actionConsumed == 0:
                        # check if parent dir selected
                        if action == ACTION_PARENT_DIR:
                            self.close()
                        else:
                            skin.XBMC_SKIN.onAction(self, action)

                    self.onActionPostHook(action)

                    self.lock -= 1
                except:
                    self.lock -= 1
                    raise
        except util.ProtocolException, ex:
            log.exception('onAction ProtocolException')
            xbmcgui.Dialog().ok(self.translator.get(27), self.translator.get(109)%str(ex)) 
        except Exception, ex:
            log.exception('onAction')
            xbmcgui.Dialog().ok( self.translator.get(27), str(ex))

    def onActionHook(self, action):
        """
        Method that is called by LegacyBaseWindow class.  This method is intended to
        be overridden by subclasses to perform custom logic.
        
        Return values:

        0   Event was not consumed by the hook.  Event will be handled
            internally. (default)
        1   Event was consumed by hook.  No further processing will be done.

        LegacyBaseWindow catches exceptions and displays dialog.  Therefore this
        type of logic does not need to replicated in this hook.
        """
        return 0
        
    def onActionPostHook( self, action ):
        """
        Method that is called after internal processing is done on an action.
        This is meant to be overridden if additional logic needs to be
        performed after the internal processing is complete.
        """
        pass

    def onControl( self, control ):
        log.debug("onControl( control= %s )"%control )

        try:
            if self.lock == 0:
                try:
                    self.lock += 1
                    rc = self.onControlHook(control)
                    self.lock -= 1
                except:
                    self.lock -= 1
                    raise
        except util.ProtocolException, ex:
            xbmcgui.Dialog().ok(self.translator.get(27), self.translator.get(109) % str(ex))
        except Exception, ex:
            traceback.print_exc(ex)
            xbmcgui.Dialog().ok(self.translator.get(27), str(ex))

    def onControlHook( self, control ):
        """
        Method that is called by LegacyBaseWindow class.  This method is intended to
        be overridden by subclasses to perform custom logic.
        
        Return values:

        0   Event was not consumed by the hook.  Event will be handled
            internally.
        1   Event was consumed by hook.  No further processing will be done.
            (default)

        LegacyBaseWindow catches exceptions and displays dialog.  Therefore this
        type of logic does not need to replicated in this hook.
        """
        return 1
