

import os
import codecs
import re
import shutil


from jk_utils import *
from jk_utils.tokenizer import *
import jk_console

from ..impl.lang_support_php import *

from .MediaWikiLocalSettingsVariableAssignment import MediaWikiLocalSettingsVariableAssignment
from .MediaWikiLocalSettingsComplexVariableAssignment import MediaWikiLocalSettingsComplexVariableAssignment
from .MediaWikiLocalSettingsArrayAppend import MediaWikiLocalSettingsArrayAppend






#
# This class represents the "LocalSettings.php" file in a MediaWiki installation.
#
# During loading the file data is parsed. Internally a line is stored in an array. Each array entry is a 3-tuple containing the following data:
# 0) An identifier specifying the type of the line: "-", "varappend", "var", "vari" and "varii"
# 1) The raw text of the line
# 2) An instance of <c>MediaWikiLocalSettingsValue</c> representing the parsed version of the line or <c>None</c> otherwise
#
class MediaWikiLocalSettingsFile(object):

	################################################################################################################################
	## Constants
	################################################################################################################################

	__VALUE_PATTERN = TokenPatternAlternatives([
		TokenPattern("str1"),
		TokenPattern("str2"),
		TokenPattern("int"),
		TokenPattern("bool"),
		TokenPattern("null"),
		TokenPattern("word"),
	])

	__OPTIONAL_SPACE_OR_NEWLINE = TokenPatternOptional(TokenPatternAlternatives([
		TokenPattern("SPACE"),
		TokenPattern("NEWLINE"),
	]))

	__VALUE_LIST_PATTERN = TokenPatternSequence([
		__VALUE_PATTERN.derive(assignToVarTyped = "value", bVarIsArray = True),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPatternOptional(TokenPatternRepeat(TokenPatternSequence([
			TokenPattern("op", ","),
			__OPTIONAL_SPACE_OR_NEWLINE,
			__VALUE_PATTERN.derive(assignToVarTyped = "value", bVarIsArray = True),
			__OPTIONAL_SPACE_OR_NEWLINE,
		])))
	])

	__PARSING_DEFAULTS = {
		"active": True,
	}

	__STMT_VARIABLE_APPENDING = TokenPatternSequence([
		TokenPatternOptional(TokenPatternSequence([
			TokenPattern("commentx").setTag("active", False),
			__OPTIONAL_SPACE_OR_NEWLINE,
		])),
		TokenPattern("varref", assignToVar = "varName"),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPattern("lparen2"),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPattern("rparen2"),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPattern("op", "="),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPatternAlternatives([
			TokenPatternSequence([
				TokenPattern("word", "array").setTag("varType", "array"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("lparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPatternOptional(__VALUE_LIST_PATTERN),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("rparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
			]),
			__VALUE_PATTERN.derive(assignToVarTyped = "value").setTag("varType", "value"),
		]),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPattern("semicolon"),
	])

	# $someVar = value
	# $someVar[value] = value
	# $someVar = array(value)
	# $someVar[value] = array(value)
	__STMT_VARIABLE_ASSIGNMENT = TokenPatternSequence([
		TokenPatternOptional(TokenPatternSequence([
			TokenPattern("commentx").setTag("active", False),
			__OPTIONAL_SPACE_OR_NEWLINE,
		])),
		TokenPattern("varref", assignToVar = "varName"),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPatternOptional(TokenPatternRepeat(TokenPatternSequence([
			TokenPattern("lparen2"),
			__OPTIONAL_SPACE_OR_NEWLINE,
			__VALUE_PATTERN.derive(assignToVarTyped = "index", bVarIsArray = True),
			__OPTIONAL_SPACE_OR_NEWLINE,
			TokenPattern("rparen2"),
			__OPTIONAL_SPACE_OR_NEWLINE,
		]))),
		TokenPattern("op", "="),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPatternAlternatives([
			TokenPatternSequence([
				TokenPattern("word", "array").setTag("varType", "array"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("lparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPatternOptional(__VALUE_LIST_PATTERN),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("rparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
			]),
			TokenPatternSequence([
				TokenPattern("word", "dirname"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("word", "__DIR__").setTag("varType", "dirValue"),
				__OPTIONAL_SPACE_OR_NEWLINE,
			]),
			TokenPatternSequence([
				TokenPattern("word", "dirname"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("word", "__FILE__").setTag("varType", "fileValue"),
				__OPTIONAL_SPACE_OR_NEWLINE,
			]),
			TokenPatternSequence([
				TokenPattern("word", "dirname"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("lparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("word", "__FILE__").setTag("varType", "dirValue"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("rparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
			]),
			TokenPatternSequence([
				TokenPattern("word", "dirname"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("lparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("word", "__DIR__").setTag("varType", "parentDirValue"),
				__OPTIONAL_SPACE_OR_NEWLINE,
				TokenPattern("rparen1"),
				__OPTIONAL_SPACE_OR_NEWLINE,
			]),
			__VALUE_PATTERN.derive(assignToVarTyped = "value").setTag("varType", "value"),
		]),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPattern("semicolon"),
	])

	__STMT_VARIABLE_ASSIGNMENT_2 = TokenPatternSequence([
		TokenPatternOptional(TokenPatternSequence([
			TokenPattern("commentx").setTag("active", False),
			__OPTIONAL_SPACE_OR_NEWLINE,
		])),
		TokenPattern("varref", assignToVar = "varName"),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPattern("op", "="),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPatternRepeat(
			TokenPatternAlternatives([
				TokenPattern("SPACE"),
				TokenPattern("varref").derive(assignToVarTyped = "x", bVarIsArray = True),
				TokenPattern("op", ".").derive(assignToVarTyped = "x", bVarIsArray = True),
				TokenPattern("str1").derive(assignToVarTyped = "x", bVarIsArray = True),
				TokenPattern("str2").derive(assignToVarTyped = "x", bVarIsArray = True),
			]),
		),
		__OPTIONAL_SPACE_OR_NEWLINE,
		TokenPattern("semicolon"),
	])

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	def __init__(self):
		self.__data = None
		self.__changedFlag = ChangedFlag(False)
		self.__filePath = None
		self.__magicVarValues = None
	#

	################################################################################################################################
	## Properties
	################################################################################################################################

	@property
	def isChanged(self):
		return self.__changedFlag.value
	#

	@property
	def isLoaded(self):
		return self.__data != None
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	#
	# For debugging purposes only: Write the internal state of this object to STDOUT.
	#
	def dump(self, onlyLineNumbers:list = None):
		if onlyLineNumbers is not None:
			assert isinstance(onlyLineNumbers, (set, tuple, list))
			onlyLineNumbers = set(onlyLineNumbers)

		print("MediaWikiLocalSettingsFile")
		print("\t__bChanged: " + str(self.__changedFlag))
		print("\t__filePath: " + str(self.__filePath))

		if self.__data != None:
			table = jk_console.SimpleTable()

			if onlyLineNumbers:
				bFirst = True
				bLastWasPoints = False
				for (b, data) in self.__data:
					if data.lineNo in onlyLineNumbers:
						if bFirst:
							bFirst = False
							if data.lineNo > 1:
								table.addRow("...", "...", "...")
						table.addRow(str(b), MediaWikiLocalSettingsFile.__getType(data), str(data))
						bLastWasPoints = False
					else:
						if not bLastWasPoints:
							table.addRow("...", "...", "...")
							bLastWasPoints = True
						bFirst = False
			else:
				for (b, data) in self.__data:
					table.addRow(str(b), MediaWikiLocalSettingsFile.__getType(data), str(data))
			print("\t__lines:")
			table.print(prefix="\t\t")
	#

	#
	# Load a LocalSettings.php file.
	#
	# Heart of this method is a parser that identifies PHP variable assignments. As we can not deal with all eventualities possible in PHP syntax
	# this parser will only recognize variable assignments similar to these examples:
	# * <c>$someVarName = 123;</c>
	# * <c>$someVarName = "abc";</c>
	# * <c>$someVarName = MY_CONSTANT;</c>
	# * <c>$someVarName = true;</c>
	# * <c>$someVarName = null;</c>
	# * <c>$someVarName = array();</c>
	# * <c>$someVarName[123] = 5;</c>
	# * <c>$someVarName[123] = array();</c>
	# * <c>$someVarName["xyz"][123] = array('abc', false, null);</c>
	# * <c>$someVarName[] = 123;</c>
	#
	# The data for loading can either be specified diretly (parameter: <c>rawText</c>), by exact file path (parameter: <c>filePath</c>) or by
	# specifying the installation directory (parameter: <c>dirPath</c>). <c>rawText</c> has higher precedence over <c>filePath</c>, which in turn
	# has higher precedence over <c>dirPath</c>.
	#
	# @param	str dirPath			The MediaWiki installation directory path.
	# @param	str filePath		The file path of the MediaWiki "LocalSettings.php" file.
	# @param	str rawText			The raw file content of a "LocalSettings.php" file.
	#
	def load(self, dirPath = None, filePath = None, rawText:str = None):			# TODO: add logging
		if rawText is not None:
			assert isinstance(rawText, str)
			filePath = None
		elif filePath is not None:
			assert isinstance(filePath, str)
			# TODO: add logging
			with codecs.open(filePath, "r", "utf-8") as f:
				rawText = f.read()
		elif dirPath is not None:
			assert isinstance(dirPath, str)
			filePath = os.path.join(dirPath, "LocalSettings.php")
			# TODO: add logging
			with codecs.open(filePath, "r", "utf-8") as f:
				rawText = f.read()
		else:
			raise Exception("At least one of the following arguments must be specified: 'rawText' or 'filePath'!")

		self.__magicVarValues = {
			"__FILE__": filePath,
			"__DIR__": dirPath,
			"dirname(__DIR__)": os.path.dirname(dirPath),
		}

		tokens = list(PHPTokenizer().tokenize(rawText, bEmitWhiteSpaces = True, bEmitComments = True, bEmitNewLines = True))
		#for t in tokens:
		#	print(t)

		# resultDataList will receive 2-tuples where
		# the first item indicates the entry type - either "arrayAppend", "varAssignComplex", "varAssign" or "other" - and
		# the second item will either be a token or a MediaWikiLocalSettingsValue.
		resultDataList = []
		pos = 0
		while pos < len(tokens):
			(bResult, n, data) = MediaWikiLocalSettingsFile.__STMT_VARIABLE_APPENDING.tryMatch(tokens, pos, MediaWikiLocalSettingsFile.__PARSING_DEFAULTS)
			if bResult:
				assert n > 0
				# interpret pattern encountered and store it
				resultDataList.append( ( "arrayAppend", MediaWikiLocalSettingsArrayAppend.parseFromDict(self.__changedFlag, data) ) )
				#print("--arrayAppend--")				# DEBUG
				#for i in range(0, n):					# DEBUG
				#	print("\t", tokens[pos+i])			# DEBUG

				# advance
				pos += n
				continue

			(bResult, n, data) = MediaWikiLocalSettingsFile.__STMT_VARIABLE_ASSIGNMENT.tryMatch(tokens, pos, MediaWikiLocalSettingsFile.__PARSING_DEFAULTS)
			if bResult:
				assert n > 0
				# interpret pattern encountered and store it
				resultDataList.append( ( "varAssign", MediaWikiLocalSettingsVariableAssignment.parseFromDict(self.__changedFlag, data) ) )
				#print("--varAssign--")					# DEBUG
				#for i in range(0, n):					# DEBUG
				#	print("\t", tokens[pos+i])			# DEBUG

				# advance
				pos += n
				continue

			(bResult, n, data) = MediaWikiLocalSettingsFile.__STMT_VARIABLE_ASSIGNMENT_2.tryMatch(tokens, pos, MediaWikiLocalSettingsFile.__PARSING_DEFAULTS)
			if bResult:
				assert n > 0
				# interpret pattern encountered and store it
				resultDataList.append( ( "varAssignComplex", MediaWikiLocalSettingsComplexVariableAssignment.parseFromDict(self.__changedFlag, data) ) )
				#print("--varAssignComplex--")			# DEBUG
				#for i in range(0, n):					# DEBUG
				#	print("\t", tokens[pos+i])			# DEBUG

				# advance
				pos += n
				continue

			resultDataList.append( ( "other", tokens[pos] ) )
			pos += 1

		#for b, t in resultDataList:
		#	print(str(b) + "\t\t" + str(t))

		#sys.exit(0)

		self.__data = resultDataList
		self.__filePath = filePath
		self.__changedFlag.setChanged(False)
	#

	#
	# Write the file (and all changes applied). If the data has not been loaded from a file calling this method will fail.
	# In that case use <c>toStr()</c> instead.
	#
	# Before writing to the file a backup file of "LocalSettings.php" named "LocalSettings.php.sav" is created.
	#
	def save(self):
		if not self.__changedFlag.value:
			return
		if self.__data is None:
			raise Exception("Not loaded!")
		if self.__filePath is None:
			raise Exception("Data was originally not loaded from a file!")
		shutil.copy2(self.__filePath, self.__filePath + ".sav")
		with codecs.open(self.__filePath, "w", "utf-8") as f:
			f.write(self.toStr())
		self.__changedFlag.setChanged(False)
	#

	#
	# (Re)Generate PHP data from the parsed text.
	#
	# @return	str			Returns the text.
	#
	def toStr(self) -> str:
		if self.__data is None:
			raise Exception("Not loaded!")
		ret = []
		for stype, item in self.__data:
			if stype == "other":
				if item.type == "varref":
					ret.append("$" + item.value)
				elif item.type in [ "bool", "str1", "str2", "int", "word" ]:
					ret.append(tokenValueToPHP(item.type, item.value))
				else:
					assert isinstance(item.value, str)
					ret.append(item.value)
			else:
				ret.append(item.toPHP())
		return "".join(ret)
	#

	#
	# (Re)Generate PHP data from the parsed text.
	#
	# @return	list		Returns a list of lines.
	#
	def toLines(self) -> list:
		if self.__data is None:
			raise Exception("Not loaded!")

		ret = []
		buffer = []

		for stype, item in self.__data:
			if stype == "other":
				if item.type == "NEWLINE":
					ret.append("".join(buffer))
					buffer.clear()
				elif item.type == "varref":
					buffer.append("$" + item.value)
				elif item.type in [ "bool", "str1", "str2", "int", "word" ]:
					buffer.append(tokenValueToPHP(item.type, item.value))
				else:
					assert isinstance(item.value, str)
					buffer.append(item.value)
			else:
				buffer.append(item.toPHP())

		if buffer:
			ret.append("".join(buffer))
		else:
			ret.append("")

		return ret
	#

	#
	# Get a variable value.
	# This method will resolve the value: If it contains magic constants or simple expressions the syntax will be evaluated and the resulting value returned.
	#
	# @return		value			This data or <c>None</c> if the variable does not exist.
	#
	def getVarValue(self, varName:str):
		assert isinstance(varName, str)

		item = self.getVar(varName)
		if item is not None:
			if isinstance(item, MediaWikiLocalSettingsComplexVariableAssignment):
				# type: MediaWikiLocalSettingsComplexVariableAssignment
				return item.getValue(self.getVarValueE)
			else:
				# type: TypeValue, MediaWikiLocalSettingsVariableAssignment, MediaWikiLocalSettingsArrayAppend
				v = item.value
				if isinstance(v, TypedValue):
					if v.dataType == "magic":
						# this is a "magic" variable. return the replacement value.
						return self.__magicVarValues[v.value]
					else:
						return v.value
				elif isinstance(v, list):
					ret = []
					for d in v:
						ret.append(d.value)
					return ret
				else:
					raise Exception("Implementation Error!")

		return None
	#

	#
	# Get a variable value.
	# This method will resolve the value: If it contains magic constants or simple expressions the syntax will be evaluated and the resulting value returned.
	#
	# @return		value			This data.
	#
	def getVarValueE(self, varName:str):
		assert isinstance(varName, str)

		item = self.getVarValue(varName)
		if item is not None:
			return item

		raise Exception("No such variable: " + repr(varName))
	#

	#
	# Get a variable-like object.
	#
	# @return		someObject			This object returned is either of type:
	#									* TypeValue - if it is a constant
	#									* MediaWikiLocalSettingsVariableAssignment - if it is a constant assigned to a variable
	#									* MediaWikiLocalSettingsComplexVariableAssignment - if it is a complex variable assignment
	#									* MediaWikiLocalSettingsArrayAppend - if it is a value appended to an array
	#
	def getVar(self, varName:str):
		assert isinstance(varName, str)

		for stype, item in self.__data:
			if stype in [ "arrayAppend", "varAssign", "varAssignComplex" ]:
				if item.varName == varName:
					return item

		return None
	#

	def getIndexedVar1(self, varName, indexValue1):
		assert isinstance(varName, str)
		assert isinstance(indexValue1, TypedValue)

		for stype, item in self.__data:
			if stype == "varAssign":
				if item.varName == varName:
					v = item.indexValue
					if (v != None) and (v == indexValue1):
						return item

		return None
	#

	def getIndexedVar2(self, varName, indexValue1, indexValue2):
		assert isinstance(varName, str)
		assert isinstance(indexValue1, TypedValue)
		assert isinstance(indexValue2, TypedValue)

		for stype, item in self.__data:
			if stype == "varAssign":
				if item.varName == varName:
					v = item.indexValue
					if (v != None) and (v == indexValue1) and (v == indexValue2):
						return item

		return None
	#

	def activateWiki(self):
		v = self.getVar("wgReadOnly")
		if v is None:
			return
		else:
			v.deactivate()
	#

	def deactivateWiki(self, text):
		v = self.getVar("wgReadOnly")
		if v is None:
			self.__data.append( ( "other", Token("NEWLINE", "\n", -1, -1) ) )
			self.__data.append( ( "other", Token("NEWLINE", "\n", -1, -1) ) )
			self.__data.append( ( "other", Token("NEWLINE", "\n", -1, -1) ) )
			self.__data.append( ( "other", Token("NEWLINE", "\n", -1, -1) ) )
			self.__data.append( ( "varAssign", MediaWikiLocalSettingsVariableAssignment(self.__changedFlag, -1, -1, True, "wgReadOnly", None, TypedValue("str1", text)) ) )
			self.__data.append( ( "other", Token("NEWLINE", "\n", -1, -1) ) )
			self.__data.append( ( "other", Token("NEWLINE", "\n", -1, -1) ) )
			self.__changedFlag.setChanged(True)
		else:
			v.setValue(TypedValue("str1", text))
			v.activate()	# set this line to state "active" if it is commented out
	#

	################################################################################################################################
	## Static Methods
	################################################################################################################################

	@staticmethod
	def __getType(something):
		tName = something.__class__.__name__
		return tName
	#

#













