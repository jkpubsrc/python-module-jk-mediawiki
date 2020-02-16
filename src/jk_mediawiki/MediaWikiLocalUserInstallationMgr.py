

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
import jk_version






#
# This class helps dealing with local MediaWiki installations running using a local user account.
# This is the preferred way for local MediaWiki installations. But please have in mind that this follows certain conventions:
#
# * NGINX is used (and must be configured to serve the wiki pages).
# * There is a `bin`-directory that holds start scripts for PHP-FPM and NGINX. Each script must use `nohub` to run the processes.
# * There is a common root directory for this (and other) Wiki(s). This directory contains files and directories as specified next:
#	* A subdirectory - here named "mywiki" - holds the wiki files and subdirectories. This is *the* Wiki installation.
#	* A subdirectory - here named "mywikidb" - holds the database files. The Wiki must be configured to use this subdirectory accordingly.
#	* A script - here named "mywikicron.sh" - continuously executes the maintenance PHP script.
#	* A script - here named "mywikicron-bg.sh" - is capable of starting this script as background process (using `nohup`).
#
class MediaWikiLocalUserInstallationMgr(object):

	#
	# Configuration parameters:
	#
	# @param	str mediaWikiDirPath		(required) The absolute directory path where the MediaWiki installation can be found.
	#										The final directory name in the path must be the same as the site name of the Wiki.
	#										Additionally there must be a cron script named "<sitename>cron.sh".
	# @param	str userName				(required) The name of the user account under which NGINX, PHP and the Wiki cron process are executed.
	#
	@checkFunctionSignature()
	def __init__(self,
		mediaWikiDirPath:str,
		userName:str,
		):

		# store and process the account name the system processes are running under

		assert isinstance(userName, str)
		assert userName

		self.__userName = userName

		# check MediaWiki installation directory and load settings

		assert isinstance(mediaWikiDirPath, str)
		assert mediaWikiDirPath
		assert os.path.isdir(mediaWikiDirPath)
		assert os.path.isabs(mediaWikiDirPath)

		self.__wikiDirPath = mediaWikiDirPath

		mwLocalSettings = jk_mediawiki.MediaWikiLocalSettingsFile()
		mwLocalSettings.load(dirPath = mediaWikiDirPath)

		wikiSiteName = mwLocalSettings.getVarValueE("wgSitename")
		dbType = mwLocalSettings.getVarValueE("wgDBtype")
		if dbType == "sqlite":
			sqliteDataDir = mwLocalSettings.getVarValueE("wgSQLiteDataDir")
			assert os.path.dirname(sqliteDataDir) == os.path.dirname(mediaWikiDirPath)
			self.__wikiDBDirPath = sqliteDataDir
		else:
			raise NotImplementedError("Backup of database not (yet) supported: " + dbType)

		self.__wikiDirName = os.path.basename(mediaWikiDirPath)
		if self.__wikiDirName.lower() != wikiSiteName.lower():
			raise Exception("Installation directory name does not match the MediaWiki site name! ("
				+ repr(self.__wikiDirName) + " vs. " + repr(wikiSiteName) + ")")

		self.__wikiBaseDirPath = os.path.dirname(mediaWikiDirPath)

		# wiki background task script

		expectedCronScriptFileName = self.__wikiDirName + "cron.sh"
		p = os.path.join(os.path.dirname(self.__wikiDirPath), expectedCronScriptFileName)
		if os.path.isfile(p):
			self.__cronScriptFilePath = p
		else:
			raise Exception("No cron script: " + repr(expectedCronScriptFileName))

		expectedStartCronScriptFileName = self.__wikiDirName + "cron-bg.sh"
		p = os.path.join(os.path.dirname(self.__wikiDirPath), expectedStartCronScriptFileName)
		if os.path.isfile(p):
			self.__startCronScriptFilePath = p
		else:
			raise Exception("No cron script: " + repr(expectedStartCronScriptFileName))

		self.__cronScriptDirPath = os.path.dirname(self.__cronScriptFilePath) if self.__cronScriptFilePath else None
		self.__cronScriptFileName = os.path.basename(self.__cronScriptFilePath) if self.__cronScriptFilePath else None
	#

	@property
	def wikiDirName(self) -> str:
		return self.__wikiDirName
	#

	@property
	def wikiDBDirPath(self) -> str:
		return self.__wikiDBDirPath
	#

	#
	# The installation directory of the media wiki installation
	#
	@property
	def wikiDirPath(self) -> str:
		return self.__wikiDirPath
	#

	#
	# The parent directory of the media wiki installation
	#
	@property
	def wikiBaseDirPath(self) -> str:
		return self.__wikiBaseDirPath
	#

	@property
	def cronScriptFilePath(self) -> str:
		return self.__cronScriptFilePath
	#

	@property
	def startCronScriptFilePath(self) -> str:
		return self.__startCronScriptFilePath
	#

	@property
	def cronScriptFileName(self) -> str:
		return self.__cronScriptFileName
	#

	@property
	def cronScriptDirPath(self) -> str:
		return self.__cronScriptDirPath
	#

	def isCronScriptRunning(self):
		return self.getCronProcesses() is not None
	#

	#
	# Load the MediaWiki file "LocalSettings.php" and return it.
	#
	def loadMediaWikiLocalSettingsFile(self) -> jk_mediawiki.MediaWikiLocalSettingsFile:
		mwLocalSettings = jk_mediawiki.MediaWikiLocalSettingsFile()
		mwLocalSettings.load(dirPath = self.__wikiDirPath)
		return mwLocalSettings
	#

	def stopCronScript(self, log = None):
		processes = self.getCronProcesses()
		if processes:
			log.info("Now stopping cron background processes: " + str([ x["pid"] for x in processes ]))
			if not jk_utils.processes.killProcesses(processes, log):
				raise Exception("There were errors stopping the cron background script!")
		else:
			log.notice("No cron background processes active.")
	#

	def startCronScript(self, log = None):
		if self.getCronProcesses() is not None:
			raise Exception("Cron process already running!")
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__userName,
				filePath=self.__startCronScriptFilePath,
				args=None,
				log=log
			):
			raise Exception("Starting cron process failed!")
	#

	#
	# Returns the master and child processes of the cron script.
	#
	def getCronProcesses(self) -> typing.Union[list, None]:
		if self.__cronScriptDirPath is None:
			return None

		processList = jk_sysinfo.get_ps()

		bashProcess = None
		for x in processList:
			if x["user"] != self.__userName:
				continue
			if not x["cmd"] == "/bin/bash":
				continue
			if "cwd" not in x:
				continue
			if x["cwd"] != self.__cronScriptDirPath:
				continue
			if ("args" not in x) or (x["args"].find(self.__cronScriptFileName) < 0):
				continue
			bashProcess = x

		if bashProcess is None:
			return None

		ret = [ bashProcess ]
		for x in processList:
			if x["ppid"] == bashProcess["pid"]:
				ret.append(x)

		return ret
	#

	def getVersion(self):
		lookingForFilePrefix = "RELEASE-NOTES-"
		for entry in os.scandir(self.__wikiDirPath):
			if entry.is_file() and entry.name.startswith(lookingForFilePrefix):
				return jk_version.Version(entry.name[len(lookingForFilePrefix):])
		raise Exception("Can't determine version!")
	#

#




