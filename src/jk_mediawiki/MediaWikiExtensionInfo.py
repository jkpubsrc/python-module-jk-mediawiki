

import os
import typing
import datetime

import jk_typing
import jk_version
import jk_prettyprintobj
import jk_json

from .impl.Utils import Utils










class MediaWikiExtensionInfo(jk_prettyprintobj.DumpMixin):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Constructor
	################################################################################################################################

	@jk_typing.checkFunctionSignature()
	def __init__(self, extensionDirPath:str, jExtCfg:dict):
		self.__extensionDirPath = extensionDirPath
		self.__jExtCfg = jExtCfg
		self.__cachedSize = None
		self.__latestTimeStamp = None
		self.__latestTimeStamp_hasValue = False
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def extensionDirPath(self) -> str:
		return self.__extensionDirPath
	#

	@property
	def name(self) -> str:
		return self.__jExtCfg["name"]
	#

	@property
	def version(self) -> typing.Union[str,jk_version.Version,None]:
		if "version" not in self.__jExtCfg:
			return None
		s = self.__jExtCfg["version"]
		try:
			return jk_version.Version(s)
		except:
			return s
	#

	@property
	def latestTimeStamp(self) -> typing.Union[datetime.datetime,None]:
		if not self.__latestTimeStamp_hasValue:
			t = Utils.getLatestUseTimeStampRecursively(self.__extensionDirPath)
			if t > 0:
				self.__latestTimeStamp = datetime.datetime.fromtimestamp(t)
				self.__latestTimeStamp_hasValue = True
		return self.__latestTimeStamp
	#

	@property
	def size(self) -> int:
		if self.__cachedSize is None:
			self.__cachedSize = Utils.getDiskSpaceRecursively(self.__extensionDirPath)
		return self.__cachedSize
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	def _dumpVarNames(self):
		return [
			"name",
			"extensionDirPath",
			"version",
			"latestTimeStamp",
			"size",
		]
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	@staticmethod
	def loadFromDir(extensionDirPath:str):
		extFilePath = os.path.join(extensionDirPath, "extension.json")
		if not os.path.isfile(extFilePath):
			raise Exception("Not an extension directory: " + extensionDirPath)

		jExtCfg = jk_json.loadFromFile(extFilePath)
		if ("name" not in jExtCfg) or (jExtCfg.get("manifest_version") is None) or (jExtCfg.get("manifest_version") < 1):
			raise Exception("Not an extension: " + extensionDirPath)

		return MediaWikiExtensionInfo(extensionDirPath, jExtCfg)
	#

#












