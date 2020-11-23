

import typing
import datetime
import collections

import jk_typing
import jk_version

from .Utils import Utils










class MediaWikiExtensionInfo(object):

	@jk_typing.checkFunctionSignature()
	def __init__(self, extensionDirPath:str, name:str, version:typing.Union[str,jk_version.Version,None]):
		self.__extensionDirPath = extensionDirPath
		self.name = name
		self.__version = version
		self.__size = None
		self.__latestTimeStamp = None
		self.__latestTimeStamp_hasValue = False
	#

	@property
	def extensionDirPath(self) -> str:
		return self.__extensionDirPath
	#

	#@property
	#def name(self) -> str:
	#	return self.__name
	#

	@property
	def version(self) -> typing.Union[str,jk_version.Version,None]:
		return self.__version
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
		if self.__size is None:
			self.__size = Utils.getDiskSpaceRecursively(self.__extensionDirPath)
		return self.__size
	#

#













