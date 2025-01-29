import os, sys
from loguru import logger
import logging


class InterceptHandler(logging.Handler):
	def emit(self, record: logging.LogRecord):
		try:
			level = logger.level(record.levelname).name
		except ValueError:
			level = str(record.levelno)

		frame, depth = logging.currentframe().f_back.f_back.f_back, 5
		while not frame.f_code.co_filename.endswith(record.filename):
			frame = frame.f_back
			depth += 1

		logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class _Logger():
	logger = None
	logLevel = None
    
	def __init__(self, logLevel):
		self.logLevel = logLevel
		logger.remove()
		log_format = "<green>{time:D MMM YYYY hh:mm:ss A!UTC}</green> | <level>{level: <8}</level> | <yellow>Line {line: >4} ({name}):</yellow> {message}"
		logger.add(sys.stdout, level=logLevel, format=log_format, colorize=True, backtrace=True, diagnose=False)
		self.logger = logger
  
  
	def initialize(self):
		logging.root.handlers = [InterceptHandler()]
		logging.root.setLevel(logLevel)

		# remove every other logger's handlers
		# and propagate to root logger
		# noinspection PyUnresolvedReferences
		for name in logging.root.manager.loggerDict.keys():
			logging.getLogger(name).handlers = []
			logging.getLogger(name).propagate = True


	def get(self):
		return self.logger


logLevel = "INFO"
debug = os.environ.get('DEBUG')
if debug != None and (debug.lower() == 'true' or debug == '1'):
    logLevel = "DEBUG"
    
_logObj = _Logger(logLevel)
def Logger(): return _logObj.get()
def LoggerInit(): return _logObj.initialize()
