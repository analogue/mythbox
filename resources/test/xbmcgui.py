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
import logging

from mockito import *

log = logging.getLogger('mythbox.unittest')

ICON_OVERLAY_HAS_TRAINER = 4
ICON_OVERLAY_HD = 8
ICON_OVERLAY_LOCKED = 3
ICON_OVERLAY_NONE = 0
ICON_OVERLAY_RAR = 1
ICON_OVERLAY_TRAINED = 5
ICON_OVERLAY_UNWATCHED = 6
ICON_OVERLAY_WATCHED = 7
ICON_OVERLAY_ZIP = 2

__author__ = 'J. Mulder <darkie@xbmc.org>'
__credits__ = 'XBMC TEAM.'
__date__ = '14 July 2006'
__platform__ = 'XBOX'
__version__ = '1.2'

def lock():
    log.debug('xbmcgui.lock() called')

def unlock():
    log.debug('xbmcgui.unlock() called')

def getCurrentWindowId():
    log.debug('xbmcgui.getCurrentWindowId() called')

def getCurrentWindowDialogId():
    """Returns the id for the current 'active' dialog as an integer."""
    log.debug('xbmcgui.getCurrentWindowDialogId() called')


class Action(object):
    """
    Action class.
    For backwards compatibility reasons the == operator is extended so that itcan compare an action with other actions and action.id with numbers  example: (action == ACTION_MOVE_LEFT)
    """
    
    def getAmount1(self):
        """Returns the first amount of force applied to the thumbstick n."""
        pass
    
    def getAmount2(self):
        """Returns the second amount of force applied to the thumbstick n."""
        pass
    
    def getButtonCode(self):
        """Returns the button code for this action."""
        pass
    
    def getId(self):
        """Returns the action's current id as a long or 0 if no action is mapped in the xml's."""
        pass
    

class DialogProgress(object):
    """
    Mock progress bar
    """

    def create(self, msg):
        self.canceled = False
        log.debug('DialogProgress::create(' + msg + ')')

    def update(self, percent, msg1, msg2, msg3) : 
        log.debug('DialogProgress::update(' + str(percent) + ', ' + msg1 + ', ' + msg2 + ', ' + msg3 + ')')

    def iscanceled(self):
        log.debug('DialogProgress::iscanceled() : ' + str(self.canceled))
        return self.canceled

    def close(self):
        log.debug('DialogProgress::close()')
        self.canceled = True


class Window(object):

    def getWidth(self):
        return 1920

    def getHeight(self):
        return 1080

    def addControl(self, control):
        log.debug('calling window.addControl(%s)' % control)
        
    def getControl(self, controlId):
        log.debug('calling getControl(%s)' % controlId)
        return Mock()

    def setFocus(self, control):
        log.debug('calling Window.setFocus(%s)' % control)
        
    def getFocus(self):
        log.debug('calling Window.getFocus()')
        
    def doModal(self):
        log.debug('calling Window.doModal()')
        
    def close(self):
        log.debug('calling Window.close()')
        
    def removeControl(self, control):
        log.debug('calling Window.removeControl(%s)' % control)
        
    def show(self):
        log.debug('calling Window.show()')   
        
    def setProperty(self, key, value):
        log.debug('calling setProperty(...)')
        
    def getFocusId(self):
        """
        getFocusId(self, int) -- returns the id of the control which is focused.\n
        Throws: SystemError, on Internal error
                RuntimeError, if no control has focus
        """
        log.debug('calling getFocusId(...)')


class WindowDialog(Window):
    
    def onAction(self, action):
        """
        This method will recieve all actions that the main program will send
        to this window.
        By default, only the PREVIOUS_MENU action is handled.
        Overwrite this method to let your script handle all actions.
        Don't forget to capture Action.PREVIOUS_MENU, else the user can't close this window.
        """
        pass    
    
    def doModal(self):
        log.debug('calling WindowDialog.doModal()')


class WindowXML(Window):
    
    def __init__(self, *args, **kwargs):
        """
        WindowXML(self, xmlFilename, scriptPath[, defaultSkin, defaultRes]) -- Create a new WindowXML script.

        xmlFilename     : string - the name of the xml file to look for.
        scriptPath      : string - path to script. used to fallback to if the xml doesn't exist in the current skin. (eg os.getcwd())
        defaultSkin     : [opt] string - name of the folder in the skins path to look in for the xml. (default='Default')
        defaultRes      : [opt] string - default skins resolution. (default='720p')

        *Note, skin folder structure is eg(resources/skins/Default/720p)

        example:
           ui = GUI('script-Lyrics-main.xml', os.getcwd(), 'LCARS', 'PAL')
           ui.doModal()
           del ui;
        """
        pass
    
    def addItem(self, item, position):
        """
        Add a new item to this Window List.
         
        item            : string, unicode or ListItem - item to add.
        position        : [opt] integer - position of item to add. (NO Int = Adds to bottom,0 adds to top, 1 adds to one below from top,-1 adds to one above from bottom etc etc )

        - If integer positions are greater than list size, negative positions will add to top of list, positive positions will add to bottom of list
       
        example:
          - addItem('Reboot XBMC', 0)
        """
        pass
    
    def clearList(self):
        """Clear the Window List."""
        pass
    
    def getCurrentListPosition(self):
        """Gets the current position in the Window List."""
        pass

    def getListItem(self, position):
        """
        Returns a given ListItem in this Window List.
         
        position        : integer - position of item to return.
         
        example:
          - listitem = getListItem(6)
        """
        pass
    
    def getListSize(self):
        """Returns the number of items in this Window List."""
        pass
    
    def removeItem(self, position): 
        """
        Removes a specified item based on position, from the Window List.
         
        position        : integer - position of item to remove.
         
        example:
          - removeItem(5)
        """
        pass
    
    def setCurrentListPosition(self, position):
        """
        Set the current position in the Window List.
         
        position        : integer - position of item to set.
         
        example:
          - setCurrentListPosition(5)
        """
        pass
    
    def setProperty(self, key, value): 
        """
        Sets a container property, similar to an infolabel.
         
        key            : string - property name.
        value          : string or unicode - value of property.
         
        *Note, Key is NOT case sensitive.
               You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
         
        example:
          - setProperty('Category', 'Newest')
        """
        pass
    

class WindowXMLDialog(WindowXML):
    pass


class Dialog(object):

    def browse(self, type, heading, shares, mask, useThumbs, treatAsFolder, default):
        """
        Show a 'Browse' dialog.
         
        type           : integer - the type of browse dialog.
        heading        : string or unicode - dialog heading.
        shares         : string or unicode - from sources.xml. (i.e. 'myprograms')
        mask           : [opt] string or unicode - '|' separated file mask. (i.e. '.jpg|.png')
        useThumbs      : [opt] boolean - if True autoswitch to Thumb view if files exist.
        treatAsFolder  : [opt] boolean - if True playlists and archives act as folders.
        default        : [opt] string - default path or file.
         
        Types:
          0 : ShowAndGetDirectory
          1 : ShowAndGetFile
          2 : ShowAndGetImage
          3 : ShowAndGetWriteableDirectory
         
        *Note, Returns filename and/or path as a string to the location of the highlighted item,
               if user pressed 'Ok' or a masked item was selected.
               Returns the default value if dialog was canceled.
         
        example:
          - dialog = xbmcgui.Dialog()
          - fn = dialog.browse(3, 'XBMC', 'files', '', False, False, 'special://masterprofile/script_data/XBMC Lyrics')
        """
        pass

    def ok(self, heading, line1, line2=None, line3=None):
        """
        Show a dialog 'OK'.
        heading        : string or unicode - dialog heading.
        line1          : string or unicode - line #1 text.
        line2          : [opt] string or unicode - line #2 text.
        line3          : [opt] string or unicode - line #3 text.
     
        *Note, Returns True if 'Ok' was pressed, else False.
     
        example:
          - dialog = xbmcgui.Dialog()
          - ok = dialog.ok('XBMC', 'There was an error.')
        """
        log.debug('ok')
        
    def select(self, heading, list):
        """
        select(heading, list) -- Show a select dialog.
        
        heading        : string or unicode - dialog heading.
        list           : string list - list of items.
        autoclose      : [opt] integer - milliseconds to autoclose dialog. (default=do not autoclose)
        
        *Note, Returns the position of the highlighted item as an integer.
        
        example:
          - dialog = xbmcgui.Dialog()
          - ret = dialog.select('Choose a playlist', ['Playlist #1', 'Playlist #2, 'Playlist #3'])\n");
        """
        log.debug('select' + str(heading) + str(list))
        
    def yesno(self, heading, line1, line2, line3, nolabel, yeslabel):
        """
        yesno(heading, line1[, line2, line3]) -- Show a dialog 'YES/NO'.
        
        heading        : string or unicode - dialog heading.
        line1          : string or unicode - line #1 text.
        line2          : [opt] string or unicode - line #2 text.
        line3          : [opt] string or unicode - line #3 text.
        nolabel        : [opt] label to put on the no button.
        yeslabel       : [opt] label to put on the yes button.
        
        *Note, Returns True if 'Yes' was pressed, else False.
        
        example:
          - dialog = xbmcgui.Dialog()
          - ret = dialog.yesno('XBMC', 'Do you want to exit this script?')
        """
        log.debug('yesno')
        
    def numeric(self, type, heading, default=None):
        """
        numeric(type, heading[, default]) -- Show a 'Numeric' dialog.
         
        type           : integer - the type of numeric dialog.
        heading        : string or unicode - dialog heading.
        default        : [opt] string - default value.
         
        Types:
          0 : ShowAndGetNumber    (default format: #)
          1 : ShowAndGetDate      (default format: DD/MM/YYYY)
          2 : ShowAndGetTime      (default format: HH:MM)
          3 : ShowAndGetIPAddress (default format: #.#.#.#)
        """
        log.debug('numeric')
                

class Control(object):
    
    def __init__(self, type, top, left, width, height):
        log.debug('creating Control...')

    def getId(self):
        """
        @return: the control's current id as an integer.
        """
        pass
    
    def setEnabled(self, enabled):
        """
        Set's the control's enabled/disabled state.
        @param enabled: bool - True=enabled / False=disabled.
        @example: self.button.setEnabled(False)
        """
        pass

    def setVisible(self, visible):
        """
        Set's the control's visible/hidden state.
        @param visible: bool - True=visible / False=hidden.
        @example: self.button.setVisible(False)
        """
        pass          
          
    def controlUp(self, control):
        log.debug('caling Control::controlUp()')

    def controlDown(self, control): 
        log.debug('calling Control::controlDown()')

    def controlLeft(self, control):
        log.debug('calling Control::controlLeft()')

    def controlRight(self, control):
        log.debug('calling Control::controlRight()')


class ControlLabel(Control):

    def __init__(self, top, left, width, height, text, fontStyle = None, fontColor = None,
                 disabledColor = None, alignment = None, hasPath = None):
        log.debug('creating ControlLabel...')

    def getLabel(self):
        """
        Returns the text value for this label.
         
        example:
          - label = self.label.getLabel()
        """
        pass
    
    def setLabel(self, label):
        """
        Set's text for this label.
         
        label          : string or unicode - text string.
         
        example:
          - self.label.setLabel('Status')
        """
        pass
      

class ControlFadeLabel(Control):

    def __init__(self,top, left, width, height, fontStyle, fontColor, alignment):
        log.debug('creating ControlFadeLabel...')

    def addLabel(self, label):
        """
        Add a label to this control for scrolling.
         
        label          : string or unicode - text string.
         
        example:
          - self.fadelabel.addLabel('This is a line of text that can scroll.')
        """
        pass
    
    def reset(self):
        """Clears this fadelabel."""
        pass
      

class ControlButton(Control):

    def __init__(self,
                 x, y, width, height,
                 label = "",
                 focusTexture = '0xFFFFFFFF', noFocusTexture = '0xFFFFFFFF',
                 textXOffset = 0, textYOffset = 0, alignment = 0, font = 'font13',
                 textColor='0xFFFFFFFF', disabledColor='0x60ffffff'):
        log.debug('creating ControlButton...')

 
    def getLabel(self):
        """Returns the buttons label as a unicode string."""
        pass
    
    def getLabel2(self):
        """Returns the buttons label2 as a unicode string."""
        pass
         
    def setDisabledColor(self, disabledColor):
        """
        Set's this buttons disabled color.
         
        disabledColor  : hexstring - color of disabled button's label. (e.g. '0xFFFF3300')
         
        example:
          - self.button.setDisabledColor('0xFFFF3300')
        """
        pass
    
    def setLabel(self, label, font, textColor, disabledColor, shadowColor, focusedColor):
        """
        Set's this buttons text attributes.
         
        label          : [opt] string or unicode - text string.
        font           : [opt] string - font used for label text. (e.g. 'font13')
        textColor      : [opt] hexstring - color of enabled button's label. (e.g. '0xFFFFFFFF')
        disabledColor  : [opt] hexstring - color of disabled button's label. (e.g. '0xFFFF3300')
        shadowColor    : [opt] hexstring - color of button's label's shadow. (e.g. '0xFF000000')
        focusedColor   : [opt] hexstring - color of focused button's label. (e.g. '0xFFFFFF00')
        label2         : [opt] string or unicode - text string.
         
        *Note, You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
         
        example:
          - self.button.setLabel('Status', 'font14', '0xFFFFFFFF', '0xFFFF3300', '0xFF000000')
        """
        pass
      

class ControlList(Control):

    def __init__(self, top, left, width, height, font = "", itemTextXOffset=1, space=1, itemHeight=20):
        log.debug('creating ControlList...')

    def getSelectedItem(self):
        """
        @return: the selected item as a ListItem object or None if the list is empty
        @example: item = cList.getSelectedItem()        
        """
        pass

    def getSelectedPosition(self):
        """
        @return: the position of the selected item as an integer or -1 for an empty list
        @example: pos = cList.getSelectedPosition()
        """
        pass
    
    def getListItem(self, index):
        """
        @return: Returns ListItem at given index
        @param index: integer - index number of item to return.
        @raise ValueError: if index is out of range.
        @example: listitem = cList.getListItem(6)
        """
        pass
    
    def addItem(self, item):
        """
        Add a new item to this list control.
        @param item: string, unicode or ListItem to add.
        @example: cList.addItem('Reboot XBMC')
        """
        pass
    
    def addItems(self, items):
        """
        Adds a list of listitems or strings to this list control.
        @keyword items: List - list of strings, unicode objects or ListItems to add.
        @note: Large lists benefit considerably, than using the standard addItem()
        @example: cList.addItems(items=listitems)
        """
        pass        

    def reset(self):
        """
        Clear all ListItems in this control list.
        """
        pass
    
    def selectItem(self, item):
        """
        Select an item by index number.
        @param item: integer - index number of the item to select.
        @example:cList.selectItem(12)
        """
        pass
    
    def size(self):
        """
        @return: total number of items in this list control as an integer.
        """
        pass
    
    def getItemHeight(self):
        """
        Returns the control's current item height as an integer.
         
        example:
          - item_height = self.cList.getItemHeight()
        """        
        pass
    
    def getSpace(self):
        """
        Returns the control's space between items as an integer.
         
        example:
          - gap = self.cList.getSpace()
        """
        pass    
    
    def getSpinControl(self):
        """
        returns the associated ControlSpin object.
         
        *Note, Not working completely yet -
               After adding this control list to a window it is not possible to change
               the settings of this spin control.
         
        example:
          - ctl = cList.getSpinControl()
        """
        pass
    
    def setImageDimensions(self, imageWidth, imageHeight):
        """
        Sets the width/height of items icon or thumbnail.
         
        imageWidth         : [opt] integer - width of items icon or thumbnail.
        imageHeight        : [opt] integer - height of items icon or thumbnail.
         
        example:
          - cList.setImageDimensions(18, 18)
        """
        pass
    
    def setItemHeight(self, itemHeight):
        """
        Sets the height of items.
         
        itemHeight         : integer - height of items.
         
        example:
          - cList.setItemHeight(25)
        """
        pass    
              
    def setPageControlVisible(self, visible):
        """
        Sets the spin control's visible/hidden state.
         
        visible            : boolean - True=visible / False=hidden.
         
        example:
          - cList.setPageControlVisible(True)
        """
        pass  
    
    def setSpace(self, space):
        """
        Set's the space between items.
         
        space              : [opt] integer - space between items.
         
        example:
          - cList.setSpace(5)
        """
        pass
                        
    def setStaticContent(self, items):
        """
        Fills a static list with a list of listitems.
         
        items                : List - list of listitems to add.
         
        *Note, You can use the above as keywords for arguments.
         
        example:
          - cList.setStaticContent(items=listitems)
        """
        pass
                              

class ControlImage(Control):

    def __init__(self, x, y, width, height, filename, aspectRatio, colorDiffuse):
        """
        x              : integer - x coordinate of control.
        y              : integer - y coordinate of control.
        width          : integer - width of control.
        height         : integer - height of control.
        filename       : string - image filename.
        colorKey       : [opt] hexString - (example, '0xFFFF3300')
        aspectRatio    : [opt] integer - (values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)
        colorDiffuse   : hexString - (example, '0xC0FF0000' (red tint))
        
        example:\n"
          - self.image = xbmcgui.ControlImage(100, 250, 125, 75, aspectRatio=2)\n");
        """
        pass
    
    def setColorDiffuse(self, colorDiffuse):
        """
        Changes the images color.
         
        colorDiffuse   : hexString - (example, '0xC0FF0000' (red tint))
         
        example:
          - self.image.setColorDiffuse('0xC0FF0000')
        """
        pass
    
    def setImage(self, filename, colorKey):
        """
        Changes the image.
         
        filename       : string - image filename.
         
        example:
          - self.image.setImage('special://home/scripts/test.png')
        """
        pass
      

class ControlTextBox(Control):
    
    def __init__(self, x, y, w, h, fnt, tcol):
        pass
    
    def reset(self):
        """Clear's this textbox."""
        pass
    
    def scroll(self, position):
        """
        Scrolls to the given position.
        
        id           : integer - position to scroll to.
        """
        pass

    def setText(self, text):
        """
        Set's the text for this textbox.
     
        text           : string or unicode - text string.
        """
        pass
          

class ControlCheckMark(Control):
    
    def __init__(self, x, y, w, h, l, checkWidth, checkHeight, alignment, textColor):
        pass

    def getSelected(self):
        """Returns the selected status for this checkmark as a bool."""
        pass
    
    def setDisabledColor(self, disabledColor):
        """
        Set's this controls disabled color.
         
        disabledColor  : hexstring - color of disabled checkmark's label. (e.g. '0xFFFF3300')
         
        example:
          - self.checkmark.setDisabledColor('0xFFFF3300')
        """
        pass
    
    def setLabel(self, label, font, textColor, disabledColor):
        """
        Set's this controls text attributes.
         
        label          : string or unicode - text string.
        font           : [opt] string - font used for label text. (e.g. 'font13')
        textColor      : [opt] hexstring - color of enabled checkmark's label. (e.g. '0xFFFFFFFF')
        disabledColor  : [opt] hexstring - color of disabled checkmark's label. (e.g. '0xFFFF3300')
         
        example:
          - self.checkmark.setLabel('Status', 'font14', '0xFFFFFFFF', '0xFFFF3300')
        """
        pass
    
    def setSelected(self, isOn):
        """
        Sets this checkmark status to on or off.
         
        isOn           : bool - True=selected (on) / False=not selected (off)
         
        example:
          - self.checkmark.setSelected(True)
        """
        pass
    

class ControlRadioButton(Control):
    
    def __init__(self, x, y, w, h, tx):
        pass
    
    def isSelected(self):
        """Returns the radio buttons's selected status."""
        pass
    
    def setLabel(self, label, font, textColor, disabledColor, shadowColor, focusedColor):
        """
        Set's the radio buttons text attributes.
         
        label          : string or unicode - text string.
        font           : [opt] string - font used for label text. (e.g. 'font13')
        textColor      : [opt] hexstring - color of enabled radio button's label. (e.g. '0xFFFFFFFF')
        disabledColor  : [opt] hexstring - color of disabled radio button's label. (e.g. '0xFFFF3300')
        shadowColor    : [opt] hexstring - color of radio button's label's shadow. (e.g. '0xFF000000')
        focusedColor   : [opt] hexstring - color of focused radio button's label. (e.g. '0xFFFFFF00')
         
        *Note, You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
         
        example:
          - self.radiobutton.setLabel('Status', 'font14', '0xFFFFFFFF', '0xFFFF3300', '0xFF000000')
        """
        pass
    
    def setRadioDimension(self, x, y, width, height):
        """
        Sets the radio buttons's radio texture's position and size.
         
        x                   : integer - x coordinate of radio texture.
        y                   : integer - y coordinate of radio texture.
        width               : integer - width of radio texture.
        height              : integer - height of radio texture.
         
        *Note, You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
         
        example:
          - self.radiobutton.setRadioDimension(x=100, y=5, width=20, height=20)
        """
        pass
    
    def setSelected(self, selected):
        """ 
        Sets the radio buttons's selected status.
         
        selected            : bool - True=selected (on) / False=not selected (off)
         
        *Note, You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
         
        example:
          - self.radiobutton.setSelected(True)
        """
        pass


class ControlGroup(Control):
    
    def __init(self, x, y, width, height):
        pass


class ControlProgress(Control):

    def __init__(self, x, y, width, height, texturebg, textureleft, texturemid, textureright, textureoverlay):
        """
        x              : integer - x coordinate of control.
        y              : integer - y coordinate of control.
        width          : integer - width of control.
        height         : integer - height of control.
        texturebg      : [opt] string - image filename.
        textureleft    : [opt] string - image filename.
        texturemid     : [opt] string - image filename.
        textureright   : [opt] string - image filename.
        textureoverlay : [opt] string - image filename.
         
        *Note, You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
               After you create the control, you need to add it to the window with addControl().
         
        example:
          - self.progress = xbmcgui.ControlProgress(100, 250, 125, 75)
        """
        pass

    def getPercent(self):
        """
        Returns a float of the percent of the progress.
         
        example:
          - print self.progress.getValue()
        """
        pass
    
    def setPercent(self, percent):
        """
        Sets the percentage of the progressbar to show.
         
        percent       : float - percentage of the bar to show.
         
        *Note, valid range for percent is 0-100
         
        example:
          - self.progress.setPercent(60)
        """
        pass
      

class ListItem(object):
 
    def __init__(self, label = "", label2 = "", iconImage = None, thumbnailImage = None):
        """
        Creates a new ListItem.
        label          : [opt] string or unicode - label1 text.
        label2         : [opt] string or unicode - label2 text.
        iconImage      : [opt] string - icon filename.
        thumbnailImage : [opt] string - thumbnail filename.
 
        example:
        - listitem = xbmcgui.ListItem('Casino Royale', '[PG-13]', 'blank-poster.tbn', 'poster.tbn')
        """
        pass

    def addContextMenuItem(self, labelAndActionTuples):
        """
        addContextMenuItem([(label, action,)*]) -- Adds item(s) to the context menu for media lists.
     
        [(label, action,)*] : list - A list of tuples consisting of label and action pairs.
          - label           : string or unicode - item's label.
          - action          : string - any built-in function to perform.
     
        List of functions - http://xbmc.org/wiki/?title=List_of_Built_In_Functions 
     
        example:
          - listitem.addContextMenuItem([('Theater Showtimes', 'XBMC.RunScript(q:\\scripts\\showtimes\\default.py,Iron Man)',)])
        """
        pass

    def getLabel(self):
        """
        getLabel() -- Returns the listitem label.
     
        example:
        - label = self.list.getSelectedItem().getLabel()
        """
        pass 
    
    def getLabel2(self):
        """
        getLabel2() -- Returns the listitem's second label.
     
        example:
            - label2 = self.list.getSelectedItem().getLabel2()
        """
        pass 

    def getProperty(self, key):
        """
        getProperty(key) -- Returns a listitem property as a string, similar to an infolabel.
        key            : string - property name.
     
        *Note, Key is NOT case sensitive.
               You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
     
        example:
            - AspectRatio = self.list.getSelectedItem().getProperty('AspectRatio')
        """
        pass 
    
    def isSelected(self):
        """
        isSelected() -- Returns the listitem's selected status.
     
        example:
            - is = self.list.getSelectedItem().isSelected()
        """
        pass

    def select(self, isSelected):
        """
        select(selected) -- Sets the listitem's selected status.
        selected        : bool - True=selected/False=not selected
        example:
        - self.list.getSelectedItem().select(True)
        """
        pass

    def setIconImage(self, icon):
        """
        setIconImage(icon) -- Sets the listitem's icon image.
        icon            : string - image filename.
        example:
        - self.list.getSelectedItem().setIconImage('emailread.png')
        """
        pass

    def setInfo(self, type, infoLabels):
        """
        Sets the listitem's infoLabels.
         
        type           : string - type of media(video/music/pictures).
        infoLabels     : dictionary - pairs of { label: value }.
         
        *Note, To set pictures exif info, prepend 'exif:' to the label. Exif values must be passed
               as strings, separate value pairs with a comma. (eg. {'exif:resolution': '720,480'}
               See CPictureInfoTag::TranslateString in PictureInfoTag.cpp for valid strings.
         
               You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
         
        General Values that apply to all types:
            count       : integer (12) - can be used to store an id for later, or for sorting purposes
            size        : long (1024) - size in bytes
            date        : string (%d.%m.%Y / 01.01.2009) - file date
         
        Video Values:
            genre       : string (Comedy)
            year        : integer (2009)
            episode     : integer (4)
            season      : integer (1)
            top250      : integer (192)
            tracknumber : integer (3)
            rating      : float (6.4) - range is 0..10
            watched     : depreciated - use playcount instead
            playcount   : integer (2) - number of times this item has been played
            overlay     : integer (2) - range is 0..8.  See GUIListItem.h for values
            cast        : list (Michal C. Hall)
            castandrole : list (Michael C. Hall|Dexter)
            director    : string (Dagur Kari)
            mpaa        : string (PG-13)
            plot        : string (Long Description)
            plotoutline : string (Short Description)
            title       : string (Big Fan)
            duration    : string (3:18)
            studio      : string (Warner Bros.)
            tagline     : string (An awesome movie) - short description of movie
            writer      : string (Robert D. Siegel)
            tvshowtitle : string (Heroes)
            premiered   : string (2005-03-04)
            status      : string (Continuing) - status of a TVshow
            code        : string (tt0110293) - IMDb code
            aired       : string (2008-12-07)
            credits     : string (Andy Kaufman) - writing credits
            lastplayed  : string (%Y-%m-%d %h:%m:%s = 2009-04-05 23:16:04)
            album       : string (The Joshua Tree)
            votes       : string (12345 votes)
            trailer     : string (/home/user/trailer.avi)
         
        Music Values:
            tracknumber : integer (8)
            duration    : integer (245) - duration in seconds
            year        : integer (1998)
            genre       : string (Rock)
            album       : string (Pulse)
            artist      : string (Muse)
            title       : string (American Pie)
            rating      : string (3) - single character between 0 and 5
            lyrics      : string (On a dark desert highway...)
         
        Picture Values:
            title       : string (In the last summer-1)
            picturepath : string (/home/username/pictures/img001.jpg)
            exif*       : string (See CPictureInfoTag::TranslateString in PictureInfoTag.cpp for valid strings)
         
        example:
          - self.list.getSelectedItem().setInfo('video', { 'Genre': 'Comedy' })
        """          
        pass

    def setLabel(self, label):
        """
        setLabel(label) -- Sets the listitem's label.
         
        label          : string or unicode - text string.
         
        example:
          - self.list.getSelectedItem().setLabel('Casino Royale')
        """
        pass

    def setLabel2(self, label2):
        """
        setLabel2(label2) -- Sets the listitem's second label.
     
        label2         : string or unicode - text string.
         
        example:
            - self.list.getSelectedItem().setLabel2('[pg-13]')
        """
        pass

    def setProperty(self, key, value):
        """
        setProperty(key, value) -- Sets a listitem property, similar to an infolabel.
     
        key            : string - property name.
        value          : string or unicode - value of property.
         
        *Note, Key is NOT case sensitive.
               You can use the above as keywords for arguments and skip certain optional arguments.
               Once you use a keyword, all following arguments require the keyword.
         
        example:
          - self.list.getSelectedItem().setProperty('AspectRatio', '1.85 : 1')
        """
        pass

    def setThumbnailImage(self, thumb):
        """
        setThumbnailImage(thumb) -- Sets the listitem's thumbnail image.
         
        thumb           : string - image filename.
         
        example:
          - self.list.getSelectedItem().setThumbnailImage('emailread.png')
        """
        pass
