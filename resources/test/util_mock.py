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

import codecs
import logging
import mockito
import os
import string
import unittest
import mythboxtest.test_util
import xbmc

from xml.dom import minidom, Node

log = logging.getLogger('mythbox.unittest')


class Translator(object):
    """
    Real XBMC uses xbmc.Language but the unit tests don't have access to this
    so this is a mock impl that will read strings.xml
    """
    def __init__(self, platform, langInfo):
        """
        platform - subclass of Platform for this box
        langinfo - instance of XBMCLangInfo
        """
        self.platform = platform
        self.langInfo = langInfo
        self.strings = {}
        self.loadStrings()

    def loadStrings(self):
        # Determine codec for GUI so that loaded messages can be encoded for
        # GUI immediately
        language = self.langInfo.getSetting('language.charsets.gui')
        #log.debug("language = %s"%language)
        (e,d,r,w) = codecs.lookup(language)

        # Build language string file name. If the file does not exist, default
        # to 'english'.
        languageDir = os.path.join(os.getcwd(), 'resources', 'language')

        lang = string.lower(xbmc.getLanguage())
        langFile = os.path.join(languageDir, lang, 'strings.xml')
        if not os.path.exists(langFile) and lang != "English":
            langFile = os.path.join(languageDir, "English", "strings.xml")
        #log.debug("langFile = %s"%langFile)

        # parse the string file
        dom = minidom.parse(langFile)
        
        #log.debug(dom.toxml())

        # load up localized string hash from file
        for n in dom.getElementsByTagName("string"):
            strId = None
            strValue = None

            strId = int(n.getAttribute("id"))
            try:
                strValue = n.childNodes[0].nodeValue 
            except IndexError, ie:
                pass  # handle <string id="nn" />
            
            # only add it if an id has been specified
            if strId >= 0:
                #(val,num) = e(strValue)
                val = str(strValue)
                self.strings[strId] = val
                #log.debug("adding translation %s = %s" % (strId, val))

        # free up dom tree
        dom.unlink()
        del dom

    def get(self, id):
        # if id is a string, assume no need to lookup translation
        if type(id) is str:
            return id
        else:
            retStr = None
            try:
                retStr = self.strings[id]
            except:
                retStr = "<Undefined>"
                pass
            log.debug("translated %d => %s" % (id, retStr))
            return retStr


class XBMCSettings(object):

    def __init__(self, filePath = None):
        #log.debug("XBMCSettings constructed - filePath = %s"%str(filePath))
        self.domTree = None
        self.tagsSeen = {}
        self.loadSettings(filePath)

    def loadSettings(self, filePath):
        #log.debug("loadSettings(%s)" % filePath)
        #
        # TODO: Remove OS specific stuff
        #
        if not filePath:
            if os.name != "nt":
                filePath = os.path.join('.', 'test', 'settings.xml')
            else:
                filePath = os.path.join('E:', 'TDATA', '0face008', 'settings.xml')

        self.domTree = minidom.parse(filePath)

    def getSetting(self, tag):
        value = None
        if not tag in self.tagsSeen:
            path = tag.split('.')
            dom = self.domTree
            while len(path) > 0:
                search = path[0]
                path.remove(search)
                #log.debug("search = %s"%search )
                dom = dom.getElementsByTagName(search)[0]
            if dom:
                value = ""
                for n in dom.childNodes:
                    value += n.nodeValue
                #log.debug("value = %s"%value )
                self.tagsSeen[tag] = value
        else:
            value = self.tagsSeen[tag]
        #log.debug("returned (tag = %s, value = %s)"%(tag, value))
        return value


class XBMCLangInfo(XBMCSettings):
    
    def __init__(self, platform):
        #log.debug("XBMCLangInfo created %s"%id(self))
        self.platform = platform
        filePath = os.path.join('resources', 'test', 'test_util', 'xbmc', 'language', xbmc.getLanguage(), 'langinfo.xml')
        XBMCSettings.__init__(self, filePath)


class TranslatorTest(unittest.TestCase):

    def setUp(self):
        self.platform = mockito.Mock()
        self.langInfo = XBMCLangInfo(self.platform)
        
    def test_getString_Success(self):
        translator = Translator(self.platform, self.langInfo)
        s = translator.get(0)
        log.debug('translated string(0) = ' + s)
        self.assertEquals('Myth TV', s)

    def test_getString_ReturnsUndefined(self):
        localizedStrings = Translator(self.platform, self.langInfo)
        s = localizedStrings.get(999)
        log.debug('translated string(999) = ' + s)
        self.assertEquals('<Undefined>', s)
        

class XBMCLangInfoTest(unittest.TestCase):

    def test_getSetting_Success(self):
        langInfo = XBMCLangInfo(mythboxtest.test_util.MockPlatform())
        s = langInfo.getSetting('language.charsets.gui')
        log.debug('language.charsets.gui = ' + s)
        self.assertEquals('CP1252', s)

    def test_getSetting_NotDefinedThrowsIndexError(self):
        try:
            langInfo = XBMCLangInfo(mythboxtest.test_util.MockPlatform())
            s = langInfo.getSetting('undefined.setting')
        except IndexError:
            pass
            