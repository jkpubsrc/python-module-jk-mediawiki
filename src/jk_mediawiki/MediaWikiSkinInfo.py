

import os
import typing

import jk_typing
import jk_json
import jk_prettyprintobj







class MediaWikiSkinInfo(jk_prettyprintobj.DumpMixin):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self, skinDirPath:str, jSkinCfg:dict):
		self.__dirPath = skinDirPath
		self.__jSkinCfg = jSkinCfg
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def dirPath(self) -> str:
		return self.__dirPath
	#

	@property
	def name(self) -> str:
		return self.__jSkinCfg["name"]
	#

	@property
	def authors(self) -> typing.List[str]:
		return self.__jSkinCfg["author"]
	#

	@property
	def url(self) -> typing.Union[str,None]:
		return self.__jSkinCfg["url"]
	#

	@property
	def validNames(self) -> typing.List[str]:
		ret = [ self.name ]
		if self.__jSkinCfg.get("ValidSkinNames"):
			for k in self.__jSkinCfg["ValidSkinNames"].keys():
				if k not in ret:
					ret.append(k)
		return ret
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	def _dumpVarNames(self):
		return [
			"name",
			"validNames",
			"dirPath",
			"authors",
			"url",
		]
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

	@staticmethod
	def loadFromDir(skinDirPath:str):
		cfgFilePath = os.path.join(skinDirPath, "skin.json")
		if not os.path.isfile(cfgFilePath):
			raise Exception("Not a skin directory: " + skinDirPath)

		jSkinCfg = jk_json.loadFromFile(cfgFilePath)
		if (not jSkinCfg.get("name")) or (jSkinCfg.get("type") != "skin") or (jSkinCfg.get("manifest_version") != 1):
			raise Exception("Not a skin: " + skinDirPath)

		return MediaWikiSkinInfo(skinDirPath, jSkinCfg)
	#

#







