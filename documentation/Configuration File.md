The following sections provide information about the configuration file `wikilocalctrl.py` requies. This file is loaded on sart of `wikilocalctrl.py`.

Location of the configuration file
----------------------------------

The configuration file must be stored at the following location:

* `~/.config/wikilocalctrl.json`

Configuration file file format
------------------------------

The location file is a JSON file. Its syntax therefore must be conform to the JSON file format standard. 

By convention content of this file must be a dictionary/object containing of key-value entries. The keys are of type `string`. The values are of type `string`, `integer`, `float` or `boolean`. Values can contain the value `null`. 

Configuration file content
--------------------------

The configuration file contains the following keys:

* `str wwwWikiRootDir`: This entry must contain the path of the root directory of the local wiki installations.
* `str httpBinDir`: This entry must contain the path of the root directory of the web server start script(s).








