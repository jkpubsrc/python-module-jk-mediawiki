

import math
import os
import typing
import datetime

import jk_utils
import jk_sysinfo
import jk_json
import jk_mediawiki
import jk_logging
import jk_typing
import jk_version

from .Utils import Utils
from .MediaWikiSkinInfo import MediaWikiSkinInfo
from .MediaWikiDiskUsageInfo import MediaWikiDiskUsageInfo
from .MediaWikiExtensionInfo import MediaWikiExtensionInfo






#
# This class helps dealing with local MediaWiki installations running using a local user account.
# Instances of this class represent a single MediaWiki installation.
#
# This is the preferred way for managing local MediaWiki installations. But please have in mind that this follows certain conventions:
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

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Variables
	################################################################################################################################

	# @field		str __userName					The name of the user account under which NGINX, PHP and the Wiki cron process are executed.
	# @field		str __wikiDirPath				The absolute directory path where the MediaWiki installation can be found.
	# @field		str __wikiDirName				The name of the directory the Wiki resides in
	# @field		str __wikiDBDirPath				The directory where all the databases are stored
	# @field		str __cronScriptFilePath		The path of the cron script file
	# @field		str __cronScriptDirPath			For convenience: The directory where the cron script file resides in
	# @field		str __cronScriptFileName		For convenience: The name of the cron script file without it's parent directory information

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Configuration parameters:
	#
	# @param	str mediaWikiDirPath		(required) The absolute directory path where the MediaWiki installation can be found.
	#										The final directory name in the path must be the same as the site name of the Wiki.
	#										Additionally there must be a cron script named "<sitename>cron.sh".
	# @param	str userName				(required) The name of the user account under which NGINX, PHP and the Wiki cron process are executed.
	#
	@jk_typing.checkFunctionSignature()
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

		#mwLocalSettings.dump()			# DEBUG

		wikiSiteName = mwLocalSettings.getVarValue("wgSitename")
		if wikiSiteName is None:
			wikiSiteName = mwLocalSettings.getVarValue("siteName")
		if wikiSiteName is None:
			wikiSiteName = mwLocalSettings.getVarValue("wikiSiteName")
		if wikiSiteName is None:
			raise Exception("None of these variables exist: $wikiSiteName, $siteName, $wgSitename")

		dbType = mwLocalSettings.getVarValueE("wgDBtype")
		if dbType == "sqlite":
			sqliteDataDir = mwLocalSettings.getVarValueE("wgSQLiteDataDir")
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

	################################################################################################################################
	## Properties
	################################################################################################################################

	@property
	def wikiLocalSettingsFilePath(self) -> str:
		filePath = os.path.join(self.__wikiDirPath, "LocalSettings.php")
		if os.path.isfile(filePath):
			return filePath
		else:
			# raise Exception("No such file: " + filePath)
			return None
	#

	@property
	def wikiExtensionsDirPath(self) -> str:
		wikiExtensionsDirPath = os.path.join(self.__wikiDirPath, "extensions")
		if os.path.isdir(wikiExtensionsDirPath):
			return wikiExtensionsDirPath
		else:
			#raise Exception("No such directory:" + wikiExtensionsDirPath)
			return None
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
	# The root directory of the media wiki installation. Here resides the LocalSettings.php file.
	#
	@property
	def wikiDirPath(self) -> str:
		return self.__wikiDirPath
	#

	#
	# The parent directory of the media wiki installation.
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

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	#
	# This method scans the MediaWiki skin directory and returns a sorted list of skins.
	#
	# @param			jk_logging.AbstractLogger log			(optional) A logger for debug output. If you run into problems loading and analyzing
	#															a skin (yes, that can happens as skins might have errors) specify a debug logger
	#															here as all analyzing is done during runtime of this method.
	#															If you don't specify a logger, any kind of errors are silently ignored.
	#
	# @return			MediaWikiSkinInfo[]						Returns skin information objects.
	#
	def getSkinInfos(self, log:jk_logging.AbstractLogger = None) -> typing.List[MediaWikiSkinInfo]:
		ret = []

		for fe in os.scandir(os.path.join(self.__wikiDirPath, "skins")):
			if fe.is_dir():

				if log:
					with log.descend("Analyzing skin: " + fe.name) as log2:
						try:
							skin = MediaWikiSkinInfo.loadFromDir(fe.path)
						except Exception as ee:
							log.error("Failed to load: " + fe.name)
							continue
				else:
					try:
						skin = MediaWikiSkinInfo.loadFromDir(fe.path)
					except Exception as ee:
						print("WARNING: Failed to load: " + fe.name)
						continue

				ret.append(skin)

		ret.sort(key=lambda x: x.name)

		return ret
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

	def getVersion(self) -> jk_version.Version:
		lookingForFilePrefix = "RELEASE-NOTES-"
		for entry in os.scandir(self.__wikiDirPath):
			if entry.is_file() and entry.name.startswith(lookingForFilePrefix):
				return jk_version.Version(entry.name[len(lookingForFilePrefix):])
		raise Exception("Can't determine version!")
	#

	def getSMWVersion(self) -> typing.Union[jk_version.Version,None]:
		p = os.path.join(self.__wikiDirPath, "extensions", "SemanticMediaWiki", "extension.json")
		if os.path.isfile(p):
			j = jk_json.loadFromFile(p)
			return jk_version.Version(j["version"])
		return None
	#

	def getLastConfigurationTimeStamp(self) -> typing.Union[datetime.datetime,None]:
		t = -1

		dirPath = self.wikiExtensionsDirPath
		if dirPath:
			for feExt in os.scandir(dirPath):
				if feExt.is_dir():
					try:
						mtime = feExt.stat(follow_symlinks=False).st_mtime
						if mtime > t:
							t = mtime
					except:
						pass
					for fe in os.scandir(feExt.path):
						if fe.is_file():
							try:
								mtime = fe.stat(follow_symlinks=False).st_mtime
								if mtime > t:
									t = mtime
							except:
								pass

		filePath = self.wikiLocalSettingsFilePath
		if filePath:
			try:
				mtime = os.stat(filePath).st_mtime
				if mtime > t:
					t = mtime
			except:
				pass

		if t <= 0:
			return None
		else:
			return datetime.datetime.fromtimestamp(mtime)
	#

	def getLastUseTimeStamp(self) -> typing.Union[datetime.datetime,None]:
		t = -1

		dirPaths = [ self.__wikiDirPath ]
		if self.__wikiDBDirPath:
			dirPaths.append(self.__wikiDBDirPath)

		for dirPath in dirPaths:
			for fe in os.scandir(dirPath):
				try:
					mtime = fe.stat(follow_symlinks=False).st_mtime
					if mtime > t:
						t = mtime
				except:
					pass

		if t <= 0:
			return None
		else:
			return datetime.datetime.fromtimestamp(mtime)
	#

	#
	# This method returns a sorted list about installed extensions.
	#
	# @param			jk_logging.AbstractLogger log			(optional) A logger for debug output. If you run into problems loading and analyzing
	#															an extention (yes, that happens, as extensions might have errors) specify a debug logger
	#															here as all analyzing is done during runtime of this method.
	#															If you don't specify a logger, any kind of errors are silently ignored.
	#
	# @return			MediaWikiExtensionInfo[]				Returns extension information objects.
	#															Please note that versions in extension information objects are currently strings
	#															as some extensions use a completely non-standard versioning schema.
	#															(This might change in the future.)
	#
	@jk_typing.checkFunctionSignature()
	def getExtensionInfos(self, log:jk_logging.AbstractLogger = None) -> typing.List[MediaWikiExtensionInfo]:
		ret = []

		for fe in os.scandir(os.path.join(self.__wikiDirPath, "extensions")):
			if fe.is_dir():

				if log:
					with log.descend("Analyzing extension: " + fe.name) as log2:
						try:
							ext = MediaWikiExtensionInfo.loadFromDir(fe.path)
						except Exception as ee:
							log.error("Failed to load: " + fe.name)
							continue
				else:
					try:
						ext = MediaWikiExtensionInfo.loadFromDir(fe.path)
					except Exception as ee:
						#print("WARNING: Failed to load: " + fe.name)
						continue

				ret.append(ext)

		ret.sort(key=lambda x: x.name)

		return ret
	#

	def getDiskUsage(self) -> MediaWikiDiskUsageInfo:
		sizeCache = Utils.getDiskSpaceRecursively(os.path.join(self.__wikiDirPath, "cache"))
		sizeImages = Utils.getDiskSpaceRecursively(os.path.join(self.__wikiDirPath, "images"))
		sizeExtensions = Utils.getDiskSpaceRecursively(os.path.join(self.__wikiDirPath, "extensions"))
		sizeDatabase = Utils.getDiskSpaceRecursively(self.__wikiDBDirPath)

		sizeCore = 0
		for fe in os.scandir(self.__wikiDirPath):
			if fe.is_symlink():
				continue
			elif fe.is_file():
				n = fe.stat().st_size
				sizeCore += int(math.ceil(n / 4096) * 4096)
			elif fe.is_dir() and fe.name not in [ "images", "cache", "extensions" ]:
				sizeCore += Utils.getDiskSpaceRecursively(fe.path)

		return MediaWikiDiskUsageInfo(sizeCore, sizeCache, sizeImages, sizeExtensions, sizeDatabase)
	#

	################################################################################################################################
	## Static Methods
	################################################################################################################################

#




