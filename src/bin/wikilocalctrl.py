#!/usr/bin/python3

import time
import datetime
import os
import getpass
import sys
import typing

import jk_argparsing
import jk_json
import jk_mediawiki
import jk_logging
import jk_typing
import jk_console
import jk_mounting
import jk_sysinfo





# initialize argument parser

ap = jk_argparsing.ArgsParser(
	"wikilocalctrl [options] <command>",
	"Manage local Wiki installations.")
ap.createAuthor("Jürgen Knauth", "jk@binary-overflow.de")
ap.setLicense("apache")

# set defaults

ap.optionDataDefaults.set("bShowHelp", False)
ap.optionDataDefaults.set("bShowVersion", False)
ap.optionDataDefaults.set("wwwWikiRootDir", None)
ap.optionDataDefaults.set("httpBinDir", None)

# arguments

ap.createOption('h', 'help', "Display this help text and then exit.").onOption = \
	lambda argOption, argOptionArguments, parsedArgs: parsedArgs.optionData.set("bShowHelp", True)
ap.createOption(None, 'version', "Display the version of this software and then exit.").onOption = \
	lambda argOption, argOptionArguments, parsedArgs: parsedArgs.optionData.set("bShowVersion", True)
ap.createOption('w', 'wwwwikirootdir', "The root directory for the local wiki installations.").onOption = \
	lambda argOption, argOptionArguments, parsedArgs: parsedArgs.optionData.set("wwwWikiRootDir", True)
ap.createOption('d', 'httpbindir', "The root directory for the web server start script(s).").onOption = \
	lambda argOption, argOptionArguments, parsedArgs: parsedArgs.optionData.set("httpBinDir", True)

# return codes

ap.createReturnCode(0, "Operation successfully completed.")
ap.createReturnCode(1, "An error occurred.")

# commands

ap.createCommand("df", "Show only disk usage information.")
ap.createCommand("help", "Display this help text.")
ap.createCommand("httpstart", "Start the HTTP service(s).")
ap.createCommand("httpstop", "Stop the HTTP service(s).")
ap.createCommand("httpstatus", "Status about the HTTP service(s).")
ap.createCommand("httprestart", "Restart the HTTP service(s).")
ap.createCommand("wikistatus", "List existing local Wikis and their status.")
ap.createCommand("wikistop", "Stop a Wiki service.").expectString("wikiName", minLength=1)
ap.createCommand("wikistart", "Start a Wiki service.").expectString("wikiName", minLength=1)
ap.createCommand("status", "List status of HTTP service(s) and local Wikis.")
ap.createCommand("statusfull", "List full status of HTTP service(s) and local Wikis.")
ap.createCommand("start", "Start relevant service(s) to run a specific wiki.").expectString("wikiName", minLength=1)
ap.createCommand("stop", "Stop relevant service(s) to terminate a specific wiki.").expectString("wikiName", minLength=1)
ap.createCommand("extensionmatrix", "Display a matrix about all wiki extensions.")




#
# @param	dict cfg			The content of the user specific configuration file "~/.config/wikilocalctrl.json"
#
@jk_typing.checkFunctionSignature()
def getHttpdCfg(cfg:dict):
	if cfg["httpBinDir"] is None:
		raise Exception("Missing configuration: 'httpBinDir'")
	startNGINXScriptPath = os.path.join(cfg["httpBinDir"], "start-nginx-bg.sh")
	if not os.path.isfile(startNGINXScriptPath):
		raise Exception("Missing script: \"start-nginx-bg.sh\"")
	startPHPFPMScriptPath = os.path.join(cfg["httpBinDir"], "start-php-fpm-bg.sh")
	if not os.path.isfile(startPHPFPMScriptPath):
		raise Exception("Missing script: \"start-php-fpm-bg.sh\"")
	return startNGINXScriptPath, startPHPFPMScriptPath
#

@jk_typing.checkFunctionSignature()
def waitForServiceStarted(fnGetPIDInfos, name:str, log:jk_logging.AbstractLogger):
	assert callable(fnGetPIDInfos)

	countDown = 20
	while True:
		time.sleep(0.5)
		pidInfos = fnGetPIDInfos()
		if pidInfos:
			log.success("Local " + name + ": " + str([ x["pid"] for x in pidInfos ]))
			break
		countDown-= 1
		if countDown == 0:
			raise Exception("Failed to start " + name + "!")
#

@jk_typing.checkFunctionSignature()
def waitForServiceStopped(fnGetPIDInfos, name:str, log:jk_logging.AbstractLogger):
	assert callable(fnGetPIDInfos)

	countDown = 40
	while True:
		time.sleep(0.5)
		pidInfos = fnGetPIDInfos()
		if not pidInfos:
			break
		countDown-= 1
		if countDown == 0:
			raise Exception("Failed to stop " + name + "!")
#

#
# Get a list of all existing Wikis (= running and not running).
#
# @param		dict cfg			The content of the user specific configuration file "~/.config/wikilocalctrl.json"
# @return		str wwwWikiRootDir		The root directory for all local wikis
# @return		str[] wikiNames			The names of the wikis available.
#
def listWikis(cfg:dict) -> typing.Tuple[str,typing.List[str]]:
	if cfg["wwwWikiRootDir"] is None:
		raise Exception("Missing configuration: 'wwwWikiRootDir'")
	if not os.path.isdir(cfg["wwwWikiRootDir"]):
		raise Exception("No such directory: \"" + cfg["wwwWikiRootDir"] + "\"")
	candidates = []
	for entry in os.scandir(cfg["wwwWikiRootDir"]):
		if entry.name.endswith("cron.sh"):
			candidates.append(entry.name[:-7])
	ret = []
	for candidate in candidates:
		basePath = os.path.join(cfg["wwwWikiRootDir"], candidate)
		if os.path.isdir(basePath) \
			and os.path.isdir(basePath + "db") \
			and os.path.isfile(basePath + "cron.sh") \
			and os.path.isfile(basePath + "cron-bg.sh"):
			ret.append(candidate)
	return cfg["wwwWikiRootDir"], sorted(ret)
#



#
# @param		dict cfg			The content of the user specific configuration file "~/.config/wikilocalctrl.json"
#
def cmd_httpstatus(cfg:dict, log) -> list:
	pids = []

	startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
	h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

	t = jk_console.SimpleTable()
	t.addRow("Service", "Status", "Main Process(es)").hlineAfterRow = True
	r = jk_console.Console.RESET

	nginxPIDs = h.getNGINXMasterProcesses()
	c = jk_console.Console.ForeGround.STD_GREEN if nginxPIDs else jk_console.Console.ForeGround.STD_DARKGRAY
	if nginxPIDs:
		pids.extend([ x["pid"] for x in nginxPIDs ])
		t.addRow("Local NGINX", "running", str([ x["pid"] for x in nginxPIDs ])).color = c
	else:
		t.addRow("Local NGINX", "stopped", "-").color = c

	phpPIDs = h.getPHPFPMMasterProcesses()
	c = jk_console.Console.ForeGround.STD_GREEN if phpPIDs else jk_console.Console.ForeGround.STD_DARKGRAY
	if phpPIDs:
		pids.extend([ x["pid"] for x in phpPIDs ])
		t.addRow("Local PHP-FPM", "running", str([ x["pid"] for x in phpPIDs ])).color = c
	else:
		t.addRow("Local PHP-FPM", "stopped", "-").color = c

	print()
	t.print()

	return pids
#





def _formatMBytes(n:int) -> str:
	s = str(round(n, 1)) + "M"
	while len(s) < 7:
		s = " " + s
	return s
#

def wrapped_cmd_wikistatus(cfg:dict, bWithDiskSpace:bool, log) -> list:
	blog = jk_logging.BufferLogger.create()
	try:
		return cmd_wikistatus(cfg, bWithDiskSpace, blog)
	except jk_logging.ExceptionInChildContextException as ee:
		blog.forwardTo(log)
		raise
#

def print_mem_used_by_pids(pids:list):
	pids = set(pids)
	totalMemKB = 0
	for jStruct in jk_sysinfo.get_ps():
		if jStruct["pid"] in pids:
			if "vmsizeKB" in jStruct:
				totalMemKB += jStruct["vmsizeKB"]

	print()
	print("Total memory used: " + (_formatMBytes(totalMemKB/1024) if totalMemKB else "???"))
#

#
# @param	dict cfg			The content of the user specific configuration file "~/.config/wikilocalctrl.json"
#
def cmd_wikistatus(cfg:dict, bWithDiskSpace:bool, log) -> list:
	wwwWikiRootDir, wikiNames = listWikis(cfg)

	pids = []

	t = jk_console.SimpleTable()
	rowData = [ "Wiki", "MW Version", "SMW Version", "Status", "Last configuration", "Last use", "Cron Script Processes" ]
	if bWithDiskSpace:
		rowData.append("SizeRO")
		rowData.append("SizeRW")
	t.addRow(*rowData).hlineAfterRow = True
	r = jk_console.Console.RESET

	for wiki in wikiNames:
		with log.descend("Checking wiki: " + wiki) as log2:
			h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)
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
				wiki,
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

	print()
	t.print()

	return pids
#




def _formatGBytes(n:int) -> str:
	s = str(round(n, 1)) + "G"
	return s
#

#
# @param	dict cfg			The content of the user specific configuration file "~/.config/wikilocalctrl.json"
#
def cmd_diskfree(cfg:dict, log):
	print()

	mounter = jk_mounting.Mounter()
	mi = mounter.getMountInfoByFilePath(cfg["wwwWikiRootDir"])
	stdout, stderr, exitcode = jk_sysinfo.run(None, "/bin/df -BK")
	ret = jk_sysinfo.parse_df(stdout, stderr, exitcode)[mi.mountPoint]

	print("Mount point:", mi.mountPoint)

	fBlock = (ret["spaceTotal"] - ret["spaceFree"]) / ret["spaceTotal"]
	barLength = min(jk_console.Console.width(), 140) - 20
	iBlock = int(round(fBlock*barLength))
	text = "{0} {1:.1f}% filled".format( "#"*iBlock + ":"*(barLength-iBlock), fBlock*100)
	print(text)

	print(
		_formatGBytes((ret["spaceTotal"] - ret["spaceFree"]) / 1073741824),
		"of",
		_formatGBytes(ret["spaceTotal"] / 1073741824),
		"used."
		)
#




def cmd_extensionmatrix(cfg:dict, log):
	print()

	wwwWikiRootDir, wikiDirNames = listWikis(cfg)
	wikiNames = sorted(wikiDirNames)
	wikis = [ jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName) for wiki in wikiNames ]

	allExtensionNames = set()
	for i, wikiName in enumerate(wikiNames):
		h = wikis[i]
		for extInfo in h.getExtensionInfos():
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
		for extInfo in h.getExtensionInfos():
			colNo = _x + 1
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
			table.row(_y + 2)[_x + 1].color = jk_console.Console.ForeGround.STD_DARKGRAY
		for _x in range(0, len(row)):
			if (maxT > 0) and (row[_x] == maxT):
				table.row(_y + 2)[_x + 1].color = jk_console.Console.ForeGround.STD_YELLOW
			elif (maxT2 > 0) and (row[_x] == maxT2):
				table.row(_y + 2)[_x + 1].color = jk_console.Console.ForeGround.STD_LIGHTGRAY

	# print table

	table.print()
#





log = jk_logging.ConsoleLogger.create(logMsgFormatter=jk_logging.COLOR_LOG_MESSAGE_FORMATTER)








#MediaWikiLocalUserServiceMgr
try:
	parsedArgs = ap.parse()

	if parsedArgs.optionData["bShowVersion"]:
		print(jk_mediawiki.__version__)
		sys.exit(1)

	if parsedArgs.optionData["bShowHelp"]:
		ap.showHelp()
		sys.exit(1)

	if len(parsedArgs.programArgs) == 0:
		ap.showHelp()
		sys.exit(1)

	# load configuration: merge it with specified arguments

	userName = getpass.getuser()
	homeDir = os.environ["HOME"]
	cfgPath = os.path.join(homeDir, ".config/wikilocalctrl.json")
	if os.path.isfile(cfgPath):
		cfg = jk_json.loadFromFile(cfgPath)
	else:
		raise Exception("No configuration file: '~/.config/wikilocalctrl.json'")
	for key in [ "wwwWikiRootDir", "httpBinDir" ]:
		if (key in parsedArgs.optionData) and (parsedArgs.optionData[key] is not None):
			cfg[key] = parsedArgs.optionData[key]
	for key in [ "wwwWikiRootDir", "httpBinDir" ]:
		if not os.path.isdir(cfg[key]):
			raise Exception(key + ": Directory does not exist: " + repr(cfg[key]))

	# process the first command

	try:
		(cmdName, cmdArgs) = parsedArgs.parseNextCommand()
	except Exception as e:
		log.error(str(e))
		sys.exit(1)

	# ----------------------------------------------------------------

	if cmdName is None:
		ap.showHelp()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "help":
		ap.showHelp()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "httpstatus":
		cmd_httpstatus(cfg, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "httpstop":
		startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
		h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

		nginxPIDs = h.getNGINXMasterProcesses()
		if nginxPIDs:
			h.stopNGINX(log.descend("Local NGINX: Stopping ..."))
		else:
			log.notice("Local NGINX: Already stopped")

		phpPIDs = h.getPHPFPMMasterProcesses()
		if phpPIDs:
			h.stopPHPFPM(log.descend("Local PHP-FPM: Stopping ..."))
		else:
			log.notice("Local PHP-FPM: Already stopped")

		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "httpstart":
		startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
		h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

		nginxPIDs = h.getNGINXMasterProcesses()
		if nginxPIDs:
			log.notice("Local NGINX: Already running")
		else:
			h.startNGINX(log.descend("Local NGINX: Starting ..."))
			waitForServiceStarted(h.getNGINXMasterProcesses, "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses()
		if phpPIDs:
			log.notice("Local PHP-FPM: Already running")
		else:
			h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
			waitForServiceStarted(h.getPHPFPMMasterProcesses, "PHP-FPM", log)

		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "httprestart":
		startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
		h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

		nginxPIDs = h.getNGINXMasterProcesses()
		if nginxPIDs:
			h.stopNGINX(log.descend("Local NGINX: Stopping ..."))
		else:
			log.notice("Local NGINX: Not running")

		phpPIDs = h.getPHPFPMMasterProcesses()
		if phpPIDs:
			h.stopPHPFPM(log.descend("Local PHP-FPM: Stopping ..."))
		else:
			log.notice("Local PHP-FPM: Not running")

		phpPIDs = h.getNGINXMasterProcesses()
		waitForServiceStopped(h.getNGINXMasterProcesses, "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses()
		waitForServiceStopped(h.getPHPFPMMasterProcesses, "PHP-FPM", log)

		h.startNGINX(log.descend("Local NGINX: Starting ..."))
		waitForServiceStarted(h.getNGINXMasterProcesses, "NGINX", log)

		h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
		waitForServiceStarted(h.getPHPFPMMasterProcesses, "PHP-FPM", log)

		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "wikistatus":
		cmd_wikistatus(cfg, False, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "wikistop":
		wwwWikiRootDir, wikiNames = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikiNames:
			raise Exception("No such Wiki: \"" + wiki + "\"")

		# ----

		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)
		bIsRunning = h.isCronScriptRunning()

		pidInfos = h.getCronProcesses()
		if pidInfos:
			h.stopCronScript(log.descend(wiki + ": Stopping ..."))
		else:
			log.notice(wiki + ": Already stopped")

	# ----------------------------------------------------------------

	elif cmdName == "wikistart":
		wwwWikiRootDir, wikiNames = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikiNames:
			raise Exception("No such Wiki: \"" + wiki + "\"")

		# ----

		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			log.notice(wiki + ": Already running")
		else:
			h.startCronScript(log.descend(wiki + ": Starting ..."))
			waitForServiceStarted(h.getCronProcesses, wiki, log)

	# ----------------------------------------------------------------

	elif cmdName == "start":
		wwwWikiRootDir, wikiNames = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikiNames:
			raise Exception("No such Wiki: \"" + wiki + "\"")

		startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
		h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

		# ----

		nginxPIDs = h.getNGINXMasterProcesses()
		if nginxPIDs:
			log.notice("Local NGINX: Already running")
		else:
			h.startNGINX(log.descend("Local NGINX: Starting ..."))
			waitForServiceStarted(h.getNGINXMasterProcesses, "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses()
		if phpPIDs:
			log.notice("Local PHP-FPM: Already running")
		else:
			h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
			waitForServiceStarted(h.getPHPFPMMasterProcesses, "PHP-FPM", log)

		# ----

		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			log.notice(wiki + ": Already running")
		else:
			h.startCronScript(log.descend(wiki + ": Starting ..."))
			waitForServiceStarted(h.getCronProcesses, wiki, log)

	# ----------------------------------------------------------------

	elif cmdName == "stop":
		wwwWikiRootDir, wikiNames = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikiNames:
			raise Exception("No such Wiki: \"" + wiki + "\"")

		startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
		h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

		# ----

		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			h.stopCronScript(log.descend(wiki + ": Stopping ..."))
		else:
			log.notice(wiki + ": Already stopped")

		# ----

		allRunningWikis = []
		for wikiToCheck in wikiNames:
			if wikiToCheck != wiki:
				h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)
				pidInfos = h.getCronProcesses()
				if pidInfos:
					allRunningWikis.append(wikiToCheck)

		if not allRunningWikis:
			# no more wikis are running

			log.notice("No more Wikis are running => NGINX and PHP no longer needed")

			h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

			nginxPIDs = h.getNGINXMasterProcesses()
			if nginxPIDs:
				h.stopNGINX(log.descend("Local NGINX: Stopping ..."))
			else:
				log.notice("Local PHP-FPM: Already stopped")

			phpPIDs = h.getPHPFPMMasterProcesses()
			if phpPIDs:
				h.stopPHPFPM(log.descend("Local PHP-FPM: Stopping ..."))
			else:
				log.notice("Local NGINX: Already stopped")

	# ----------------------------------------------------------------

	elif cmdName == "status":
		pids1 = cmd_httpstatus(cfg, log)
		assert isinstance(pids1, list)
		pids2 = wrapped_cmd_wikistatus(cfg, False, log)
		assert isinstance(pids2, list)

		pids = []
		pids.extend(pids1)
		pids.extend(pids2)
		print_mem_used_by_pids(pids)

		cmd_diskfree(cfg, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "statusfull":
		cmd_httpstatus(cfg, log)
		cmd_wikistatus(cfg, True, log)
		cmd_diskfree(cfg, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "df":
		cmd_diskfree(cfg, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "extensionmatrix":
		cmd_extensionmatrix(cfg, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	else:
		raise Exception("Implementation Error!")

except jk_logging.ExceptionInChildContextException as ee:
	pass
except Exception as ee:
	log.error(ee)
	sys.exit(1)




