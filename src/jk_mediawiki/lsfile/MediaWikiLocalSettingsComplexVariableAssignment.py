

import os


from jk_utils import *
from jk_utils.tokenizer import *

from ..impl.lang_support_php import *







class MediaWikiLocalSettingsComplexVariableAssignment(object):

	# ================================================================================================================================
	# ==== Constructor Methods

	def __init__(self, changedFlag:ChangedFlag, lineNo:int, colNo:int, bIsActive:bool, varName:str, x:list):
		assert isinstance(changedFlag, ChangedFlag)
		assert isinstance(lineNo, int)
		assert isinstance(colNo, int)
		assert isinstance(bIsActive, bool)
		assert isinstance(varName, str)
		assert isinstance(x, list)
		for xItem in x:
			assert isinstance(xItem, TypedValue)

		self.__changedFlag = changedFlag
		self.__lineNo = lineNo
		self.__colNo = colNo
		self.__bIsActive = bIsActive
		self.__varName = varName
		self.__x = x
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
	def isActive(self) -> bool:
		return self.__bIsActive
	#

	@property
	def isCommentedOut(self) -> bool:
		return not self.__bIsActive
	#

	# ================================================================================================================================
	# ==== Methods

	def toPHP(self):
		ret = "" if self.__bIsActive else "#=# "
		ret += "$" + self.__varName
		ret += " ="

		for xItem in self.__x:
			if xItem.dataType == "varref":
				ret += " $" + xItem.value
			else:
				ret += " " + xItem.toPHP()

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

	#
	# Use this method to obtain the value of this variable.
	#
	# @param		callable getValueCallback		A callback method that can be used to resolve other variables. This is necessary as this is the fundamental concept all this
	#												implementation here is about: values that are built from complex concatenations of strings.
	#
	def getValue(self, getValueCallback) -> str:
		assert callable(getValueCallback)

		ret = []

		for xItem in self.__x:
			dataType = xItem.dataType
			dataValue = xItem.value

			if dataType == "op":
				continue
			if dataType == "varref":
				v = getValueCallback(dataValue)
				assert isinstance(v, str)
				ret += v
			else:
				assert isinstance(dataValue, str)
				ret += dataValue

		return "".join(ret)
	#

	# ================================================================================================================================
	# ==== Static Methods

	#
	# Dictionary <c>dataMap</c> contains something like this:
	#
	# {
	# 	"lineNo": 21,
	#	"colNo": 1,
	#	"active": True,
	#	"varName": "wgSQLiteDataDir",
	#	"x": [
	#		V(varref: "rootDirPath"),
	#		V(op: "."),
	#		V(str1: "/"),
	#		V(op: "."),
	#		V(varref: "dirName"),
	#		V(op: "."),
	#		V(str1: "db")
	#	]
	# }
	#
	@staticmethod
	def parseFromDict(changedFlag:ChangedFlag, dataMap:dict):
		assert isinstance(changedFlag, ChangedFlag)
		assert isinstance(dataMap, dict)

		lineNo = dataMap["lineNo"]
		colNo = dataMap["colNo"]
		bIsActive = dataMap["active"]
		varName = dataMap["varName"]
		x = dataMap["x"]

		ret = MediaWikiLocalSettingsComplexVariableAssignment(changedFlag, lineNo, colNo, bIsActive, varName, x)
		return ret
	#

#











