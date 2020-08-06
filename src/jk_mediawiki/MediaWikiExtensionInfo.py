

import typing
import datetime
import collections

import jk_typing




class MediaWikiExtensionInfo(object):

	@jk_typing.checkFunctionSignature()
	def __init__(self, name:str, version:typing.Union[str,None], size:int, latestTimeStamp:typing.Union[datetime.datetime,None]):
		self.name = name
		self.version = version
		self.size = size
		self.latestTimeStamp = latestTimeStamp
	#

#













