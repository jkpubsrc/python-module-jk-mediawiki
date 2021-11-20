

import os
import typing

import jk_typing
import jk_sysinfo

from .AbstractProcessFilter import AbstractProcessFilter






class OSProcessProvider(AbstractProcessFilter):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self):
		pass
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

		# enrich the data dictionaries

		for x in jk_sysinfo.get_ps():
			if "args" in x:
				# naive splitting at spaces, regardless of the exact nature of the command line
				x["args_list"] = [ a.strip() for a in x["args"].split() ]
			else:
				# no arguments => empty list
				x["args_list"] = []
			ret.append(x)

		return ret
	#

	def invalidate(self):
		pass
	#

#









