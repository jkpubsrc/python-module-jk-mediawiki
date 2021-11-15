The following section(s) provide an introduction in the structure of this module.

Classes
--------------------------------------------------------------------

### Informational classes

| Class							| Description															|
| ---							| ---																	|
| `impl.LocalWikiScanner`		| Scans a directory tree for MW installations.							|
| `impl.LocalWikiInstInfo`		| Holds rudimentary information about a detected MW installation.		|

### Classes for process retrieving and filtering

Purpose: A robust interface to identify relevant processes for managing the whole software system.

| Class							| Description																	|
| ---							| ---																			|
| `impl.AbstractProcessFilter`	| Abstract base class for a process generator and all process filters.			|
| `impl.OSProcessProvider`		| Provides data about currently running processes.								|
| `impl.ProcessProviderCache`	| Provides data of an underlying provider, but adds caching of 3 seconds.		|
| `impl.ProcessFilter`			| Enforces constraints by restricting processes passing through this instance.	|
| `impl.WikiCronProcessFilter`	| Top level identification layer for MW cron processes.							|
| `impl.WikiNGINXProcessFilter`	| Top level identification layer for MW NGINX processes.						|
| `impl.WikiPHPProcessFilter`	| Top level identification layer for MW PHP processes.							|











