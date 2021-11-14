

import os
import signal
import subprocess
import typing

import jk_pathpatternmatcher2
import jk_utils
import jk_sysinfo
import jk_json
import jk_mediawiki
import jk_logging
from jk_typing import *






#
# This class helps dealing with local MediaWiki installations running using a local user account.
# This is the preferred way for local MediaWiki installations. But please have in mind that this follows certain conventions:
#
# * NGINX is used (and must be configured to serve the wiki pages).
# * There is a `bin`-directory that holds start scripts for PHP-FPM and NGINX. Each script must use `nohub` to run the processes.
#
class MediaWikiLocalUserServiceMgr(object):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Configuration parameters:
	#
	# @param	str startNGINXScript		The absolute file path of a script that starts an user space NGINX in the background.
	#										If not specified no shutdown and restart can be performed.
	# @param	str startPHPFPMScript		The absolute file path of a script that starts an user space PHP process in the background.
	#										If not specified no shutdown and restart can be performed.
	# @param	str localEtcDirPath			The path of the local 'etc' directory used by the NGINX and PHP process
	# @param	str userName				The name of the user account under which NGINX, PHP and the Wiki cron process are executed.
	#
	@checkFunctionSignature()
	def __init__(self,
		startNGINXScript:str,
		startPHPFPMScript:str,
		localEtcDirPath:str,
		userName:str,
		bVerbose:bool = False,
		):

		# store and process the account name the system processes are running under

		assert isinstance(userName, str)
		assert userName

		self.__userName = userName

		# other scripts

		if startNGINXScript is not None:
			assert isinstance(startNGINXScript, str)
			assert os.path.isfile(startNGINXScript)

		if startPHPFPMScript is not None:
			assert isinstance(startPHPFPMScript, str)
			assert os.path.isfile(startPHPFPMScript)

		assert isinstance(localEtcDirPath, str)
		assert os.path.isdir(localEtcDirPath)

		self.__startNGINXScriptFilePath = startNGINXScript
		self.__startNGINXScriptDirPath = os.path.dirname(startNGINXScript) if startNGINXScript else None
		self.__startPHPFPMScriptFilePath = startPHPFPMScript
		self.__startPHPFPMScriptDirPath = os.path.dirname(startPHPFPMScript) if startPHPFPMScript else None
		self.__localEtcDirPath = localEtcDirPath
		self.__bVerbose = bVerbose
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def localEtcDirPath(self) -> str:
		return self.__localEtcDirPath
	#

	@property
	def startNGINXScriptFilePath(self) -> str:
		return self.__startNGINXScriptFilePath
	#

	@property
	def startNGINXScriptDirPath(self) -> str:
		return self.__startNGINXScriptDirPath
	#

	@property
	def startPHPFPMScriptFilePath(self) -> str:
		return self.__startPHPFPMScriptFilePath
	#

	@property
	def startPHPFPMScriptDirPath(self) -> str:
		return self.__startPHPFPMScriptDirPath
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def isPHPFPMRunning(self, debugLog:jk_logging.AbstractLogger = None):
		return self.getPHPFPMMasterProcesses(debugLog) is not None
	#

	def isNGINXRunning(self, debugLog:jk_logging.AbstractLogger = None):
		return self.getNGINXMasterProcesses(debugLog) is not None
	#

	#
	# This method stops PHP-FPM processes if they are running.s
	# On error an exception is raised.
	#
	# NOTE: Debug information is written to the log if verbose output is enabled.
	#
	def stopPHPFPM(self, log:jk_logging.AbstractLogger):
		processes = self.getPHPFPMMasterProcesses(log if self.__bVerbose else None)
		if processes:
			log.info("Now stopping PHP-FPM processes: " + str([ x["pid"] for x in processes ]))
			if not jk_utils.processes.killProcesses(processes, log):
				raise Exception("There were errors stopping PHP-FPM!")
		else:
			log.notice("No PHP-FPM processes active.")
	#

	#
	# This method stops NGINX processes if they are running.s
	# On error an exception is raised.
	#
	# NOTE: Debug information is written to the log if verbose output is enabled.
	#
	def stopNGINX(self, log:jk_logging.AbstractLogger):
		processes = self.getNGINXMasterProcesses(log if self.__bVerbose else None)
		if processes:
			log.info("Now stopping NGINX processes: " + str([ x["pid"] for x in processes ]))
			if not jk_utils.processes.killProcesses(processes, log):
				raise Exception("There were errors stopping NGINX!")
		else:
			log.notice("No NGINX processes active.")
	#

	#
	# This method starts the PHP-FPM process.
	# On error an exception is raised.
	#
	# NOTE: Debug information is written to the log if verbose output is enabled.
	#
	def startPHPFPM(self, log:jk_logging.AbstractLogger):
		if self.getPHPFPMMasterProcesses(log if self.__bVerbose else None) is not None:
			raise Exception("PHP-FPM process already running!")
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__userName,
				filePath=self.__startPHPFPMScriptFilePath,
				args=None,
				log=log if self.__bVerbose else None
			):
			raise Exception("Starting PHP-FPM process failed!")
		log.info("PHP-FPM started.")
	#

	#
	# This method starts the NGINX process.
	# On error an exception is raised.
	#
	# NOTE: Debug information is written to the log if verbose output is enabled.
	#
	def startNGINX(self, log:jk_logging.AbstractLogger):
		if self.getNGINXMasterProcesses(log if self.__bVerbose else None) is not None:
			raise Exception("NGINX process already running!")
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__userName,
				filePath=self.__startNGINXScriptFilePath,
				args=None,
				log=log if self.__bVerbose else None
			):
			raise Exception("Starting NGINX process failed!")
		log.info("NGINX started.")
	#

	#
	# Returns the master process(es) of "php-fpm". This should be only one process.
	#
	def getPHPFPMMasterProcesses(self, debugLog:jk_logging.AbstractLogger = None) -> typing.Union[list, None]:
		if self.__startPHPFPMScriptDirPath is None:
			return None

		processList = jk_sysinfo.get_ps()

		if debugLog and self.__bVerbose:
			debugLog = debugLog.descend("Scanning for processes ...")
		else:
			# NOTE: if no debugging is enabled, no debug logger will be used.
			debugLog = None

		ret = []
		for x in processList:
			if x["user"] != self.__userName:
				if debugLog:
					debugLog.debug("Rejecting because not owned by user '{}': {}".format(self.__userName, x))
				continue
			if x["cmd"].find("php-fpm") < 0:
				if debugLog:
					debugLog.debug("Rejecting because command does not contain 'php-fpm': {}".format(x))
				continue
			if not x["args"].startswith("master process"):
				if debugLog:
					debugLog.debug("Rejecting because 'args' does not start with 'master process': {}".format(self.__startPHPFPMScriptDirPath, x))
				continue
			if x["args"].find("(" + self.__localEtcDirPath) < 0:
				if debugLog:
					debugLog.debug("Rejecting because does not seem to refer to the local configuration directory: {}".format(x))
				continue
			if debugLog:
				debugLog.debug("Accepting: {}".format(x))
			ret.append(x)

		return ret if ret else None
	#

	#
	# Returns the master process(es) of "nginx". This should be only one process.
	#
	def getNGINXMasterProcesses(self, debugLog:jk_logging.AbstractLogger = None) -> typing.Union[list, None]:
		if self.__startNGINXScriptDirPath is None:
			return None

		processList = jk_sysinfo.get_ps()

		if debugLog and self.__bVerbose:
			debugLog = debugLog.descend("Scanning for processes ...")
		else:
			# NOTE: if no debugging is enabled, no debug logger will be used.
			debugLog = None

		ret = []
		for x in processList:
			if x["user"] != self.__userName:
				if debugLog:
					debugLog.debug("Rejecting because not owned by user '{}': {}".format(self.__userName, x))
				continue
			if not x["cmd"].startswith("nginx"):
				if debugLog:
					debugLog.debug("Rejecting because command does not start with 'nginx': {}".format(x))
				continue
			if not x["args"].startswith("master process"):
				if debugLog:
					debugLog.debug("Rejecting because 'args' does not start with 'master process': {}".format(self.__startPHPFPMScriptDirPath, x))
				continue
			if x["args"].find("-c " + self.__localEtcDirPath) < 0:
				if debugLog:
					debugLog.debug("Rejecting because does not seem to refer to the local configuration directory: {}".format(x))
				continue
			if debugLog:
				debugLog.debug("Accepting: {}".format(x))
			ret.append(x)

		return ret if ret else None
	#

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

#




