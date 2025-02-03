import configparser
import os


class _Prefs:
	config = None
	configFilePath = None

	def __init__(self, path):
		self.config = configparser.RawConfigParser() 
		self.configFilePath = path
		if (os.path.isfile(self.configFilePath)):
			self.config.read(self.configFilePath)

			
	def commitPref(self):
		with open(self.configFilePath, 'w') as configfile:
			self.config.write(configfile)
	
	
	def updatePref(self, section, pref, value):
		self.config.set(section, pref, value)
		
	
	def getSections(self):
		try:
			return self.config.sections()
		except Exception as error:
			return ""		
	
	def getKeys(self, section):
		try:
			return self.config[section]
		except Exception as error:
			return ""
	

	def getPref(self, pref, section='default'):
		try:
			return self.config.get(section, pref)
		except Exception as error:
			return ""
	
	
	def getBoolPref(self, pref, section='default'):
		try:
			return self.config.getboolean(section, pref)
		except Exception as error:
			return ""
		
		
	def getIntPref(self, pref, section='default'):
		try:
			return self.config.getint(section, pref)
		except Exception as error:
			return ""
	

	def getFloatPref(self, pref, section='default'):
		try:
			return self.config.getfloat(section, pref)
		except Exception as error:
			return ""

			
prefsPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.cfg")
_prefsObj = _Prefs(prefsPath)
def Prefs(): return _prefsObj