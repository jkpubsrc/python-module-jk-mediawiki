

import os
import signal
import subprocess
import typing

import jk_utils
import jk_sysinfo
import jk_logging
import jk_typing

from .impl.AbstractProcessFilter import AbstractProcessFilter
from .impl.WikiNGINXProcessFilter import WikiNGINXProcessFilter
from .impl.WikiPHPProcessFilter import WikiPHPProcessFilter
from .MWManagementCtx import MWManagementCtx







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
	# @param	MWManagementCtx ctx			A management context that provides common data.
	# @param	str startNGINXScript		The absolute file path of a script that starts an user space NGINX in the background.
	#										If not specified no shutdown and restart can be performed.
	# @param	str startPHPFPMScript		The absolute file path of a script that starts an user space PHP process in the background.
	#										If not specified no shutdown and restart can be performed.
	# @param	str localEtcDirPath			The path of the local 'etc' directory used by the NGINX and PHP process
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self,
		ctx:MWManagementCtx,
		startNGINXScript:str,
		startPHPFPMScript:str,
		localEtcDirPath:str,
		bVerbose:bool = False,
		):

		self.__ctx = ctx

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

		self.__phpProcessProvider = WikiPHPProcessFilter(
			userName=self.__ctx.currentUserName,
			source=self.__ctx.osProcessProvider
		)
		self.__nginxProcessProvider = WikiNGINXProcessFilter(
			userName=self.__ctx.currentUserName,
			source=self.__ctx.osProcessProvider
		)
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

	def isPHPFPMRunning(self, debugLog:jk_logging.AbstractLogger = None) -> bool:
		provider = self.getPHPFPMMasterProcessesProvider(debugLog)
		if provider is None:
			return False
		return bool(provider())
	#

	def isNGINXRunning(self, debugLog:jk_logging.AbstractLogger = None) -> bool:
		provider = self.getNGINXMasterProcessesProvider(debugLog)() is not None
		if provider is None:
			return False
		return bool(provider())
	#

	#
	# This method stops PHP-FPM processes if they are running.s
	# On error an exception is raised.
	#
	# NOTE: Debug information is written to the log if verbose output is enabled.
	#
	def stopPHPFPM(self, log:jk_logging.AbstractLogger):
		provider = self.getPHPFPMMasterProcessesProvider(log if self.__bVerbose else None)
		processes = provider()
		if processes:
			log.info("Now stopping PHP-FPM processes: " + str([ x["pid"] for x in processes ]))
			provider.invalidate()
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
		provider = self.getNGINXMasterProcessesProvider(log if self.__bVerbose else None)
		processes = provider()
		if processes:
			log.info("Now stopping NGINX processes: " + str([ x["pid"] for x in processes ]))
			provider.invalidate()
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
		provider = self.getPHPFPMMasterProcessesProvider(log if self.__bVerbose else None)
		processes = provider()
		if processes:
			raise Exception("PHP-FPM process already running!")
		provider.invalidate()
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__ctx.currentUserName,
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
		provider = self.getNGINXMasterProcessesProvider(log if self.__bVerbose else None)
		processes = provider()
		if processes:
			raise Exception("NGINX process already running!")
		provider.invalidate()
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__ctx.currentUserName,
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
	@jk_typing.checkFunctionSignature()
	def getPHPFPMMasterProcessesProvider(self, debugLog:jk_logging.AbstractLogger = None) -> typing.Union[AbstractProcessFilter,None]:
		if self.__startPHPFPMScriptDirPath is None:
			return None

		return self.__phpProcessProvider
	#

	#
	# Returns the master process(es) of "nginx". This should be only one process.
	#
	@jk_typing.checkFunctionSignature()
	def getNGINXMasterProcessesProvider(self, debugLog:jk_logging.AbstractLogger = None) -> typing.Union[AbstractProcessFilter,None]:
		if self.__startNGINXScriptDirPath is None:
			return None

		return self.__nginxProcessProvider
	#

	@jk_typing.checkFunctionSignature()
	def getPHPFPMMasterProcesses(self, debugLog:jk_logging.AbstractLogger = None) -> typing.Union[typing.List[dict],None]:
		pidsProvider = self.getPHPFPMMasterProcessesProvider(debugLog)
		return pidsProvider() if pidsProvider else None
	#

	@jk_typing.checkFunctionSignature()
	def getNGINXMasterProcesses(self, debugLog:jk_logging.AbstractLogger = None) -> typing.Union[typing.List[dict],None]:
		pidsProvider = self.getNGINXMasterProcessesProvider(debugLog)
		return pidsProvider() if pidsProvider else None
	#

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

#




