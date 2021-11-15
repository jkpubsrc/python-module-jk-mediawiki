

import os


from jk_utils import *
from jk_utils.tokenizer import *

from ..impl.lang_support_php import *







class MediaWikiLocalSettingsArrayAppend(object):

	# ================================================================================================================================
	# ==== Constructor Methods

	def __init__(self, changedFlag:ChangedFlag, lineNo:int, colNo:int, bIsActive:bool, varName:str, value):
		assert isinstance(changedFlag, ChangedFlag)
		assert isinstance(lineNo, int)
		assert isinstance(colNo, int)
		assert isinstance(bIsActive, bool)
		assert isinstance(varName, str)
		assert isinstance(value, TypedValue)

		self.__changedFlag = changedFlag
		self.__lineNo = lineNo
		self.__colNo = colNo
		self.__bIsActive = bIsActive
		self.__varName = varName
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

	def setValue(self, value):
		assert isinstance(value, TypedValue)
		self.__value = value
		self.__changedFlag.setChanged(True)
	#

	def toPHP(self):
		ret = "" if self.__bIsActive else "#=# "
		ret += "$" + self.__varName
		ret += "[] = "
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
		assert varType == "value"
		value = dataMap["value"]
		assert isinstance(value, TypedValue)

		return MediaWikiLocalSettingsArrayAppend(changedFlag, lineNo, colNo, bIsActive, varName, value)
	#

#







