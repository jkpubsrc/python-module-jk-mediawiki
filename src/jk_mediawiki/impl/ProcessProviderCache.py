

import os
import typing
import time

import jk_typing

from .AbstractProcessFilter import AbstractProcessFilter






class ProcessProviderCache(AbstractProcessFilter):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self, source:AbstractProcessFilter, cachingSeconds:int = 2):
		assert cachingSeconds > 0

		self.__source = source
		self.__cachingSeconds = cachingSeconds
		self.__lastT = 0
		self.__lastData = None
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
		tNow = time.time()
		tAge = tNow - self.__lastT

		if (tAge > 1) or (self.__lastData is None):
			self.__lastData = self.__source.listProcesses()
			self.__lastT = tNow

		return self.__lastData
	#

	def invalidate(self):
		self.__lastData = None
		self.__source.invalidate()
	#

#









