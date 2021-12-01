






import os
import typing

import jk_typing

from .ProcessFilter import ProcessFilter






class WikiCronProcessFilter(ProcessFilter):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self, userName:str, wikiInstDirPath:typing.Union[str,None], source:typing.Callable):
		# {
		#	'ppid': 21827,
		#	'pid': 21841,
		#	'tty': 'pts/7',
		#	'stat': 'S',
		#	'uid': 1000,
		#	'gid': 1000,
		#	'cmd': 'php',
		#	'args': '/srv/wikis/srv/wikis/infowiki/infowiki/maintenance/runJobs.php --wait',
		# 	'user': 'woodoo',
		# 	'group': 'woodoo'
		# }
		super().__init__(
			source = source,
			userName = userName,
			cmdExact="php",
			#argEndsWith="runJobs.php",
			argExact=os.path.join(wikiInstDirPath, "maintenance", "runJobs.php") if wikiInstDirPath else None
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

#





