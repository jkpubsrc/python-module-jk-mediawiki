

import os


from jk_utils import *
from jk_utils.tokenizer import *

from ..impl.lang_support_php import *







class MediaWikiLocalSettingsVariableAssignment(object):

	# ================================================================================================================================
	# ==== Constructor Methods

	def __init__(self, changedFlag:ChangedFlag, lineNo:int, colNo:int, bIsActive:bool, varName:str, varIndexList:list, value):
		assert isinstance(changedFlag, ChangedFlag)
		assert isinstance(lineNo, int)
		assert isinstance(colNo, int)
		assert isinstance(bIsActive, bool)
		assert isinstance(varName, str)
		if varIndexList is not None:
			assert isinstance(varIndexList, list)
		else:
			varIndexList = []
		assert isinstance(value, (TypedValue, list))
		if isinstance(value, list):
			for item in value:
				assert isinstance(item, TypedValue)
		else:
			assert isinstance(value, TypedValue)

		self.__changedFlag = changedFlag
		self.__lineNo = lineNo
		self.__colNo = colNo
		self.__bIsActive = bIsActive
		self.__varName = varName
		self.__varIndexList = varIndexList
		self.__value = value
	#

	# ================================================================================================================================
	# ==== Properties

	@property
	def lineNo(self) -> int:
		return self.__lineNo
	#

	@property
	def colNo(self) -> int:
		return self.__colNo
	#

	@property
	def varName(self) -> str:
		return self.__varName
	#

	@property
	def indexValues(self):
		return list(self.__varIndexList)
	#

	@property
	def value(self):
		return self.__value
	#

	@property
	def isActive(self) -> bool:
		return self.__bIsActive
	#

	@property
	def isCommentedOut(self) -> bool:
		return not self.__bIsActive
	#

	# ================================================================================================================================
	# ==== Methods

	def indexValue(self, pos:int):
		assert isinstance(pos, int)

		if (pos < 0) or (pos >= len(self.__varIndexList)):
			return None
		return self.__varIndexList[pos]
	#

	def setValue(self, value):
		if value is list:
			for item in value:
				assert isinstance(item, TypedValue)
		else:
			assert isinstance(value, TypedValue)
		self.__value = value
		self.__changedFlag.setChanged(True)
	#

	def toPHP(self):
		ret = "" if self.__bIsActive else "#=# "
		ret += "$" + self.__varName
		for index in self.__varIndexList:
			ret += "[" + index.toPHP() + "]"
		ret += " = "
		if isinstance(self.__value, list):
			ret += "array("
			bNeedComma = False
			for item in self.__value:
				if bNeedComma:
					ret += ","
				else:
					bNeedComma = True
				ret += item.toPHP()
			ret += ")"
		else:
			ret += self.__value.toPHP()
		ret += ";"
		return ret
	#

	def __str__(self):
		return self.toPHP()
	#

	def __repr__(self):
		return self.toPHP()
	#

	def activate(self):
		if not self.__bIsActive:
			self.__bIsActive = True
			self.__changedFlag.setChanged(True)
	#

	def deactivate(self):
		if self.__bIsActive:
			self.__bIsActive = False
			self.__changedFlag.setChanged(True)
	#

	# ================================================================================================================================
	# ==== Static Methods

	@staticmethod
	def parseFromDict(changedFlag:ChangedFlag, dataMap:dict):
		assert isinstance(changedFlag, ChangedFlag)
		assert isinstance(dataMap, dict)

		lineNo = dataMap["lineNo"]
		colNo = dataMap["colNo"]
		bIsActive = dataMap["active"]
		varName = dataMap["varName"]
		varType = dataMap["varType"]
		assert varType in [ "value", "array", "parentDirValue", "fileValue", "dirValue" ]
		value = dataMap.get("value", None)
		if value is None:
			if varType == "array":
				value = []
			elif varType == "fileValue":
				value = TypedValue("magic", "__FILE__")
			elif varType == "dirValue":
				value = TypedValue("magic", "__DIR__")
			elif varType == "parentDirValue":
				value = TypedValue("magic", "dirname(__DIR__)")
			else:
				assert value != None
		varIndexList = dataMap.get("index", None)

		return MediaWikiLocalSettingsVariableAssignment(changedFlag, lineNo, colNo, bIsActive, varName, varIndexList, value)
	#

#











