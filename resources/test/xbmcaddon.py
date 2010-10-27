
class Addon(object):
    '''
     |  Addon class.
     |  
     |  Addon(id) -- Creates a new Addon class.
     |  
     |  id          : string - id of the addon.
     |  
     |  *Note, You can use the above as a keyword.
     |  
     |  example:
     |   - self.Addon = xbmcaddon.Addon(id='script.recentlyadded')    
    '''
    def __init__(self, id):
        pass
    
    def getAddonInfo(self, id):
        '''
        Returns the value of an addon property as a string
        id        : string - id of the property that the module needs to access
        
        *Note, choices are (author, changelog, description, disclaimer, fanart. icon, id, name, path
                            profile, stars, summary, type, version)
        You can use the above as keywords for arguments.
        
        example:
        version = self.Addon.getAddonInfo('version')

        >>> a.getAddonInfo('path')
        '/home/analogue/.xbmc/addons/script.mythbox'
        >>> a.getAddonInfo('profile')
        'special://profile/addon_data/script.mythbox/'
        >>> a.getAddonInfo('changelog')
        '/home/analogue/.xbmc/addons/script.mythbox/changelog.txt'
        >>> a.getAddonInfo('description')
        'MythBox is a MythTV frontend for XBMC'
        >>> a.getAddonInfo('disclaimer')
        ''
        >>> a.getAddonInfo(id='version')
        '1.0.RC2'
        >>> a.getAddonInfo('id')
        'script.mythbox'
        >>> a.getAddonInfo('name')
        'MythBox'
        >>> a.getAddonInfo('stars')
        0
        >>> a.getAddonInfo('summary')
        'MythBox for XBMC'
        >>> a.getAddonInfo('type')
        'xbmc.python.script'
        '''
        d = {
             'type':'xbmc.python.script',
             'summary': 'script summary',
             'name': 'MythBox',
             'id': 'script.mythbox',
             'profile': 'special://profile/addon_data/script.mythbox/',
             'path':'/tmp/script.mythbox'
        }
        return d.get('id', 'TODO')

    def getLocalizedString(self, id):
        '''
         |      getLocalizedString(id) -- Returns an addon's localized 'unicode string'.
         |      
         |      id             : integer - id# for string you want to localize.
         |      
         |      *Note, You can use the above as keywords for arguments.
         |      
         |      example:
         |        - locstr = self.Addon.getLocalizedString(id=6)
        '''
        return 'TODO'
     
    def getSetting(self, id):
        '''
         |      getSetting(id) -- Returns the value of a setting as a unicode string.
         |      
         |      id        : string - id of the setting that the module needs to access.
         |      
         |      *Note, You can use the above as a keyword.
         |      
         |      example:
         |        - apikey = self.Addon.getSetting('apikey')
        '''
        return ''
    
    def openSettings(self):
        '''
         |      openSettings() -- Opens this scripts settings dialog.
         |      
         |      example:
         |        - self.Settings.openSettings()
        '''
        pass
    
    def setSetting(self, id, value):
        '''
         |      setSetting(id, value) -- Sets a script setting.
         |      
         |      id        : string - id of the setting that the module needs to access.
         |      value     : string or unicode - value of the setting.
         |      
         |      *Note, You can use the above as keywords for arguments.
         |      
         |      example:
         |        - self.Settings.setSetting(id='username', value='teamxbmc')
        '''
        pass 
