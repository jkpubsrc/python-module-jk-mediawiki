






import os
import typing

import jk_typing

from .AbstractProcessFilter import AbstractProcessFilter
from .ProcessFilter import ProcessFilter






class WikiPHPProcessFilter(AbstractProcessFilter):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self, userName:str, source:typing.Callable):
		# {
		#	'ppid': 1,
		#	'pid': 16406,
		#	'tty': None,
		#	'stat': 'Ss',
		#	'uid': 1000,
		#	'gid': 1000,
		#	'cmd': 'php-fpm:',
		#	'args': 'master process (/srv/wikis/etc/php/7.2/fpm/php-fpm.conf)',
		#	'user': 'woodoo',
		#	'group': 'woodoo'
		# }
		self.__filter1 = ProcessFilter(
			source = source,
			userName = userName,
			cmdExact="php-fpm:",
			argsEndsWith="/fpm/php-fpm.conf)",
		)

		self.__filter2 = ProcessFilter(
			source = source,
			userName = userName,
			cmdExact="php-fpm:",
			argsExact="pool www",
		)
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
			for x in ret:
				print(x)
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





