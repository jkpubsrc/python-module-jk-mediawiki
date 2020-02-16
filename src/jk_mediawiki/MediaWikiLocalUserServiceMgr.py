

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

	#
	# Configuration parameters:
	#
	# @param	str startNGINXScript		The absolute file path of a script that starts an user space NGINX in the background.
	#										If not specified no shutdown and restart can be performed.
	# @param	str startPHPFPMScript		The absolute file path of a script that starts an user space PHP process in the background.
	#										If not specified no shutdown and restart can be performed.
	# @param	str userName				The name of the user account under which NGINX, PHP and the Wiki cron process are executed.
	#
	@checkFunctionSignature()
	def __init__(self,
		startNGINXScript:str,
		startPHPFPMScript:str,
		userName:str,
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

		self.__startNGINXScriptFilePath = startNGINXScript
		self.__startNGINXScriptDirPath = os.path.dirname(startNGINXScript) if startNGINXScript else None
		self.__startPHPFPMScriptFilePath = startPHPFPMScript
		self.__startPHPFPMScriptDirPath = os.path.dirname(startPHPFPMScript) if startPHPFPMScript else None
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

	def isPHPFPMRunning(self):
		return self.getPHPFPMMasterProcesses() is not None
	#

	def isNGINXRunning(self):
		return self.getNGINXMasterProcesses() is not None
	#

	def stopPHPFPM(self, log = None):
		processes = self.getPHPFPMMasterProcesses()
		if processes:
			log.info("Now stopping PHP-FPM processes: " + str([ x["pid"] for x in processes ]))
			if not jk_utils.processes.killProcesses(processes, log):
				raise Exception("There were errors stopping PHP-FPM!")
		else:
			log.notice("No PHP-FPM processes active.")
	#

	def stopNGINX(self, log = None):
		processes = self.getNGINXMasterProcesses()
		if processes:
			log.info("Now stopping NGINX processes: " + str([ x["pid"] for x in processes ]))
			if not jk_utils.processes.killProcesses(processes, log):
				raise Exception("There were errors stopping NGINX!")
		else:
			log.notice("No NGINX processes active.")
	#

	def startPHPFPM(self, log = None):
		if self.getPHPFPMMasterProcesses() is not None:
			raise Exception("PHP-FPM process already running!")
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__userName,
				filePath=self.__startPHPFPMScriptFilePath,
				args=None,
				log=log
			):
			raise Exception("Starting PHP-FPM process failed!")
	#

	def startNGINX(self, log = None):
		if self.getNGINXMasterProcesses() is not None:
			raise Exception("NGINX process already running!")
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__userName,
				filePath=self.__startNGINXScriptFilePath,
				args=None,
				log=log
			):
			raise Exception("Starting NGINX process failed!")
	#

	#
	# Returns the master process(es) of "php-fpm". This should be only one process.
	#
	def getPHPFPMMasterProcesses(self) -> typing.Union[list, None]:
		if self.__startPHPFPMScriptDirPath is None:
			return None

		processList = jk_sysinfo.get_ps()

		ret = []
		for x in processList:
			if x["user"] != self.__userName:
				continue
			if x["cmd"].find("php-fpm") < 0:
				continue
			if "cwd" not in x:
				continue
			if x["cwd"] != self.__startPHPFPMScriptDirPath:
				continue
			if not x["args"].startswith("master process"):
				continue
			ret.append(x)

		return ret if ret else None
	#

	#
	# Returns the master process(es) of "nginx". This should be only one process.
	#
	def getNGINXMasterProcesses(self) -> typing.Union[list, None]:
		if self.__startNGINXScriptDirPath is None:
			return None

		processList = jk_sysinfo.get_ps()

		ret = []
		for x in processList:
			if x["user"] != self.__userName:
				continue
			if not x["cmd"].startswith("nginx"):
				continue
			if "cwd" not in x:
				continue
			if x["cwd"] != self.__startNGINXScriptDirPath:
				continue
			if not x["args"].startswith("master process"):
				continue
			ret.append(x)

		return ret if ret else None
	#

#




