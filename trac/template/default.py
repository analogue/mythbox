import os
import xbmc
import xbmcgui


class MyWindow(xbmcgui.WindowXML):
    
    def __init__(self, *args, **kwargs):
        xbmc.log("MyWindow constructed")

    def onInit(self):
        xbmc.log("onInit called")
    
    def onFocus(self, controlId):
        xbmc.log("onFocus called");
 
    def onAction(self, action):
        xbmc.log("onAction called")
        
    def onClick(self, controlId):
        xbmc.log("onClick called")
        self.close()

                
window = MyWindow("mywindow.xml", os.getcwd(), "Default")

window.doModal()

xbmc.log("script exited")
