

import os
import typing

import jk_typing
import jk_utils
import jk_logging
import jk_json
import jk_prettyprintobj
import jk_sysinfo
import jk_cachefunccalls








class ProcessFilter(object):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self,
			source:typing.Callable,
			userName:str = None,
			cmdExact:str = None,
			argEndsWith:str = None,
			argExact:str = None,
			argStartsWith:str = None,
		):
		assert callable(source)
		self.__source = source

		self.__userName = userName
		self.__cmdExact = cmdExact
		self.__argEndsWith = argEndsWith
		self.__argExact = argExact
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def listProcesses(self) -> typing.List[dict]:
		ret = []

		for x in self.__source():

			# filter by user name

			if self.__userName:
				if x["user"] != self.__userName:
					continue

			# filter by command

			if self.__cmdExact:
				if x["cmd"] != self.__cmdExact:
					continue

			# filter by argument

			if self.__argEndsWith:
				bFound = False
				for arg in x["args"].split(" "):
					arg = arg.strip()
					if arg.endswith(self.__argEndsWith):
						bFound = True
						break
				if not bFound:
					continue

			if self.__argExact:
				bFound = False
				for arg in x["args"].split(" "):
					arg = arg.strip()
					if arg == self.__argExact:
						bFound = True
						break
				if not bFound:
					continue

			ret.append(x)

		return ret
	#

	def __call__(self):
		return self.listProcesses()
	#

#









