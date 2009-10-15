#
#    xbmcskin.py - v0.1 - Bitplane
#    loads xbmc skins, in a crude kind of way.
#    read skinningreadme.txt for details
#    
#    Modifications for Myth TV python scripts for XBMC by Tom Warkentin & analogue@yahoo.com
#    
#    NOTE: I repeat that this has been modified from Bitplane's original to include
#          some bug fixes, extra functionality, and debug logging.

import logging
import os
import string
import traceback
import ui
import util
import xbmcgui

from xml.dom import minidom
from util import timed

    
log = logging.getLogger('mythtv.skin')

class XBMC_SKIN_CONTROL:
    
    def __init__(self, owner, translator):
        self.options = {}
        self.control = None
        self.owner = owner
        self.translator = translator

    def create(self):
        """
        internal:
        creates the control and adds it to the page
        assumes width/height etc are already set
        does not do navigation
        """

        # get generic stuff, position, type, etc
        id = string.lower(self.getoption("id"))
        t = string.lower(self.getoption("type"))
        
        x = int(self.getvalue(self.getoption("posx")))
        y = int(self.getvalue(self.getoption("posy")))
        c=None

        # 0 means auto (afaik)
        w = 0  
        h = 0  
        t1 = self.getoption("width")
        if t1 != "":
            w = int(self.getvalue(t1))
        t1 = self.getoption("height")
        if t1 != "":
            h = int(self.getvalue(t1))
        l = self.getoption("label")
        try:
            t1 = int(l)
            l = self.translator.get(t1)
        except:
            pass
        
        help = self.getoption("help")
        try:
            t1 = int(help)
            help = self.translator.get(t1)
        except:
            pass
        self.options['help'] = help
        
        tx = self.getoption("texture")
        if tx != "":
            tx = util.findMediaFile( tx )
            # if it didn't find the script skin file then use the xbmc skin file
            if tx == None:
                tx = self.getoption("texture")
                
        tx1 = self.getoption("texturefocus")
        if tx1 != "":
            tx1 = util.findMediaFile( tx1 )
        tx2 = self.getoption("texturenofocus")
        if tx2 != "":
            tx2 = util.findMediaFile( tx2 )
            
        ck = self.getoption("colorkey")
        aspectRatio = self.getoption("aspectratio")
        fnt = self.getvalue(self.getoption("font"))
        tcol = self.getoption("textcolor")

        log.debug( "id=[%s] x=[%d] y=[%d] w=[%d] h=[%d] font=[%s]"%(id,x,y,w,h,fnt) )
        c = None
        if t == "image":
            try:
                if ck == "" and aspectRatio == "":
                    c = xbmcgui.ControlImage(x,y,w,h,tx)
                elif aspectRatio != "":
                    c = xbmcgui.ControlImage(x,y,w,h,tx, aspectRatio=int(aspectRatio))
                else: 
                    c = xbmcgui.ControlImage(x,y,w,h,tx,ck)
            except Exception:
                log.exception("Unable to load image id:%s filename:%s" %(id, tx))

        elif t == "button":
            try:
                tox = int(self.getvalue(self.getoption("offsetx")))
            except:
                tox = 17
            try:
                toy = int(self.getvalue(self.getoption("offsety")))
            except:
                toy = 2
            try:
                align = int(self.getvalue(self.getoption("alignment")))
            except:
                align = 0   # left
            log.debug("font=[%s] tox=[%d] toy=[%d] align=[%d]" % (fnt, tox, toy, align))

            if tx1 == "":
                if fnt == "":
                    c = xbmcgui.ControlButton(
                        x,y,w,h,l,
                        textXOffset=int(tox),textYOffset=int(toy),
                        alignment=align)
                else:
                    c = xbmcgui.ControlButton(
                        x,y,w,h,l,font=str(fnt),
                        textXOffset=int(tox),textYOffset=int(toy),
                        alignment=align)
            elif tx2 == "":
                if fnt == "":
                    c = xbmcgui.ControlButton(
                        x,y,w,h,l,tx1,
                        textXOffset=int(tox),textYOffset=int(toy),
                        alignment=align)
                else:
                    c = xbmcgui.ControlButton(
                        x,y,w,h,l,tx1,font=fnt,
                        textXOffset=int(tox),textYOffset=int(toy),
                        alignment=align)
            else:
                if fnt == "":
                    c = xbmcgui.ControlButton(
                        x, y, w, h, l, tx1, tx2,
                        textXOffset=int(tox), textYOffset=int(toy),
                        alignment=align)
                else:
                    c = xbmcgui.ControlButton(
                        x, y, w, h, l, tx1, tx2, font=fnt,
                        #textXOffset=int(tox), 
                        #textYOffset=int(toy),
                        alignment=align)
        elif t == "fadelabel":
            try:
                align = int(self.getvalue(self.getoption("alignment")))
            except Exception:
##                traceback.print_exc()
##                print ( "XBMCMYTHTV: %s " % str(ex) )
                align = 6   # left
            c = xbmcgui.ControlFadeLabel(x, y, w, h, str(fnt), tcol, alignment=align)
        
        elif t == "label":
            try:
                align = int(self.getvalue(self.getoption("alignment")))
            except:
                align = 0   # left
            c = xbmcgui.ControlLabel(x, y, w, h, l, str(fnt), tcol, alignment=align)

        elif t == "listcontrol":
            try:
                tox = int(self.getvalue(self.getoption("offsetx")))
            except:
                tox = 17
            try:
                spc = int(self.getvalue(self.getoption("space")))
            except:
                spc = 1
            try:
                ih = int(self.getvalue(self.getoption("itemheight")))
            except:
                ih = 20

            #    ALIGN_LEFT                          = 0
            #    ALIGN_RIGHT                         = 1
            #    ALIGN_CENTER_X                      = 2
            #    ALIGN_CENTER_Y                      = 4
            #    ALIGN_TRUNCATED                     = 8

            bt = util.findMediaFile('button-focus.png')
            aly = ui.ALIGN_TRUNCATED | ui.ALIGN_CENTER_Y
            
            log.debug( "font=[%s] tox=[%d] ih=[%d]"%(fnt,tox,ih) )

            if tx1 == "":
                if fnt == "":
                    c = xbmcgui.ControlList(x, y, w, h, itemTextXOffset=int(tox), space=int(spc), itemHeight=int(ih), alignmentY=aly, buttonFocusTexture=bt)
                else:
                    c = xbmcgui.ControlList(x, y, w, h, font=fnt, itemTextXOffset=int(tox), space=int(spc), itemHeight=int(ih), alignmentY=aly, buttonFocusTexture=bt)
                log.debug("xbmcgui.ControlList(x,y,w,h)")
            elif tx2 == "":
                if fnt == "":
                    c = xbmcgui.ControlList(x, y, w, h, tx1, itemTextXOffset=int(tox), space=int(spc), itemHeight=int(ih), alignmentY=aly, buttonFocusTexture=bt)
                else:
                    c = xbmcgui.ControlList(x, y, w, h, tx1, font=fnt, itemTextXOffset=int(tox), space=int(spc), itemHeight=int(ih), alignmentY=aly, buttonFocusTexture=bt)
                log.debug("xbmcgui.ControlList(x,y,w,h,tx1)")
            else:
                if fnt == "":
                    c = xbmcgui.ControlList(x, y, w, h, tx1, tx2, itemTextXOffset=int(tox), space=int(spc), itemHeight=int(ih), alignmentY=aly, buttonFocusTexture=bt)
                else:
                    c = xbmcgui.ControlList(x, y, w, h, tx1, tx2, font=fnt, itemTextXOffset=int(tox), space=int(spc), itemHeight=int(ih), alignmentY=aly, buttonFocusTexture=bt)
                log.debug("xbmcgui.ControlList(x,y,w,h,tx1,tx2)")
        elif t == "textbox":
            c = xbmcgui.ControlTextBox(x, y, w, h, fnt, tcol)
            # c.setText()
        elif t == "checkmark":
            try:
                cw = int(self.getoption("checkwidth"))
            except:
                cw = 30
            try:
                ch = int(self.getoption("checkheight"))
            except:
                ch = 30
            try:
                align = int(self.getvalue(self.getoption("alignment")))
            except:
                align = 1   # right
            if tx1 == "":
                c = xbmcgui.ControlCheckMark(x, y, w, h, l, checkWidth=cw, checkHeight=ch, alignment=align, textColor=tcol)
            elif tx2 == "":
                c = xbmcgui.ControlCheckMark(x, y, w, h, l, tx1, checkWidth=cw, checkHeight=ch, alignment=align, textColor=tcol)
            else:
                c = xbmcgui.ControlCheckMark(x, y, w, h, l, tx1, tx2, cw, ch, align, textColor=tcol)
        log.debug("created '%s' control"%t)

        # TODO: Remove OS specific checks
        if c != None:
            if os.name != "nt":
                self.owner.addControl(c)
            else:
                # lists are acting funny. trying remove instead of hide
                t1 = self.owner.getoption("defaultgroup")
                if t1 == self.getoption("group") or self.getoption("group") == "":
                    self.owner.addControl(c)
        self.control = c

    def getoption(self,stroption):
        """
        gets a setting from the controls options
        without raising an error if it doesnt exist (returns "")
        """
        x = ""
        try:
            x = self.options[stroption]
        except:
            pass
        if x == "-":
            x = ""
        return x

    def getvalue(self,strval):
        """
            internal: gets a value from an equation for x,y,width,height
        """
        #log.debug( "strval=[%s]"%strval )
        r = str(strval)
        for x in self.owner.options:
            r = string.replace(r,"(" + str(x) + ")",str(self.owner.options[x]))
        try:
            return eval(r)
        except:
            return r
    

class XBMC_SKIN(xbmcgui.Window):
    
    def __init__(self, *args, **kwargs):
        xbmcgui.Window.__init__(self, *args, **kwargs)
        
    @timed    
    def loadskin(self, skinName):
        """
        loads the given skin file and creates all the controls
        then makes the default group ("") visible
        
        controls are listed in the XBMC_SKIN.controls dictionary
        window settings are listed in the XBMC_SKIN.options
        """
        log.debug("loadskin(%s)" + skinName)
        # load the skin XML
        skinXml = util.loadSkin(skinName, self.getWidth(), self.getHeight())

        log.debug("skinXml=[%s]" % skinXml)

        # parse the xml
        dom = minidom.parseString(skinXml)

        # get the current path
        self.path = skinXml[0:skinXml.rfind("\\") + 1]

        # set window options
        self.options = {}
        self.options["width"] = self.getWidth()
        self.options["height"] = self.getHeight()
        self.setoptions(dom.getElementsByTagName("window")[0])

        # create the controls
        self.controls = {}
        self.activecontrol = None
        self.addcontrols(dom.getElementsByTagName("control"))
        
        dom.unlink()
        del dom

        # show the default group
        self.group = ""
        self.showgroup(self.getoption("defaultgroup"))

    def getvalue(self,strval):
        """
            internal: gets a value from an equation for x,y,width,height
        """
        r = str(strval)
        for x in self.options:
            r = string.replace(r,"(" + str(x) + ")",str(self.options[x]))
        try:
            return eval(r)
        except:
            log.debug("Possible skin error: problem evaluating '%s'"%r)
            return r

    def setoptions(self, n):
        """
            internal: loads the window options
            from the <window> section in the skin
            n = root window node
        """
        # add window settings
        for m in n.childNodes:
            if m.nodeType == 1:
                if string.lower(str(m.nodeName)) != "controls":
                    self.options[string.lower(str(m.nodeName))] = self.getvalue(m.childNodes[0].nodeValue)
    
    def addcontrols(self, nodes):
        """
            internal: adds the controls in the DOM nodes collection
        """

        # add the controls
        for n in nodes:
            me = XBMC_SKIN_CONTROL(self, self.translator)
            for m in n.childNodes:
                if m.nodeType == 1:
                    if string.lower(str(m.nodeName)) == "id":
                        self.controls[str(m.childNodes[0].nodeValue)] = me
                    me.options[string.lower(str(m.nodeName))] = str(m.childNodes[0].nodeValue)
            me.create()

    def getoption(self,stroption):
        """
            gets an setting from the windows options
            without raising an error if it doesnt exist (returns "")
        """
        x = ""
        try:
            x = self.options[stroption]
        except:
            pass
        if x == "-":
            x = ""
        return x

    def showgroup(self, strgrp, hideother=True):
        """
        shows all controls that have group=strgroup, or group=""
        if strgrp is "", the window's default control is focused
        otherwise, the control with "default" set is focused
        """
        log.debug("showgroup(strgrp='%s')"%strgrp)
        
        if self.group != strgrp:
            self.group = strgrp
            # lock the gui for speed
            xbmcgui.lock()
            isLocked = 1
            
            try:
                # add/hide all the controls
                for id in self.controls:
                    n = self.controls[id]
                    m = n.getoption("group")
                    try:
                        if m == strgrp or m == "":
                            # TODO: Remove OS specific checks
                            if os.name != "nt":
                                n.control.setVisible(True)
                            else:
                                self.addControl(n.control)
                        else:
                            if hideother:
                                # TODO: Remove OS specific checks
                                if os.name != "nt":
                                    n.control.setVisible(False)
                                else:
                                    self.removeControl(n.control)
                    except:
                        pass
                        
                setdef = None
                # sort out the navigation
                for id in self.controls:
                    n = self.controls[id]
                    m = n.getoption("group")
                    if m == strgrp or m == "":
                        # this one is here, set its options
                        x = n.getoption("onup")
                        if x != "":
                            n.control.controlUp(self.controls[x].control)
                        x = n.getoption("ondown")
                        if x != "":
                            n.control.controlDown(self.controls[x].control)
                        x = n.getoption("onleft")
                        if x != "":
                            n.control.controlLeft(self.controls[x].control)
                        x = n.getoption("onright")
                        if x != "":
                            n.control.controlRight(self.controls[x].control)
                        if n.getoption("default") != "":
                            setdef = n
                
                # unlock the gui
                xbmcgui.unlock()
                isLocked = 0

                # set the default control
                if strgrp == "":
                    if self.getoption("defaultcontrol") != "":
                        self.setFocus(self.controls[self.getoption("defaultcontrol")].control)
                else:
                    if setdef != None:
                        self.setFocus(setdef.control)
            except:
                if isLocked > 0:
                    xbmcgui.unlock()
                traceback.print_exc()
                raise

    def hidegroup(self, strgrp):
        """
            hides all controls that have group=strgroup
            if strgrp is "" nothing will happen
        """
        log.debug("hidegroup( strgrp=[%s] )"%strgrp )
        
        # lock the gui for speed
        xbmcgui.lock()
        isLocked = 1
        
        try:
            # add/hide all the controls
            for id in self.controls:
                n = self.controls[id]
                m = n.getoption("group")
                try:
                    if m == strgrp:
                        # TODO: Remove OS specific checks
                        if os.name != "nt":
                            n.control.setVisible(False)
                        else:
                            self.removeControl(n.control)
                except:
                    pass
                    
            # unlock the gui
            xbmcgui.unlock()
            isLocked = 0

        except:
            if isLocked > 0:
                xbmcgui.unlock()
            traceback.print_exc()
            raise

    def getcontrolid(self,control):
        """
            returns the ID of the control from the xml,
            if it is in the skin's list
        """
        for i in self.controls:
            if self.controls[i].control is control:
                return str(i)
        return ""
