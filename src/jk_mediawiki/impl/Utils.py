

import os
import math







class Utils(object):

	@staticmethod
	def getLatestUseTimeStampRecursively(dirPath:str) -> int:
		t = 0
		for fe in os.scandir(dirPath):
			if fe.is_symlink():
				continue
			elif fe.is_file():
				mtime = fe.stat(follow_symlinks=False).st_mtime
				if mtime > t:
					t = mtime
			elif fe.is_dir():
				mtime = Utils.getLatestUseTimeStampRecursively(fe.path)
				if mtime > t:
					t = mtime
		return t
	#

	@staticmethod
	def getDiskSpaceRecursively(dirPath:str) -> int:
		ret = 0
		for fe in os.scandir(dirPath):
			if fe.is_symlink():
				continue
			elif fe.is_file():
				n = fe.stat().st_size
				ret += int(math.ceil(n / 4096) * 4096)
			elif fe.is_dir():
				ret += Utils.getDiskSpaceRecursively(fe.path)
		return ret
	#

	@staticmethod
	def getDiskSpaceNonRecursively(dirPath:str) -> int:
		ret = 0
		for fe in os.scandir(dirPath):
			if fe.is_symlink():
				continue
			elif fe.is_file():
				n = fe.stat().st_size
				ret += int(math.ceil(n / 4096) * 4096)
		return ret
	#

#





























