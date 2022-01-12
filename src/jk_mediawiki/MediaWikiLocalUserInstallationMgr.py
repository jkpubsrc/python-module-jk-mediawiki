

import math
import os
import typing
import datetime

import jk_utils
import jk_sysinfo
import jk_json
import jk_logging
import jk_typing
import jk_version

from .impl.Utils import Utils
from .impl.LocalWikiInstInfo import LocalWikiInstInfo
from .MediaWikiSkinInfo import MediaWikiSkinInfo
from .MediaWikiDiskUsageInfo import MediaWikiDiskUsageInfo
from .MediaWikiExtensionInfo import MediaWikiExtensionInfo
from .MWManagementCtx import MWManagementCtx
from .lsfile.MediaWikiLocalSettingsFile import MediaWikiLocalSettingsFile
from .impl.AbstractProcessFilter import AbstractProcessFilter
from .impl.OSProcessProvider import OSProcessProvider
from .impl.ProcessProviderCache import ProcessProviderCache
from .impl.ProcessFilter import ProcessFilter
from .impl.WikiCronProcessFilter import WikiCronProcessFilter
from .impl.WikiNGINXProcessFilter import WikiNGINXProcessFilter
from .impl.WikiPHPProcessFilter import WikiPHPProcessFilter






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
# TODO: Rename this class to MediaWikiLocalUserInstallationMgr as it represents a local user installation of a MediaWiki.
#
class MediaWikiLocalUserInstallationMgr(object):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Variables
	################################################################################################################################

	# @field		str __userName					The name of the user account under which NGINX, PHP and the Wiki cron process are executed.
	# @field		str __wikiInstDirPath				The absolute directory path where the MediaWiki installation can be found.
	# @field		str __wikiDirName				The name of the directory the Wiki resides in
	# @field		str __wikiDBDirPath				The directory where all the databases are stored
	# @field		str __cronScriptFilePath		The path of the cron script file
	# @field		str __cronScriptDirPath			For convenience: The directory where the cron script file resides in
	# @field		str __cronScriptFileName		For convenience: The name of the cron script file without it's parent directory information
	# @field		OSProcessProvider __osProcessProvider			A direct operating system process provider
	# @field		ProcessProviderCache __cachedOSProcessProvider	A cached operating system process provider
	################################################################################################################################
	## Constructor
	################################################################################################################################

	"""
	#
	# Configuration parameters:
	#
	# @param	MWManagementCtx ctx							A management context that provides common data.
	# @param	str mediaWikiInstDirPath					(required) The absolute directory path where the MediaWiki installation can be found.
	#														The final directory name in the path must be the same as the site name of the Wiki.
	#														Additionally there must be a cron script named "<sitename>cron.sh".
	#
	@jk_typing.checkFunctionSignature(logDescend="Analyzing MediaWiki installation at: {mediaWikiInstDirPath}")
	def __init__(self,
			ctx:MWManagementCtx,
			mediaWikiInstDirPath:str,
			log:jk_logging.AbstractLogger,
		):

		self.__ctx = ctx

		# check MediaWiki installation directory and load settings

		assert isinstance(mediaWikiInstDirPath, str)
		assert mediaWikiInstDirPath
		assert os.path.isdir(mediaWikiInstDirPath)
		assert os.path.isabs(mediaWikiInstDirPath)

		self.__wikiInstDirPath = mediaWikiInstDirPath

		assert os.path.isdir(self.wikiExtensionsDirPath)
		assert os.path.isdir(self.wikiImagesDirPath)
		assert os.path.isdir(self.wikiSkinsDirPath)
		assert os.path.isfile(self.wikiLocalSettingsFilePath)

		mwLocalSettings = MediaWikiLocalSettingsFile()
		mwLocalSettings.load(dirPath = mediaWikiInstDirPath)		# TODO: add logging

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

		self.__wikiDirName = os.path.basename(mediaWikiInstDirPath)
		if self.__wikiDirName.lower() != wikiSiteName.lower():
			raise Exception("Installation directory name does not match the MediaWiki site name! ("
				+ repr(self.__wikiDirName) + " vs. " + repr(wikiSiteName) + ")")

		self.__wikiBaseDirPath = os.path.dirname(mediaWikiInstDirPath)

		# wiki background task script

		expectedCronScriptFileName = self.__wikiDirName + "cron.sh"
		p = os.path.join(os.path.dirname(self.__wikiInstDirPath), expectedCronScriptFileName)
		if os.path.isfile(p):
			self.__cronScriptFilePath = p
		else:
			raise Exception("No cron script: " + repr(expectedCronScriptFileName))

		expectedStartCronScriptFileName = self.__wikiDirName + "cron-bg.sh"
		p = os.path.join(os.path.dirname(self.__wikiInstDirPath), expectedStartCronScriptFileName)
		if os.path.isfile(p):
			self.__startCronScriptFilePath = p
		else:
			raise Exception("No cron script: " + repr(expectedStartCronScriptFileName))

		self.__cronScriptDirPath = os.path.dirname(self.__cronScriptFilePath) if self.__cronScriptFilePath else None
		self.__cronScriptFileName = os.path.basename(self.__cronScriptFilePath) if self.__cronScriptFilePath else None
	#
	"""

	#
	# Configuration parameters:
	#
	# @param	MWManagementCtx ctx							A management context that provides common data.
	# @param	str mediaWikiInstDirPath					(required) The absolute directory path where the MediaWiki installation can be found.
	#														The final directory name in the path must be the same as the site name of the Wiki.
	#														Additionally there must be a cron script named "<sitename>cron.sh".
	#
	@jk_typing.checkFunctionSignature(logDescend="Analyzing MediaWiki installation: {mwInstInfo.name}")
	def __init__(self,
			ctx:MWManagementCtx,
			mwInstInfo:LocalWikiInstInfo,
			log:jk_logging.AbstractLogger,
		):

		self.__ctx = ctx

		# check MediaWiki installation directory and load settings

		assert mwInstInfo.isValid()

		self.__wikiInstDirPath = mwInstInfo.instRootDirPath

		assert os.path.isdir(self.wikiExtensionsDirPath)
		assert os.path.isdir(self.wikiImagesDirPath)
		assert os.path.isdir(self.wikiSkinsDirPath)
		assert os.path.isfile(self.wikiLocalSettingsFilePath)

		mwLocalSettings = MediaWikiLocalSettingsFile()
		mwLocalSettings.load(dirPath = mwInstInfo.instRootDirPath)		# TODO: add logging

		#mwLocalSettings.dump()			# DEBUG

		wikiSiteName = mwLocalSettings.getVarValue("wgSitename")
		if wikiSiteName is None:
			wikiSiteName = mwLocalSettings.getVarValue("siteName")
		if wikiSiteName is None:
			wikiSiteName = mwLocalSettings.getVarValue("wikiSiteName")
		if wikiSiteName is None:
			raise Exception("None of these variables exist: $wikiSiteName, $siteName, $wgSitename")

		if wikiSiteName.lower() != mwInstInfo.name.lower():
			raise Exception("Directory name does not match the MediaWiki site name! ("
				+ repr(mwInstInfo.name) + " vs. " + repr(wikiSiteName) + ")")
		self.__wikiSiteName = wikiSiteName

		self.__wikiDBDirPath = mwInstInfo.dbDirPath
		dbType = mwLocalSettings.getVarValueE("wgDBtype")
		if dbType == "sqlite":
			_sqliteDataDir = mwLocalSettings.getVarValueE("wgSQLiteDataDir")
			if self.__wikiDBDirPath != _sqliteDataDir:
				raise Exception("Actual database directory does not match the configured database directory! ("
					+ repr(self.__wikiDBDirPath) + " vs. " + repr(_sqliteDataDir) + ")")
		else:
			raise NotImplementedError("Backup of database not (yet) supported: " + dbType)

		self.__wikiBaseDirPath = os.path.dirname(mwInstInfo.instRootDirPath)

		# wiki background task script

		self.__cronScriptFilePath = mwInstInfo.cronShFilePath
		self.__startCronScriptFilePath = mwInstInfo.cronBgShFilePath

		self.__cronScriptDirPath = os.path.dirname(self.__cronScriptFilePath)
		self.__cronScriptFileName = os.path.basename(self.__cronScriptFilePath)
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def wikiLocalSettingsFilePath(self) -> typing.Union[str,None]:
		filePath = os.path.join(self.__wikiInstDirPath, "LocalSettings.php")
		if os.path.isfile(filePath):
			return filePath
		else:
			# raise Exception("No such file: " + filePath)
			return None
	#

	@property
	def wikiExtensionsDirPath(self) -> typing.Union[str,None]:
		ret = os.path.join(self.__wikiInstDirPath, "extensions")
		if os.path.isdir(ret):
			return ret
		else:
			#raise Exception("No such directory:" + ret)
			return None
	#

	@property
	def wikiSkinsDirPath(self) -> typing.Union[str,None]:
		ret = os.path.join(self.__wikiInstDirPath, "skins")
		if os.path.isdir(ret):
			return ret
		else:
			#raise Exception("No such directory:" + ret)
			return None
	#

	@property
	def wikiImagesDirPath(self) -> typing.Union[str,None]:
		ret = os.path.join(self.__wikiInstDirPath, "images")
		if os.path.isdir(ret):
			return ret
		else:
			#raise Exception("No such directory:" + ret)
			return None
	#

	@property
	def wikiDirName(self) -> str:
		return self.__wikiSiteName
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
		return self.__wikiInstDirPath
	#

	#
	# The parent directory of the media wiki installation.
	#
	# In recent installations this is the same as cronScriptDirPath.
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

	#
	# In recent installations this is the same as wikiBaseDirPath.
	#
	@property
	def cronScriptDirPath(self) -> str:
		return self.__cronScriptDirPath
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	@jk_typing.checkFunctionSignature()
	def __newMWCronProcessFilter(self, wikiInstDirPath:str = None) -> AbstractProcessFilter:
		return WikiCronProcessFilter(
			userName=self.__ctx.currentUserName,
			wikiInstDirPath=wikiInstDirPath,
			source=self.__ctx.osProcessProvider
		)
	#

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

		for fe in os.scandir(os.path.join(self.__wikiInstDirPath, "skins")):
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
	# (Re)load the MediaWiki file "LocalSettings.php" and return it.
	#
	def loadMediaWikiLocalSettingsFile(self) -> MediaWikiLocalSettingsFile:
		mwLocalSettings = MediaWikiLocalSettingsFile()
		mwLocalSettings.load(dirPath = self.__wikiInstDirPath)
		return mwLocalSettings
	#

	def stopCronScript(self, log = None):
		processProvider = self.getCronProcessesProvider()
		processes = processProvider()
		if processes:
			log.info("Now stopping cron background processes: " + str([ x["pid"] for x in processes ]))
			processProvider.invalidate()
			if not jk_utils.processes.killProcesses(processes, log):
				raise Exception("There were errors stopping the cron background script!")
		else:
			log.notice("No cron background processes active.")
	#

	def startCronScript(self, log = None):
		processProvider = self.getCronProcessesProvider()
		processes = processProvider()
		if processes:
			raise Exception("Cron process already running!")
		processProvider.invalidate()
		if not jk_utils.processes.runProcessAsOtherUser(
				accountName=self.__ctx.currentUserName,
				filePath=self.__startCronScriptFilePath,
				args=None,
				log=log
			):
			raise Exception("Starting cron process failed!")
	#

	#
	# Returns the master and child processes of the cron script.
	#
	@jk_typing.checkFunctionSignature()
	def getCronProcesses(self) -> typing.Union[typing.List[dict],None]:
		if self.__cronScriptDirPath is None:
			return None

		processList = self.__newMWCronProcessFilter(self.__wikiInstDirPath)()
		if not processList:
			return None

		return processList
	#

	@jk_typing.checkFunctionSignature()
	def getCronProcessesProvider(self) -> typing.Union[AbstractProcessFilter,None]:
		if self.__cronScriptDirPath is None:
			return None

		return self.__newMWCronProcessFilter(self.__wikiInstDirPath)
	#

	def getVersion(self) -> jk_version.Version:
		lookingForFilePrefix = "RELEASE-NOTES-"
		for entry in os.scandir(self.__wikiInstDirPath):
			if entry.is_file() and entry.name.startswith(lookingForFilePrefix):
				return jk_version.Version(entry.name[len(lookingForFilePrefix):])
		raise Exception("Can't determine version!")
	#

	def getSMWVersion(self) -> typing.Union[jk_version.Version,None]:
		p = os.path.join(self.__wikiInstDirPath, "extensions", "SemanticMediaWiki", "extension.json")
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

		dirPaths = [ self.__wikiInstDirPath ]
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

		for fe in os.scandir(os.path.join(self.__wikiInstDirPath, "extensions")):
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
		sizeCache = Utils.getDiskSpaceRecursively(os.path.join(self.__wikiInstDirPath, "cache"))
		sizeImages = Utils.getDiskSpaceRecursively(os.path.join(self.__wikiInstDirPath, "images"))
		sizeExtensions = Utils.getDiskSpaceRecursively(os.path.join(self.__wikiInstDirPath, "extensions"))
		sizeDatabase = Utils.getDiskSpaceRecursively(self.__wikiDBDirPath)

		sizeCore = 0
		for fe in os.scandir(self.__wikiInstDirPath):
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




