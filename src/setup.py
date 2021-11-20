################################################################################
################################################################################
###
###  This file is automatically generated. Do not change this file! Changes
###  will get overwritten! Change the source file for "setup.py" instead.
###  This is either 'packageinfo.json' or 'packageinfo.jsonc'
###
################################################################################
################################################################################


from setuptools import setup

def readme():
	with open("README.md", "r", encoding="UTF-8-sig") as f:
		return f.read()

setup(
	author = "Jürgen Knauth",
	author_email = "pubsrc@binary-overflow.de",
	classifiers = [
		"Development Status :: 4 - Beta",
		"License :: OSI Approved :: Apache Software License",
		"Programming Language :: Python :: 3",
	],
	description = "This module provides functions, classes and binaries to assist in working with MediaWiki installations.",
	include_package_data = False,
	install_requires = [
		"jk_utils",
		"jk_console",
		"jk_argparsing",
		"jk_json",
		"jk_version",
		"jk_typing",
		"jk_logging",
		"jk_sysinfo",
		"jk_mounting",
		"jk_prettyprintobj",
	],
	keywords = [
		"mediawiki",
		"mw",
		"php",
	],
	license = "Apache2",
	name = "jk_mediawiki",
	packages = [
		"jk_mediawiki",
		"jk_mediawiki.impl",
		"jk_mediawiki.lsfile",
	],
	scripts = [
		"bin/wikilocalctrl.py",
	],
	version = "0.2021.11.20",
	zip_safe = False,
	long_description = readme(),
	long_description_content_type="text/markdown",
)
