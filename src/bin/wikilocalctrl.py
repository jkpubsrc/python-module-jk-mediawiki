#!/usr/bin/python3

import time
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

ap.createCommand("scan", "Scan all projects.")
ap.createCommand("help", "Display this help text.")
ap.createCommand("httpstart", "Start the HTTP service(s).")
ap.createCommand("httpstop", "Stop the HTTP service(s).")
ap.createCommand("httpstatus", "Status about the HTTP service(s).")
ap.createCommand("wikistatus", "List existing local Wikis and their status.")
ap.createCommand("wikistop", "Stop a Wiki service.").expectString("wikiName", minLength=1)
ap.createCommand("wikistart", "Start a Wiki service.").expectString("wikiName", minLength=1)
ap.createCommand("status", "List full status of HTTP service(s) and local Wikis.")
ap.createCommand("start", "Start relevant service(s) to run a specific wiki.").expectString("wikiName", minLength=1)
ap.createCommand("stop", "Stop relevant service(s) to terminate a specific wiki.").expectString("wikiName", minLength=1)




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
def waitForService(fnGetPIDInfos, name:str, log:jk_logging.AbstractLogger):
	countDown = 20
	while countDown > 0:
		time.sleep(0.5)
		pidInfos = fnGetPIDInfos()
		if pidInfos:
			log.success("Local " + name + ": " + str([ x["pid"] for x in pidInfos ]))
			break
		countDown-= 1
		if countDown == 0:
			raise Exception("Failed to start " + name + "!")
#

#
# Get a list of all existing Wikis (= running and not running).
#
# @return		str wwwWikiRootDir		The root directory for all local wikis
# @return		str[] wikiName			The names of the wikis available.
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
	return cfg["wwwWikiRootDir"], ret
#



def cmd_httpstatus(cfg:dict, log):
	startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
	h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

	t = jk_console.SimpleTable()
	t.addRow("Service", "Status", "Main Process(es)").hlineAfterRow = True
	r = jk_console.Console.RESET

	nginxPIDs = h.getNGINXMasterProcesses()
	c = jk_console.Console.ForeGround.STD_GREEN if nginxPIDs else jk_console.Console.ForeGround.STD_DARKGRAY
	if nginxPIDs:
		t.addRow("Local NGINX", "running", str([ x["pid"] for x in nginxPIDs ])).color = c
	else:
		t.addRow("Local NGINX", "stopped", "-").color = c

	phpPIDs = h.getPHPFPMMasterProcesses()
	c = jk_console.Console.ForeGround.STD_GREEN if phpPIDs else jk_console.Console.ForeGround.STD_DARKGRAY
	if phpPIDs:
		t.addRow("Local PHP-FPM", "running", str([ x["pid"] for x in phpPIDs ])).color = c
	else:
		t.addRow("Local PHP-FPM", "stopped", "-").color = c

	print()
	t.print()
#



def cmd_wikistatus(cfg:dict, log):
	wwwWikiRootDir, wikis = listWikis(cfg)

	t = jk_console.SimpleTable()
	t.addRow("Wiki", "Version", "Status", "Cron Script Processes").hlineAfterRow = True
	r = jk_console.Console.RESET

	for wiki in wikis:
		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)
		bIsRunning = h.isCronScriptRunning()
		c = jk_console.Console.ForeGround.STD_GREEN if bIsRunning else jk_console.Console.ForeGround.STD_DARKGRAY
		t.addRow(
			wiki,
			str(h.getVersion()),
			"running" if bIsRunning else "stopped",
			str([ x["pid"] for x in h.getCronProcesses() ]) if bIsRunning else "-",
			).color = c

	print()
	t.print()
#






log = jk_logging.ConsoleLogger.create(logMsgFormatter=jk_logging.COLOR_LOG_MESSAGE_FORMATTER)








#MediaWikiLocalUserServiceMgr
try:
	parsedArgs = ap.parse()

	if parsedArgs.optionData["bShowVersion"]:
		print(__version__)
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
		cfg = {}
	for key in [ "wwwWikiRootDir", "httpBinDir"]:
		if (key in parsedArgs.optionData) and (parsedArgs.optionData[key] is not None):
			cfg[key] = parsedArgs.optionData[key]

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
			log.notice("Local PHP-FPM: Already stopped")

		phpPIDs = h.getPHPFPMMasterProcesses()
		if phpPIDs:
			h.stopPHPFPM(log.descend("Local PHP-FPM: Stopping ..."))
		else:
			log.notice("Local NGINX: Already stopped")

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
			waitForService(h.getNGINXMasterProcesses, "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses()
		if phpPIDs:
			log.notice("Local PHP-FPM: Already running")
		else:
			h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
			waitForService(h.getPHPFPMMasterProcesses, "PHP-FPM", log)

		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "wikistatus":
		cmd_wikistatus(cfg, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	elif cmdName == "wikistop":
		wwwWikiRootDir, wikis = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikis:
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
		wwwWikiRootDir, wikis = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikis:
			raise Exception("No such Wiki: \"" + wiki + "\"")

		# ----

		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			log.notice(wiki + ": Already running")
		else:
			h.startCronScript(log.descend(wiki + ": Starting ..."))
			waitForService(h.getCronProcesses, wiki, log)

	# ----------------------------------------------------------------

	elif cmdName == "start":
		wwwWikiRootDir, wikis = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikis:
			raise Exception("No such Wiki: \"" + wiki + "\"")

		startNGINXScriptPath, startPHPFPMScriptPath = getHttpdCfg(cfg)
		h = jk_mediawiki.MediaWikiLocalUserServiceMgr(startNGINXScriptPath, startPHPFPMScriptPath, userName)

		# ----

		nginxPIDs = h.getNGINXMasterProcesses()
		if nginxPIDs:
			log.notice("Local NGINX: Already running")
		else:
			h.startNGINX(log.descend("Local NGINX: Starting ..."))
			waitForService(h.getNGINXMasterProcesses, "NGINX", log)

		phpPIDs = h.getPHPFPMMasterProcesses()
		if phpPIDs:
			log.notice("Local PHP-FPM: Already running")
		else:
			h.startPHPFPM(log.descend("Local PHP-FPM: Starting ..."))
			waitForService(h.getPHPFPMMasterProcesses, "PHP-FPM", log)

		# ----

		h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)

		pidInfos = h.getCronProcesses()
		if pidInfos:
			log.notice(wiki + ": Already running")
		else:
			h.startCronScript(log.descend(wiki + ": Starting ..."))
			waitForService(h.getCronProcesses, wiki, log)

	# ----------------------------------------------------------------

	elif cmdName == "stop":
		wwwWikiRootDir, wikis = listWikis(cfg)
		wiki = cmdArgs[0]
		if wiki not in wikis:
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
		for wikiToCheck in wikis:
			if wikiToCheck != wiki:
				h = jk_mediawiki.MediaWikiLocalUserInstallationMgr(os.path.join(wwwWikiRootDir, wiki), userName)
				pidInfos = h.getCronProcesses()
				if pidInfos:
					allRunningWikis.append(wikiToCheck)

		if not allRunningWikis:
			# no more wikis are running

			log.notice("No more Wikis are running => NGINX and PHP no longer needed")

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
		cmd_httpstatus(cfg, log)
		cmd_wikistatus(cfg, log)
		print()
		sys.exit(0)

	# ----------------------------------------------------------------

	else:
		raise Exception("Implementation Error!")

except Exception as e:
	log.error(e)
	sys.exit(1)




