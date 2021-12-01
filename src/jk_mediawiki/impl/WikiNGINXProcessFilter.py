






import os
import typing

import jk_typing

from .AbstractProcessFilter import AbstractProcessFilter
from .ProcessFilter import ProcessFilter






class WikiNGINXProcessFilter(AbstractProcessFilter):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self, userName:str, source:typing.Callable):
		self.__filter1 = ProcessFilter(
			source = source,
			userName = userName,
			cmdExact="nginx:",
			#argsExact="master process nginx -c " + wikiDirTreeRoot + "/etc/nginx/nginx.conf -p " + wikiDirTreeRoot + "/",
			argsStartsWith="master process nginx -c",
		)

		self.__filter2 = ProcessFilter(
			source = source,
			userName = userName,
			cmdExact="nginx:",
		)

		#assert not wikiDirTreeRoot.endswith("/")
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
		ret = self.__filter1.listProcesses()

		if len(ret) == 0:
			return ret

		if len(ret) > 1:
			raise Exception("Ambiguous: Multiple master processes found!")

		self.__filter2.ppid = ret[0]["pid"]

		ret.extend(self.__filter2())

		return ret
	#

	def invalidate(self):
		self.__filter1.invalidate()
		self.__filter2.invalidate()
	#

#





