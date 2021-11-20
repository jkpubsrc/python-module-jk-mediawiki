


import sys
import os
import typing
import getpass

import jk_typing
import jk_utils
import jk_logging
import jk_json
import jk_prettyprintobj

from .impl.ProcessProviderCache import ProcessProviderCache
from .impl.OSProcessProvider import OSProcessProvider







class MWManagementCtx(object):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self):
		self.__userPID = os.getuid()
		self.__userName = getpass.getuser()
		self.__osProcessProvider = ProcessProviderCache(OSProcessProvider())
		self.__homeDir = os.environ["HOME"]
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	@property
	def cfgFilePath(self) -> str:
		return os.path.join(self.__homeDir, ".config/wikilocalctrl.json")
	#

	@property
	def homeDir(self) -> str:
		return self.__homeDir
	#

	#
	# A (cachable) provider for processes.
	#
	@property
	def osProcessProvider(self) -> ProcessProviderCache:
		return self.__osProcessProvider
	#

	#
	# The name of the user account under which NGINX, PHP and the Wiki cron process are executed.
	#
	@property
	def currentUserName(self) -> str:
		return self.__userName
	#

	@property
	def currentUserPID(self) -> int:
		return self.__userPID
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

#









