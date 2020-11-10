#!/usr/bin/python





import re
import os
import sys





from jk_utils import TypedValue
from jk_utils.tokenizer import RegExBasedTokenizer, Token






def tokenValueToPHP(dataType:str, value):
	if dataType == "bool":
		return "true" if value else "false"
	elif dataType == "str2":
		return "\"" + PHP.encodeString(value) + "\""
	elif dataType == "str1":
		return "\'" + PHP.encodeString(value) + "\'"
	elif dataType == "int":
		return str(value)
	elif dataType == "op":
		return value
	elif dataType == "word":
		return value
	elif dataType == "magic":
		return value
	else:
		raise Exception("Implementation Error! (" + repr(dataType) + ", " + repr(value) + ")")
#

#### Add a "toPHP()" method to TypedValue

def __toPHP(someVar):
	return tokenValueToPHP(someVar.dataType, someVar.value)
#

setattr(TypedValue, "toPHP", __toPHP)









#
# This tokenizer parses a PHP file.
#
class PHPTokenizer(RegExBasedTokenizer):

	def __init__(self):
		super().__init__([
			( "phpintro", "<\\?php" ),
			( "phpoutro", "\\?>" ),
			( "str1", r"'", r"[^']*", r"'" ),
			( "str2", r"\"", r"[^\"]*", r"\"" ),
			( "int_1", r"[+-]?[1-9][0-9]*" ),
			( "int_2", r"0" ),
			( "varref", r"\$", r"[a-zA-Z_][a-zA-Z0-9_]*", None ),
			( "commentx", "#=#" ),
			( "comment_1", "#[^\n]*" ),
			( "comment_2", "//[^\n]*" ),
			( "comment_3", "/*[.*?]*/" ),
			( "lparen1", "\\(" ),
			( "rparen1", "\\)" ),
			( "lparen2", "\\[" ),
			( "rparen2", "\\]" ),
			( "lparen3", "\\{" ),
			( "rparen3", "\\}" ),
			( "semicolon", r";" ),
			( "bool_1", r"true" ),
			( "bool_2", r"false" ),
			( "null", r"null" ),
			( "word", r"[a-zA-Z_][a-zA-Z0-9_]*" ),
		])

		i = 1
		for op in [ "===", "!==", "<<=", ">>=", "<=>",
			"<>", "||", "&&", "==", "!=", "+=", "-=", "*=", "/=", "%=", "<=", ">=", "^=", "=>", "++", "--", ">>", "<<", "??", "->",
			"^", "!", "%", "+", "-", "*", "/", ".", ",", "?", ":", "~", "@", "&", "|", "=" ]:
			self.addTokenPattern("op_" + str(i), re.escape(op))
			i += 1

		self.compile()

		self.registerTypeParsingDelegate("int", "1", self.__parseInt)
		self.registerTypeParsingDelegate("int", "2", self.__parseInt)
		self.registerTypeParsingDelegate("str1", None, PHP.decodeString)
		self.registerTypeParsingDelegate("str2", None, PHP.decodeString)
		self.registerTypeParsingDelegate("bool", "1", self.__parseBool)
		self.registerTypeParsingDelegate("bool", "2", self.__parseBool)
		self.registerTypeParsingDelegate("null", None, self.__parseNull)
	#

	def __parseNull(self, rawTokenText):
		return None
	#

	def __parseBool(self, rawTokenText):
		return rawTokenText == "true"
	#

	def __parseInt(self, rawTokenText):
		return int(rawTokenText)
	#

	def tokenize(self, text, bEmitWhiteSpaces = False, bEmitNewLines = False, bEmitComments = False):
		for token in super().tokenize(text, bEmitWhiteSpaces, bEmitNewLines):
			if (token.type == "comment") and not bEmitComments:
				continue
			yield token
	#

#









class PHP(object):

	_REPL1 = {
		"n": "\n",
		"r": "\r",
		"t": "\t",
		"v": "\v",
		"e": "\x1B",
		"f": "\f",
	}

	_REPL2 = {
		"\x00": "\\0",
		"\x01": "\\x01",
		"\x02": "\\x02",
		"\x03": "\\x03",
		"\x04": "\\x04",
		"\x05": "\\x05",
		"\x06": "\\x06",
		"\x07": "\\x07",
		"\x08": "\\x08",
		"\t": "\\t",		# 0x09
		"\n": "\\n",		# 0x0a
		"\v": "\\v",		# 0x0b
		"\f": "\\f",		# 0x0c
		"\r": "\\r",		# 0x0d
		"\x0e": "\\x0e",
		"\x0f": "\\x0f",
		"\x10": "\\x10",
		"\x11": "\\x11",
		"\x12": "\\x12",
		"\x13": "\\x13",
		"\x14": "\\x14",
		"\x15": "\\x15",
		"\x16": "\\x16",
		"\x17": "\\x17",
		"\x18": "\\x18",
		"\x19": "\\x19",
		"\x1a": "\\x1a",
		"\x1b": "\\e",
		"\x1c": "\\x1c",
		"\x1d": "\\x1d",
		"\x1e": "\\x1e",
		"\x1f": "\\x1f",
		"\"": "\\\"",
		"\\": "\\\\",
	}

	_RE_OCTAL = re.compile("[0-7]{1,3}")
	_RE_HEX = re.compile("x[0-9A-Fa-f]{1,2}")
	_RE_UNICODE = re.compile("u{[0-9A-Fa-f]+}")

	"""
	@staticmethod
	def encode(someVar):
		if someVar.dataType == "bool":
			if someVar.value:
				return "true"
			else:
				return "false"
		elif someVar.dataType == "str":
			return PHP.encodeString(someVar.value)
		elif someVar.dataType == "int":
			return str(someVar.value)
		elif someVar.dataType == "const":
			return someVar.value
		else:
			raise Exception("Implementation Error!")
	#
	"""

	"""
	@staticmethod
	def parse(text):
		if text is None:
			return None

		if (text == "true") or (text == "false"):
			return TypedValue("bool", text == "true")

		patternStr = re.compile(r"^(?P<d>[\"'])(?P<v>.*)(?P=d)$")
		matchResult = patternStr.match(text)
		if matchResult:
			return TypedValue("str", PHP.decodeString(matchResult.group(2)))

		patternConst = re.compile(r"^(?P<v>[a-zA-Z_][a-zA-Z0-9_]*)$")
		matchResult = patternConst.match(text)
		if matchResult:
			return TypedValue("const", matchResult.group(1))

		patternInt = re.compile(r"^(?P<v>[+-]?[1-9][0-9]*)$")
		matchResult = patternInt.match(text)
		if matchResult:
			return TypedValue("int", int(matchResult.group(1)))

		if text.startswith("array(") and text.endswith(")"):
			text = text[6:]
			text = text[:-1]

		return None
	#
	"""

	#
	# Creates a text from a given string that directly could be inserted into a PHP source code file to represent a string.
	#
	@staticmethod
	def encodeString(someString):
		ret = ""
		for c in someString:
			ret += PHP._REPL2.get(c, c)
		return ret
	#

	#
	# Parses (= decodes) a PHP source code string.
	#
	# See: http://php.net/manual/en/language.types.string.php
	#
	@staticmethod
	def decodeString(someString):
		ret = ""
		bMasked = False
		i = 0
		imax = len(someString)
		while i < imax:
			c = someString[i]
			if bMasked:
				result = PHP._RE_UNICODE.match(someString, i)
				if result:
					clip = someString[i:result.endpos()]
					i += len(clip)
					ret += chr(int(clip))
				else:
					result = PHP._RE_HEX.match(someString, i)
					if result:
						clip = someString[i:result.endpos()]
						i += len(clip)
						if len(clip) == 1:
							clip = "0" + clip
						ret += chr(int(clip, 16))
					else:
						result = PHP._RE_OCTAL.match(someString, i)
						if result:
							clip = someString[i:result.endpos()]
							i += len(clip)
							while len(clip) < 3:
								clip = "0" + clip
							ret += chr(int(clip, 8))
						else:
							# fallback
							repl = PHP._REPL1.get(c, None)
							if repl is None:
								ret += c
							else:
								ret += repl
							i += 1
				bMasked = False
			else:
				if c == "\\":
					bMasked = True
				else:
					ret += c
				i += 1
		return ret
	#

#















