# materialx_importer

#### Requirements

- Houdini version 19.5 or higher required

#### HOW TO INSTALL:

Unzip the code inside $HOME/houdini{your_version}/scripts
If scripts folder does not exist, create it

Copy this python code in a new shelf-tool

```bash
import sys, os, importlib

houdini_version = hou.applicationVersion()

if houdini_version < (19, 5, 0):
    hou.ui.displayMessage("At least Houdini 19.5 version is required", severity=hou.severityType.Error)
    sys.exit()

scritps_path = os.path.join(hou.getenv("HOME"), "houdini{}.{}".format(houdini_version[0], houdini_version[1]), "scripts")

if scritps_path not in sys.path:
    sys.path.append(scritps_path)

from materialx_importer import run_ui

run_ui.run()
```

#### License
This project is licensed under the MIT License.