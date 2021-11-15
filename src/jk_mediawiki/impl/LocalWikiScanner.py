


import os
import typing
import collections

import jk_typing



from .LocalWikiInstInfo import LocalWikiInstInfo






#
# This class is responsible for finding MediaWiki installation in a local directory tree.
#
class LocalWikiScanner(object):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self, wikiRootDir:str):
		self.__wikiRootDir = wikiRootDir
		self.__wikis = None
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def wikiRootDir(self) -> str:
		return self.__wikiRootDir
	#

	@property
	def wikiNames(self) -> typing.List[str]:
		if self.__wikis is None:
			self.__wikis = self.__identifyWikis(self.__wikiRootDir)

		return [ x.name for x in self.__wikis ]
	#

	@property
	def wikis(self) -> typing.List[LocalWikiInstInfo]:
		if self.__wikis is None:
			self.__wikis = self.__identifyWikis(self.__wikiRootDir)

		return list(self.__wikis)
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	@jk_typing.checkFunctionSignature()
	def __isWikiBaseDir(self, instDirPath:str) -> bool:
		if not os.path.isdir(instDirPath) \
			or not os.path.isdir(instDirPath + "db") \
			or not os.path.isfile(instDirPath + "cron.sh") \
			or not os.path.isfile(instDirPath + "cron-bg.sh"):
			return False
		return True
	#

	#
	# This method returns path to root directories of MediaWiki installation directories (= those directories that contain the LocalSettings.php)
	#
	def __identifyWikisStorageFormat1(self, wikiInstRootDir:str) -> typing.Iterable[LocalWikiInstInfo]:
		for fe in os.scandir(wikiInstRootDir):
			if fe.is_file() and fe.name.endswith("cron.sh"):
				wikiName = fe.name[:-7]
				instDirPath = os.path.join(wikiInstRootDir, wikiName)
				if self.__isWikiBaseDir(instDirPath):
					yield LocalWikiInstInfo(instDirPath, wikiName)
	#

	def __identifyWikisStorageFormat2(self, wikiInstRootDir:str) -> typing.Iterable[LocalWikiInstInfo]:
		for fe1 in os.scandir(wikiInstRootDir):
			if fe1.is_dir():
				wikiName = fe1.name
				instDirPath = os.path.join(wikiInstRootDir, wikiName, wikiName)
				if self.__isWikiBaseDir(instDirPath):
					yield LocalWikiInstInfo(instDirPath, wikiName)
	#

	def __identifyWikis(self, wikiRootDir:str) -> typing.List[LocalWikiInstInfo]:
		ret = []

		ret.extend(self.__identifyWikisStorageFormat1(wikiRootDir))
		ret.extend(self.__identifyWikisStorageFormat2(wikiRootDir))

		ret.sort(key=lambda x: x.name)

		return ret
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def clearCache(self):
		self.__wikis = None
	#

	def getWikiInstDirPath(self, wikiName:str):
		if self.__wikis is None:
			self.__wikis = self.__identifyWikis(self.__wikiRootDir)

		for x in self.__wikis:
			if x.name == wikiName:
				return x.instDirPath
		return None
	#

#








