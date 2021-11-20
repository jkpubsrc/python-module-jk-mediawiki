

import typing

import jk_typing

from .AbstractProcessFilter import AbstractProcessFilter







class ProcessFilter(AbstractProcessFilter):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self,
			source:typing.Callable,
			ppid:typing.Union[int,None] = None,
			userName:typing.Union[str,typing.List[str],None] = None,
			cmdExact:typing.Union[str,typing.List[str],None] = None,
			argExact:typing.Union[str,typing.List[str],None] = None,
			argEndsWith:typing.Union[str,typing.List[str],None] = None,
			argStartsWith:typing.Union[str,typing.List[str],None] = None,
			argContains:typing.Union[str,typing.List[str],None] = None,
			argsExact:typing.Union[str,typing.List[str],None] = None,
			argsEndsWith:typing.Union[str,typing.List[str],None] = None,
			argsStartsWith:typing.Union[str,typing.List[str],None] = None,
			argsContains:typing.Union[str,typing.List[str],None] = None,
		):
		assert callable(source)
		self.__source = source

		self.ppid = ppid
		self.userName = userName
		self.cmdExact = cmdExact
		self.argEndsWith = argEndsWith
		self.argStartsWith = argStartsWith
		self.argExact = argExact
		self.argContains = argContains
		self.argsEndsWith = argsEndsWith
		self.argsStartsWith = argsStartsWith
		self.argsExact = argsExact
		self.argsContains = argsContains
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	@jk_typing.checkFunctionSignature()
	def __isMatch(self, jData:dict, varName:str, fn:typing.Callable, validValueOrValues:typing.Union[str,int,typing.List[typing.Union[str,int]]]) -> bool:
		if isinstance(validValueOrValues, (str, int)):
			validValues = [ validValueOrValues ]
		else:
			validValues = validValueOrValues

		if varName not in jData:
			return False

		encounteredValueOrValues = jData[varName]
		if isinstance(encounteredValueOrValues, (tuple, list)):
			for x in encounteredValueOrValues:
				for validValue in validValues:
					if fn(x, validValue):
						return True
		else:
			x = encounteredValueOrValues
			for validValue in validValues:
				if fn(x, validValue):
					return True

		return False
	#

	def __test_any_eq(self, encounteredValue, referenceValue) -> bool:
		return encounteredValue == referenceValue
	#

	def __test_any_ne(self, encounteredValue, referenceValue) -> bool:
		return encounteredValue == referenceValue
	#

	def __test_str_endsWith(self, encounteredValue:str, referenceValue:str) -> bool:
		assert isinstance(encounteredValue, str)
		assert isinstance(referenceValue, str)
		return encounteredValue.endswith(referenceValue)
	#

	def __test_str_startsWith(self, encounteredValue:str, referenceValue:str) -> bool:
		assert isinstance(encounteredValue, str)
		assert isinstance(referenceValue, str)
		return encounteredValue.startswith(referenceValue)
	#

	def __test_str_contains(self, encounteredValue:str, referenceValue:str) -> bool:
		assert isinstance(encounteredValue, str)
		assert isinstance(referenceValue, str)
		return encounteredValue.find(referenceValue) >= 0
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def listProcesses(self) -> typing.List[dict]:
		ret = []

		for x in self.__source():
			# filter by ppid

			if self.ppid is not None:
				if not self.__isMatch(x, "ppid", self.__test_any_eq, self.ppid):
					continue

			# filter by user name

			if self.userName:
				if not self.__isMatch(x, "user", self.__test_any_eq, self.userName):
					continue

			#print("------ ", x)

			# filter by command

			if self.cmdExact:
				if not self.__isMatch(x, "cmd", self.__test_any_eq, self.cmdExact):
					continue

			# filter by argument

			if self.argStartsWith:
				if not self.__isMatch(x, "args_list", self.__test_str_startsWith, self.argStartsWith):
					continue

			if self.argEndsWith:
				if not self.__isMatch(x, "args_list", self.__test_str_endsWith, self.argEndsWith):
					continue

			if self.argExact:
				if not self.__isMatch(x, "args_list", self.__test_any_eq, self.argExact):
					continue

			if self.argContains:
				if not self.__isMatch(x, "args_list", self.__test_str_contains, self.argContains):
					continue

			if self.argsStartsWith:
				if not self.__isMatch(x, "args", self.__test_str_startsWith, self.argsStartsWith):
					continue

			if self.argsEndsWith:
				if not self.__isMatch(x, "args", self.__test_str_endsWith, self.argsEndsWith):
					continue

			if self.argsExact:
				if not self.__isMatch(x, "args", self.__test_any_eq, self.argsExact):
					continue

			if self.argsContains:
				if not self.__isMatch(x, "args", self.__test_str_contains, self.argsContains):
					continue

			ret.append(x)

		return ret
	#

	def invalidate(self):
		self.__source.invalidate()
	#

#









