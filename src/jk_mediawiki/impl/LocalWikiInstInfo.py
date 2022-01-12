


import os
import typing
import collections

import jk_typing
import jk_prettyprintobj
import jk_utils






#
# This class represents a MediaWiki installation on a local disk.
# It provides name and paths to essential directories and scripts as detected.
#
class LocalWikiInstInfo(jk_prettyprintobj.DumpMixin):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	# @param		str name				The name of the wiki
	# @param		str instDirPath		The directory where the 'LocalSettings.php' file is located
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self,
			*args,
			name:str,
			instRootDirPath:str,
			dbDirPath:str,
			cronShFilePath:str,
			cronBgShFilePath:str,
		):

		if args:
			raise jk_utils.ImplementationError("Call this method with named arguments only!")

		self.__name = name
		self.__instRootDirPath = os.path.abspath(instRootDirPath)
		self.__dbDirPath = os.path.abspath(dbDirPath)
		self.__cronShFilePath = os.path.abspath(cronShFilePath)
		self.__cronBgShFilePath = os.path.abspath(cronBgShFilePath)
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def name(self) -> str:
		return self.__name
	#

	@property
	def instRootDirPath(self) -> str:
		return self.__instRootDirPath
	#

	@property
	def dbDirPath(self) -> str:
		return self.__dbDirPath
	#

	@property
	def cronShFilePath(self) -> str:
		return self.__cronShFilePath
	#

	@property
	def cronBgShFilePath(self) -> str:
		return self.__cronBgShFilePath
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	def _dumpVarNames(self) -> list:
		return [
			"name",
			"instRootDirPath",
			"dbDirPath",
			"cronShFilePath",
			"cronBgShFilePath",
		]
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	#
	# Check if the wiki seems to exist with the specified layout
	# (meaning: all files and directories exist as expected)
	#
	def isValid(self) -> bool:
		if not os.path.isdir(self.__instRootDirPath):
			return False
		if not os.path.isdir(self.__dbDirPath):
			return False
		if not os.path.isfile(self.__cronShFilePath):
			return False
		if not os.path.isfile(self.__cronBgShFilePath):
			return False

		return True
	#

#












