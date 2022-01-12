

import os
import typing
import getpass
import datetime

import jk_typing
import jk_console
import jk_mediawiki
import jk_logging

from .impl.LocalWikiInstInfo import LocalWikiInstInfo
from .impl.LocalWikiScanner import LocalWikiScanner
from .MWManagementCtx import MWManagementCtx







def _formatMBytes(n:int) -> str:
	s = str(round(n, 1)) + "M"
	while len(s) < 7:
		s = " " + s
	return s
#

class _StatusOverviewResult(object):
	
	def __init__(self, table:jk_console.SimpleTable, pids:typing.List[int]):
		self.table = table
		self.pids = pids
	#

#









#
# This class manages the set of local MediaWiki installations.
#
class LocalMediaWikisMgr(object):

	################################################################################################################################
	## Constructors
	################################################################################################################################

	#
	# Constructor.
	#
	# @param		str wwwWikiRootDir			The directory where all local MediaWiki installations reside.
	#
	@jk_typing.checkFunctionSignature()
	def __init__(self, ctx:MWManagementCtx, wwwWikiRootDir:str, bVerbose:bool):
		if not os.path.isdir(wwwWikiRootDir):
			raise Exception("No such directory: \"{}\"".format(wwwWikiRootDir))
		self.__wwwWikiRootDir = os.path.abspath(wwwWikiRootDir)

		self.__userName = getpass.getuser()

		self.__bVerbose = bVerbose

		self.__wikiScanner = LocalWikiScanner(self.__wwwWikiRootDir)

		self.__ctx = ctx
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	#
	# The directory where all local MediaWiki installations reside.
	#
	@property
	def wwwWikiRootDir(self) -> str:
		return self.__wwwWikiRootDir
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	#
	# Collects a list of installed mediawikis
	#
	@jk_typing.checkFunctionSignature()
	def _getStatusOverview(self, wikiName:typing.Union[str,None], bWithDiskSpace:bool, bVerbose:bool, log:jk_logging.AbstractLogger) -> _StatusOverviewResult:
		wikiInsts = self.__wikiScanner.wikis

		pids = []

		t = jk_console.SimpleTable()
		rowData = [ "Wiki", "MW Version", "SMW Version", "Status", "Last configuration", "Last use", "Cron Script Processes" ]
		if bWithDiskSpace:
			rowData.append("SizeRO")
			rowData.append("SizeRW")
		t.addRow(*rowData).hlineAfterRow = True
		r = jk_console.Console.RESET

		for wikiInst in wikiInsts:
			if wikiName:
				if wikiInst.name != wikiName:
					continue

			blog = jk_logging.BufferLogger.create()
			try:
				with blog.descend("Checking wiki: " + wikiInst.name) as log2:
					h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(self.__ctx, wikiInst, log2)
					bIsRunning = h.isCronScriptRunning()
					c = jk_console.Console.ForeGround.STD_GREEN if bIsRunning else jk_console.Console.ForeGround.STD_DARKGRAY
					smVersion = h.getSMWVersion()
					lastCfgTime = h.getLastConfigurationTimeStamp()
					lastUseTime = h.getLastUseTimeStamp()
					processInfos = h.getCronProcesses()
					if processInfos:
						processPIDs = [ x["pid"] for x in processInfos ]
						pids.extend(processPIDs)
					rowData = [
						wikiInst.name,
						str(h.getVersion()),
						str(smVersion) if smVersion else "-",
						"running" if bIsRunning else "stopped",
						lastCfgTime.strftime("%Y-%m-%d %H:%M") if lastCfgTime else "-",
						lastUseTime.strftime("%Y-%m-%d %H:%M") if lastUseTime else "-",
						str(processPIDs) if bIsRunning else "-",
					]
					if pids:
						pids.extend(pids)
					if bWithDiskSpace:
						diskUsage = h.getDiskUsage()
						rowData.append(_formatMBytes(diskUsage.ro / 1048576))
						rowData.append(_formatMBytes(diskUsage.rw / 1048576))
					t.addRow(*rowData).color = c
			except jk_logging.ExceptionInChildContextException as ee:
				pass

			if blog.stats.hasAtLeastWarning or bVerbose:
				blog.forwardTo(log)

		return _StatusOverviewResult(t, pids)
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def getWikiInstDirPath(self, wikiName:str):
		return self.__wikiScanner.getWikiInstDirPath(wikiName)
	#

	#
	# Scan the disk to list all existing Wikis (= running and not running).
	#
	# @return		str[] wikiNames			The names of the wikis available.
	#
	def listWikis(self) -> list:
		return self.__wikiScanner.wikiNames
	#

	#
	# Collects a list of mediawikis installed
	#
	@jk_typing.checkFunctionSignature()
	def getStatusOverviewAll(self, bWithDiskSpace:bool, bVerbose:bool, log:jk_logging.AbstractLogger) -> _StatusOverviewResult:
		return self._getStatusOverview(None, bWithDiskSpace, bVerbose, log)
	#

	#
	# Collects a list of mediawikis installed
	#
	@jk_typing.checkFunctionSignature()
	def getStatusOverviewOne(self, wikiName:str, bWithDiskSpace:bool, bVerbose:bool, log:jk_logging.AbstractLogger) -> _StatusOverviewResult:
		return self._getStatusOverview(wikiName, bWithDiskSpace, bVerbose, log)
	#

	#
	# Get a matrix that lists all wikis with all extensions.
	#
	@jk_typing.checkFunctionSignature()
	def getExtensionMatrix(self, log:jk_logging.AbstractLogger) -> jk_console.SimpleTable:
		# str[] wikiNames
		# MediaWikiLocalUserInstallationMgr[] wikis
		# MediaWikiExtensionInfo[] wikiExtensionInfos

		wikiInsts = self.__wikiScanner.wikis
		wikiNames = [ wikiInst.name for wikiInst in wikiInsts ]
		wikis = [ jk_mediawiki.MediaWikiLocalUserInstallationMgr(wikiInst, self.__userName, log) for wikiInst in wikiInsts ]
		wikiExtensionInfos = []

		allExtensionNames = set()
		for i, wikiName in enumerate(wikiNames):
			with log.descend("Scanning: {}".format(wikiName)) as log2:
				try:
					if self.__bVerbose:
						extInfos = []
						for extInfo in wikis[i].getExtensionInfos(log2):
							extInfos.append(extInfo)
					else:
						extInfos = list(wikis[i].getExtensionInfos())
				except jk_logging.ExceptionInChildContextException as ee:
					log2.error("Stopping scanning for {} because of errors.".format(wikiName))
					extInfos = None
				except Exception as ee:
					log2.error(ee)
					log2.error("Stopping scanning for {} because of errors.".format(wikiName))
					extInfos = None

			wikiExtensionInfos.append(extInfos)
			if extInfos:
				for extInfo in extInfos:
					allExtensionNames.add(extInfo.name)
		allExtensionNames = sorted(allExtensionNames)

		allExtensionsRowIndex = { name:(i+2) for i, name in enumerate(allExtensionNames) }

		# prepare data matrix

		columnNames = [ "" ] + allExtensionNames
		rowNames = [ "" ] + wikiNames
		rowNames2 = [ "" ] + [ str(w.getVersion()) for w in wikis ]
		_emptyList = [ "-" for x in wikiNames ]
		_emptyList2 = [ 0 for x in wikiNames ]

		table = jk_console.SimpleTable()
		table.addRow(*rowNames)
		table.addRow(*rowNames2).hlineAfterRow = True
		table.row(0).color = jk_console.Console.ForeGround.STD_LIGHTCYAN
		table.row(1).color = jk_console.Console.ForeGround.STD_LIGHTCYAN

		rawTimeData = []

		for extensionName in allExtensionNames:
			dataRow = [ extensionName ] + _emptyList
			table.addRow(*dataRow)[0].color = jk_console.Console.ForeGround.STD_LIGHTCYAN
			rawTimeData.append(list(_emptyList2))

		# fill with raw data

		dtEpoch = datetime.datetime(1970, 1, 1)
		for _x, h in enumerate(wikis):
			colNo = _x + 1
			if wikiExtensionInfos[_x]:
				for extInfo in wikiExtensionInfos[_x]:
					rowNo = allExtensionsRowIndex[extInfo.name]

					s = str(extInfo.version) if extInfo.version else None
					if extInfo.latestTimeStamp:
						if s is None:
							s = extInfo.latestTimeStamp.strftime("%Y-%m-%d")
						rawTimeData[rowNo - 2][_x] = (extInfo.latestTimeStamp - dtEpoch).total_seconds()

					if s:
						table.row(rowNo)[colNo].value = s
					else:
						table.row(rowNo)[colNo].value = "?"
			else:
				for rowNo in allExtensionsRowIndex.values():
					table.row(rowNo)[colNo].value = "err"

		for _y in range(0, len(rawTimeData)):
			row = rawTimeData[_y]
			maxX = -1
			maxT2 = 0
			maxT = 0

			for _x in range(0, len(row)):
				if row[_x] > maxT:
					maxT2 = maxT
					maxT = row[_x]
					maxX = _x
				cell = table.row(_y + 2)[_x + 1]
				if cell.value == "err":
					cell.color = jk_console.Console.ForeGround.STD_RED
				else:
					cell.color = jk_console.Console.ForeGround.STD_DARKGRAY

			for _x in range(0, len(row)):
				cell = table.row(_y + 2)[_x + 1]
				if (maxT > 0) and (row[_x] == maxT):
					cell.color = jk_console.Console.ForeGround.STD_YELLOW
				elif (maxT2 > 0) and (row[_x] == maxT2):
					cell.color = jk_console.Console.ForeGround.STD_LIGHTGRAY

		# return table

		return table
	#

#






























