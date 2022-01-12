#!/usr/bin/python3.8

import time
import datetime
import os
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

from jk_mediawiki.MWManagementCtx import MWManagementCtx
from jk_mediawiki.impl.AbstractProcessFilter import AbstractProcessFilter






# initialize argument parser

ap = jk_argparsing.ArgsParser(
	"wikilocalctrl [options] <command>",
	"Manage local Wiki installations.")
ap.createAuthor("Jürgen Knauth", "jk@binary-overflow.de")
ap.setLicense("apache")

# set defaults

ap.optionDataDefaults.set("bShowHelp", False)
ap.optionDataDefaults.set("bVerbose", False)
ap.optionDataDefaults.set("bShowVersion", False)
ap.optionDataDefaults.set("wwwWikiRootDir", None)
ap.optionDataDefaults.set("httpBinDir", None)

# arguments

ap.createOption('h', 'help', "Display this help text and then exit.").onOption = \
	lambda argOption, argOptionArguments, parsedArgs: parsedArgs.optionData.set("bShowHelp", True)
ap.createOption(None, 'version', "Display the version of this software and then exit.").onOption = \
	lambda argOption, argOptionArguments, parsedArgs: parsedArgs.optionData.set("bShowVersion", True)
ap.createOption(None, 'verbose', "Specify this option for more log output (for debugging purposes).").onOption = \
	lambda argOption, argOptionArguments, parsedArgs: parsedArgs.optionData.set("bVerbose", True)
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
ap.createCommand("wikistatus", "List existing local Wikis and their status.").expectString("wikiName", minLength=1)
ap.createCommand("wikistop", "Stop a Wiki service.").expectString("wikiName", minLength=1)
ap.createCommand("wikistart", "Start a Wiki service.").expectString("wikiName", minLength=1)
ap.createCommand("status", "List status of HTTP service(s) and local Wikis.")
ap.createCommand("statusfull", "List full status of HTTP service(s) and local Wikis.")
ap.createCommand("start", "Start relevant service(s) to run a specific wiki.").expectString("wikiName", minLength=1)
ap.createCommand("stop", "Stop relevant service(s) to terminate a specific wiki.").expectString("wikiName", minLength=1)
ap.createCommand("extensionmatrix", "Display a matrix about all wiki extensions.")
ap.createCommand("list", "Display a list of installed wikis.")




#
# @param	dict cfg			The content of the user specific configuration file "~/.config/wikilocalctrl.json"
#
@jk_typing.checkFunctionSignature()
def getHttpdCfg(cfg:dict) -> tuple:
	if cfg["httpBinDir"] is None:
		raise Exception("Missing configuration key: 'httpBinDir'")
	if cfg["wikiEtcDir"] is None:
		raise Exception("Missing configuration key: 'wikiEtcDir'")

	startNGINXScriptPath = os.path.join(cfg["httpBinDir"], "start-nginx-bg.sh")
	if not os.path.isfile(startNGINXScriptPath):
		raise Exception("Missing script: \"start-nginx-bg.sh\"")
	startPHPFPMScriptPath = os.path.join(cfg["httpBinDir"], "start-php-fpm-bg.sh")
	if not os.path.isfile(startPHPFPMScriptPath):
		raise Exception("Missing script: \"start-php-fpm-bg.sh\"")
	if not os.path.isdir(cfg["wikiEtcDir"]):
		raise Exception("Invalid directory specified for 'wikiEtcDir': {}".format(cfg["wikiEtcDir"]))

	return startNGINXScriptPath, startPHPFPMScriptPath, cfg["wikiEtcDir"]
#

@jk_typing.checkFunctionSignature()
def instantiateLocalUserServiceMgr(ctx:MWManagementCtx, cfg:dict, bVerbose:bool) -> jk_mediawiki.MediaWikiLocalUserServiceMgr:
	startNGINXScriptPath, startPHPFPMScriptPath, wikiEtcDirPath = getHttpdCfg(cfg)
	return jk_mediawiki.MediaWikiLocalUserServiceMgr(ctx, startNGINXScriptPath, startPHPFPMScriptPath, wikiEtcDirPath, bVerbose)
#

@jk_typing.checkFunctionSignature()
def waitForServiceStarted(fnGetPIDInfos:jk_mediawiki.impl.AbstractProcessFilter, name:str, log:jk_logging.AbstractLogger):
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
def waitForServiceStopped(fnGetPIDInfos:jk_mediawiki.impl.AbstractProcessFilter, name:str, log:jk_logging.AbstractLogger):
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
# @param		dict cfg			The content of the user specific configuration file "~/.config/wikilocalctrl.json"
#
@jk_typing.checkFunctionSignature()
def cmd_httpstatus(ctx:jk_mediawiki.MWManagementCtx, cfg:dict, log, bVerbose:bool) -> list:
	pids = []

	h = instantiateLocalUserServiceMgr(ctx, cfg, bVerbose)

	t = jk_console.SimpleTable()
	t.addRow("Service", "Status", "Main Process(es)").hlineAfterRow = True
	r = jk_console.Console.RESET

	nginxPIDs = h.getNGINXMasterProcesses(log)
	c = jk_console.Console.ForeGround.STD_GREEN if nginxPIDs else jk_console.Console.ForeGround.STD_DARKGRAY
	if nginxPIDs:
		pids.extend([ x["pid"] for x in nginxPIDs ])
		t.addRow("Local NGINX", "running", str([ x["pid"] for x in nginxPIDs ])).color = c
	else:
		t.addRow("Local NGINX", "stopped", "-").color = c

	phpPIDs = h.getPHPFPMMasterProcesses(log)
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








with jk_logging.wrapMain() as log:

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

	bVerbose = parsedArgs.optionData["bVerbose"]
	if bVerbose:
		log.notice("Verbose output mode: enabled")

	# load configuration: merge it with specified arguments

	ctx = jk_mediawiki.MWManagementCtx()
	if bVerbose:
		log.notice("Loading: " + ctx.cfgFilePath)
	if os.path.isfile(ctx.cfgFilePath):
		cfg = jk_json.loadFromFile(ctx.cfgFilePath)
	else:
		raise Exception("No configuration file: '~/.config/wikilocalctrl.json'")
	if bVerbose:
		log.notice("Verifying configuration ...")
	for key in [ "wwwWikiRootDir", "httpBinDir" ]:
		if (key in parsedArgs.optionData) and (parsedArgs.optionData[key] is not None):
			cfg[key] = parsedArgs.optionData[key]
	for key in [ "wwwWikiRootDir", "httpBinDir" ]:
		if not os.path.isdir(cfg[key]):
			raise Exception(key + ": Directory does not exist: " + repr(cfg[key]))

	localMediaWikisMgr = jk_mediawiki.LocalMediaWikisMgr(ctx, cfg["wwwWikiRootDir"], bVerbose)

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
		cmd_httpstatus(ctx, cfg, log, bVerbose)
		print()
		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "httpstop":
		h = instantiateLocalUserServiceMgr(ctx, cfg, bVerbose)

		nginxPIDs = h.getNGINXMasterProcesses(log)
		if nginxPIDs:
			h.stopNGINX(log.descend("Local NGINX: Stopping ..."))
		else:
			log.notice("Local NGINX: Already stopped")

		phpPIDs = h.getPHPFPMMasterProcesses(log)
		if phpPIDs:
			h.stopPHPFPM(log.descend("Local PHP-FPM: Stopping ..."))
		else:
			log.notice("Local PHP-FPM: Already stopped")

		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "httpstart":
		h = instantiateLocalUserServiceMgr(ctx, cfg, bVerbose)

		nginxPIDs = h.getNGINXMasterProcesses(log)
		if nginxPIDs:
			log.notice("Local NGINX: Already running")
		else:
			h.startNGINX(log.descend("Local NGINX: Starting ..."))
			waitForServiceStarted(h.getNGINXMasterProcessesProvider(), "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses(log)
		if phpPIDs:
			log.notice("Local PHP-FPM: Already running")
		else:
			h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
			waitForServiceStarted(h.getPHPFPMMasterProcessesProvider(), "PHP-FPM", log)

		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "httprestart":
		h = instantiateLocalUserServiceMgr(ctx, cfg, bVerbose)

		nginxPIDs = h.getNGINXMasterProcesses(log)
		if nginxPIDs:
			h.stopNGINX(log.descend("Local NGINX: Stopping ..."))
		else:
			log.notice("Local NGINX: Not running")

		phpPIDs = h.getPHPFPMMasterProcesses(log)
		if phpPIDs:
			h.stopPHPFPM(log.descend("Local PHP-FPM: Stopping ..."))
		else:
			log.notice("Local PHP-FPM: Not running")

		phpPIDs = h.getNGINXMasterProcesses(log)
		waitForServiceStopped(h.getNGINXMasterProcessesProvider(), "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses(log)
		waitForServiceStopped(h.getPHPFPMMasterProcessesProvider(), "PHP-FPM", log)

		h.startNGINX(log.descend("Local NGINX: Starting ..."))
		waitForServiceStarted(h.getNGINXMasterProcessesProvider(), "NGINX", log)

		h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
		waitForServiceStarted(h.getPHPFPMMasterProcessesProvider(), "PHP-FPM", log)

		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "wikistatus":
		wikiNames = localMediaWikisMgr.listWikis()
		wikiName = cmdArgs[0]
		if wikiName not in wikiNames:
			raise Exception("No such Wiki: \"" + wikiName + "\"")

		# ----

		r = localMediaWikisMgr.getStatusOverviewOne(wikiName, False, bVerbose, log)
	
		print()
		r.table.print()
		print()

		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "list":
		r = localMediaWikisMgr.getStatusOverviewAll(False, bVerbose, log)
	
		print()
		r.table.print()
		print()

		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "wikistop":
		wikiNames = localMediaWikisMgr.listWikis()
		wikiName = cmdArgs[0]
		if wikiName not in wikiNames:
			raise Exception("No such Wiki: \"" + wikiName + "\"")

		# ----

		_wikiInstDirPath = localMediaWikisMgr.getWikiInstDirPath(wikiName)
		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(ctx, _wikiInstDirPath, log)
		bIsRunning = h.isCronScriptRunning()

		pidInfos = h.getCronProcesses()
		if pidInfos:
			h.stopCronScript(log.descend(wikiName + ": Stopping ..."))
		else:
			log.notice(wikiName + ": Already stopped")

	# ----------------------------------------------------------------

	elif cmdName == "wikistart":
		wikiNames = localMediaWikisMgr.listWikis()
		wikiName = cmdArgs[0]
		if wikiName not in wikiNames:
			raise Exception("No such Wiki: \"" + wikiName + "\"")

		# ----

		_wikiInstDirPath = localMediaWikisMgr.getWikiInstDirPath(wikiName)
		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(ctx, _wikiInstDirPath, log)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			log.notice(wikiName + ": Already running")
		else:
			h.startCronScript(log.descend(wikiName + ": Starting ..."))
			waitForServiceStarted(h.getCronProcessesProvider(), wikiName, log)

	# ----------------------------------------------------------------

	elif cmdName == "start":
		wikiNames = localMediaWikisMgr.listWikis()
		wikiName = cmdArgs[0]
		if wikiName not in wikiNames:
			raise Exception("No such Wiki: \"" + wikiName + "\"")

		h = instantiateLocalUserServiceMgr(ctx, cfg, bVerbose)

		# ----

		nginxPIDs = h.getNGINXMasterProcesses(log)
		if nginxPIDs:
			log.notice("Local NGINX: Already running")
		else:
			h.startNGINX(log.descend("Local NGINX: Starting ..."))
			waitForServiceStarted(h.getNGINXMasterProcessesProvider(), "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses(log)
		if phpPIDs:
			log.notice("Local PHP-FPM: Already running")
		else:
			h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
			waitForServiceStarted(h.getPHPFPMMasterProcessesProvider(), "PHP-FPM", log)

		# ----

		_wikiInstDirPath = localMediaWikisMgr.getWikiInstDirPath(wikiName)
		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(ctx, _wikiInstDirPath, log)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			log.notice(wikiName + ": Already running")
		else:
			h.startCronScript(log.descend(wikiName + ": Starting ..."))
			waitForServiceStarted(h.getCronProcessesProvider(), wikiName, log)

	# ----------------------------------------------------------------

	elif cmdName == "stop":
		wikiNames = localMediaWikisMgr.listWikis()
		wikiName = cmdArgs[0]
		if wikiName not in wikiNames:
			raise Exception("No such Wiki: \"" + wikiName + "\"")

		h = instantiateLocalUserServiceMgr(ctx, cfg, bVerbose)

		# ----

		_wikiInstDirPath = localMediaWikisMgr.getWikiInstDirPath(wikiName)
		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(ctx, _wikiInstDirPath, log)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			h.stopCronScript(log.descend(wikiName + ": Stopping ..."))
		else:
			log.notice(wikiName + ": Already stopped")

		# ----

		allRunningWikis = []
		for wikiToCheck in wikiNames:
			if wikiToCheck != wikiName:
				_wikiInstDirPath = localMediaWikisMgr.getWikiInstDirPath(wikiName)
				h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(ctx, _wikiInstDirPath, log)
				pidInfos = h.getCronProcesses()
				if pidInfos:
					allRunningWikis.append(wikiToCheck)

		if not allRunningWikis:
			# no more wikis are running

			log.notice("No more Wikis are running => NGINX and PHP no longer needed")

			h = instantiateLocalUserServiceMgr(ctx, cfg, bVerbose)

			nginxPIDs = h.getNGINXMasterProcesses(log)
			if nginxPIDs:
				h.stopNGINX(log.descend("Local NGINX: Stopping ..."))
			else:
				log.notice("Local PHP-FPM: Already stopped")

			phpPIDs = h.getPHPFPMMasterProcesses(log)
			if phpPIDs:
				h.stopPHPFPM(log.descend("Local PHP-FPM: Stopping ..."))
			else:
				log.notice("Local NGINX: Already stopped")

	# ----------------------------------------------------------------

	elif cmdName == "status":
		pids1 = cmd_httpstatus(ctx, cfg, log, bVerbose)
		assert isinstance(pids1, list)

		r = localMediaWikisMgr.getStatusOverviewAll(False, bVerbose, log)
	
		print()
		r.table.print()
		print()

		pids = []
		pids.extend(pids1)
		pids.extend(r.pids)
		print_mem_used_by_pids(pids)

		cmd_diskfree(cfg, log)
		print()
		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "statusfull":
		cmd_httpstatus(ctx, cfg, log, bVerbose)

		r = localMediaWikisMgr.getStatusOverviewAll(True, bVerbose, log)

		print()
		r.table.print()
		print()

		cmd_diskfree(cfg, log)
		print()
		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "df":
		cmd_diskfree(cfg, log)
		print()
		#sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "extensionmatrix":
		table = localMediaWikisMgr.getExtensionMatrix(log)

		print()
		table.print()
		print()

		#sys.exit(0)

	# ----------------------------------------------------------------

	else:
		raise Exception("Implementation Error!")





