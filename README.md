# Native2Proton

Native2Proton is a runner for forcing the install and execution of Windows versions of Steam games rather than running the native Linux version.

Requires python3 and wget

README: This script is not required anymore since Valve Implemented a solution directly in Steam. Please see https://github.com/ValveSoftware/steam-for-linux/issues/5638 and https://askubuntu.com/questions/1151873/how-to-run-supported-games-on-steam-with-proton


    In Steam settings in the category "Steam Play" check "Enable Steam Play for all other titles".

    Then right-click on the game in question, open "Properties", and on the bottom of the "General" tab, check "Force the use of a specific Steam Play compatibility tool".

    That will tell Steam to run the game via Proton even if there is a native Linux version available.


# Using Native2Proton

To clone the repo: 

```git clone https://github.com/Holston5/Native2Proton.git && cd Native2Proton```

Run with `./native2proton.py`

The Steam ID for the game you wish to install is required.  It can be found in the url of the steam store page for the game.

Detection of your steam install location should be automatic and Native2Proton also includes a wrapper for running winetricks on the prefixes it creates.

# Running Native2Proton Games

Games installed with Native2Proton are best added to your Steam client as a non-Steam game.
To do this point Steam to the .desktop shortcut created in "~/.local/share/native2proton/launchers" and set the Launch Options for the shortcut to "/home/user/.local/share/native2proton/$steam_app_id/$runner_name.sh

# Known limitations & Issues

Not every game will work due to DRM and anti-cheat methods they might employ.  Some games might also require additional libraries like corefonts or vcruntimes.  These can usually be installed with Native2Proton's builtin winetricks option.  

Native2Proton is a wrapper for Proton and the technologies it uses including DXVK. As such all warnings for those applications apply here.
Some technologies in DXVK have been known to get players banned where the game uses anti-cheat technology.  Use DXVK and Native2Proton at your own risk. 
