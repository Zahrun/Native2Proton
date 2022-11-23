#!/usr/bin/env python3
import os, sys, re, configparser, subprocess, time, shutil
from requests import get


def n2p_config(home, base_dir, config):
    #setting up environment
    print("Setting up...")
    global proton_dir
    global n2p_library
    global steam_dir
    steam_library = None

    
    #Locate steam install by finding library file
    if os.path.isfile(home+"/.local/share/Steam/steamapps/libraryfolders.vdf"):
        steam_library = str(home+"/.local/share/Steam/steamapps/libraryfolders.vdf")
        steamapps_dir = str(home+"/.local/share/Steam/steamapps")
        steam_dir = str(home+"/.local/share/Steam")
        print("Found libraryfolders.vdf")
    elif  os.path.isfile(home+"/.steam/steam/steamapps/libraryfolders.vdf"):
        steam_library = str(home+"/.steam/steam/steamapps/libraryfolders.vdf")
        steamapps_dir = str(home+"/.steam/steam/steamapps")
        steam_dir = str(home+"/.steam")
        print("Found libraryfolders.vdf")
    if steam_library != None:
        
        libraries=[]
        
        for line in open(steam_library,'r'):
            stripline = line.lstrip()
            if "path" in stripline:
                if os.path.isdir(re.findall(r'"([^"]*)"', line)[1]+"/steamapps/common"):
                    libraries.append(re.findall(r'"([^"]*)"', line)[1]+"/steamapps/common")
        if not libraries:
            #user has no stored libraries, use default location
            libraries.append(steamapps_dir+"/common")
        #Search each library location looking for a Proton install
        for library in libraries:

            for findproton in (os.listdir(library)):
                if str(findproton).startswith("Proton "):
                    if (os.path.isfile(library+"/"+findproton+"/user_settings.py")) or (os.path.isfile(library+"/"+findproton+"/user_settings.sample.py")):
                        proton_dir = str(library+"/"+findproton)
                        print(proton_dir)
    while proton_dir is None:
        proton_dir = input("Couldn't find Proton, please enter full path to Proton (eg: Steam_Library/steamapps/common/Proton 3.7):  ")
        if not (os.path.isfile(proton_dir+"/user_settings.py") or os.path.isfile(proton_dir+"/user_settings.sample.py")):
            print("Proton not found in given directory, please try again")
            proton_dir = None
    print("Proton located: "+proton_dir)

    
    #Pick default n2p library
    
    n2p_library = str(os.path.abspath(proton_dir+"../../../../../native2proton"))
    if n2p_library == str(home+"/.steam/native2proton"): #N2P library can't be inside .steam dir or steam llibrary otherwise steam overwrites windows game files with native 
        n2p_library = str(home+"/games/native2proton") 

    change_n2p_library = input("Default directory for native2proton game data: "+n2p_library+"   Change? (y/n)  ")
    if change_n2p_library == 'y':
        n2p_library = input("Please enter new data directory, do not use your steam library:  ")
        print("New native2proton library: " + n2p_library)
    

    #make directories
    os.makedirs(n2p_library, 0o755, exist_ok=True)

    if not os.path.isdir(base_dir):
        os.makedirs(base_dir+"/.steamcmd", 0o755)
        os.makedirs(base_dir+"/resources", 0o755)
        os.system('wget "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" && tar -xf steamcmd_linux.tar.gz -C '+base_dir+'/.steamcmd')
    if not os.path.isdir(base_dir+"/.steamcmd"):
        os.mkdir(base_dir+"/.steamcmd", 0o755)
        os.system('wget "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" && tar -xf steamcmd_linux.tar.gz -C '+base_dir+'/.steamcmd')
    if not os.path.isfile(base_dir+"/.winetricks/winetricks"):
        os.system('wget -P '+base_dir+'/.winetricks/ "https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks"')
        os.chmod(base_dir+'/.winetricks/winetricks', 0o775)
    winetricks_dir = base_dir+'/.winetricks'
    
    #Copy resources
    if not os.path.isdir(base_dir+"/resources"):
        os.makedirs(base_dir+"/resources", 0o755)
            
    shutil.copy(os.path.dirname(os.path.abspath(__file__))+"/resources/desktop_template.txt", base_dir+"/resources/desktop_template.txt")
    shutil.copy(os.path.dirname(os.path.abspath(__file__))+"/resources/runner_template.txt", base_dir+"/resources/runner_template.txt")    
    shutil.copy(os.path.dirname(os.path.abspath(__file__))+"/resources/n2p.png", base_dir+"/resources/n2p.png")
    
    #write config
    print("Writing config")
    config['DEFAULTS'] = {'proton_dir': proton_dir, 'n2p_library': n2p_library, 'steam_dir': steam_dir}
    with open(base_dir+"/settings.conf", 'w') as config_file:
        config.write(config_file)
    config_file.close()
    return steam_dir, proton_dir, n2p_library, winetricks_dir


def full_file(src, dst):
    if os.path.islink(src):
        os.symlink(os.path.realpath(src), dst)
    else:
        shutil.copy(src,dst)


def copy_prefix(src, dst):
    for src_dir, dirs, files in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for dir_ in dirs:
            src_file = os.path.join(src_dir, dir_)
            dst_file = os.path.join(dst_dir, dir_)
            if os.path.islink(src_file) and not os.path.exists(dst_file):
                full_file(src_file, dst_file)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if not os.path.exists(dst_file):
                full_file(src_file, dst_file)


def get_user_prefixes(base_dir):
    prefixes = []
    all_paths = os.listdir(base_dir) 
    for path in all_paths:
        if path.startswith("UP"):
            prefixes.append(path)
    if prefixes == None:
        prefixes[0] = 0
    num_prefixes = len(prefixes)+1
    app_id = "UP"+(str(num_prefixes).zfill(4))
    print("New prefix: ")
    return app_id


def install_game(base_dir, n2p_library, proton_dir, steam_dir, app_type):

    if app_type == "steam":
        while True:
            app = input("Please enter the Steam app ID or the game name (eg: Arma 3): ")
            app_dictionary = get('http://api.steampowered.com/ISteamApps/GetAppList/v0001/').json()

            # get app information from steam api
            conflict_aware = False
            for i in app_dictionary['applist']['apps']['app']:
                if (i['name'] == app or i['appid'].__str__() == app) and not conflict_aware:
                    app_name = i['name']
                    app_id = i['appid'].__str__()
                    conflict_aware = True

                # in case the game name has been saved as an app id (e.g. contains only numbers)
                elif (i['name'] == app or i['appid'].__str__() == app) and conflict_aware:
                    print("Encountered conflict:")
                    print("[1] " + app_name + " (ID: " + app_id + ")")
                    print("[2] " + i['name'] + " (ID: " + i['appid'] + ")")
                    if input("Choose the correct game you wish to install: ") == "2":
                        app_name = i['name']
                        app_id = i['appid'].__str__()
                    else:
                        break

            print("Got: " + app_name + " (ID: " + app_id + ")")
            if input("Is that correct? (y/n)") == "y":
                break

        # download game data
        steam_cmd(base_dir, n2p_library, app_name, app_id)
        exe_list = []
        list_id = 0
        for dirpath, dirnames, filenames in os.walk(n2p_library+"/"+app_name):
            for filename in [f for f in filenames if f.endswith(".exe")]:
                print("[" + str(list_id) + "] " + os.path.join(dirpath, filename))
                exe_list.append(os.path.join(dirpath, filename))
                list_id = list_id + 1
        exe_num = input("Please select the game executable by number: ")
        exe = exe_list[int(exe_num)]

        # Create symlink in .local/share/native2proton/app_id to data
        if  not os.path.isdir(base_dir+"/"+app_id):
            os.makedirs(base_dir+"/"+app_id, 0o755)
        prefix_dir = base_dir+"/"+app_id+"/pfx"
        if not os.path.isdir(base_dir+"/"+app_id+"/data"):
            os.symlink(n2p_library+"/"+app_name, base_dir+"/"+app_id+"/data")

        while True:
            prefix_arch = input("Do you want to create a 64bit [1] or 32bit [2] Wine Prefix for this game? ")
            if prefix_arch == "1":
                create_prefix(base_dir, app_id, proton_dir, prefix_dir)
                dst = prefix_dir + "/drive_c/Program Files (x86)/Steam"
                break
            elif prefix_arch == "2":
                create_32bit_prefix(base_dir, app_id, proton_dir, prefix_dir)
                dst = prefix_dir + "/drive_c/Program Files/Steam"
                break

        print("Copying Steam dll's")
        os.makedirs(dst, exist_ok=True)
        copy_dlls = ["steamclient.dll", "steamclient64.dll", "Steam.dll"]
        print("Steam DIR:"+steam_dir )
        for dll in copy_dlls:
            print(steam_dir + "/legacycompat/"+dll)
            try:
                if os.path.isfile(dst+"/"+dll):
                    os.remove(dst+"/"+dll)
                    print("removed file")
                print(os.path.abspath(steam_dir + "/legacycompat/") +dll)
                shutil.copy(os.path.abspath(steam_dir + "/legacycompat/" +dll), dst+"/"+dll)
                print("copied " +dll+"to "+dst+"/"+dll)
            except:
                pass

    else:
        if input("Do you need to create a new prefix? (y/n)") == "y":
            app_id = get_user_prefixes(base_dir)
            prefix_dir = base_dir+"/"+app_id+"/pfx"

            while True:
                prefix_arch = input("Do you want to create a 64bit [1] or 32bit [2] Wine Prefix for this game? ")
                if prefix_arch == "1":
                    create_prefix(base_dir, app_id, proton_dir, prefix_dir)
                    break
                elif prefix_arch == "2":
                    create_32bit_prefix(base_dir, app_id, proton_dir, prefix_dir)
                    break

        else:
            prefixes = []
            all_paths = os.listdir(base_dir) 
            for path in all_paths:
                if path.startswith("UP"):
                    prefixes.append(path)
            for index, prefix in enumerate(prefixes):
                print("["+str(index)+"] "+prefix)
            print("[m] Enter prefix directory manually")
      
            prefix_choice = input("Select prefix: ")
            if prefix_choice == "m":
                prefix_dir = input("Enter prefix directory in full (eg /home/user/prefix2): ")
            else:
                prefix_dir = base_dir+"/"+prefixes[int(prefix_choice)]+"/pfx"
                app_id = base_dir+"/"+prefixes[int(prefix_choice)]
    print("Prefix: "+prefix_dir)
    time.sleep(2)
    
    winetricks = base_dir+'/.winetricks/winetricks' 

    dll_overrides = None
    ext="/dist"
    if not os.path.isdir(proton_dir+"/dist"):
        ext="/files"
    if app_type == "nonsteam":
        
        dll_overrides = input("Assuming you first need to run an installer or similar: Do you wish to set any DLL overrides now? (y/n)")
        if dll_overrides == "y":
            override_string = input("Please enter your override string (eg: xaudio2_7=n,b;dxgi=n;nvapi,nvapi64=disabled): ")
            os.environ["WINEDLLOVERRIDES"]='"'+override_string+'"'
        
        tricks = input("Do you need to install additional winetricks?")
        if tricks == "y":
            print("Your current prefix is: "+app_id)
            use_winetricks(base_dir)
        installer = None
        while installer == None:
            installer = input("Please enter full path to installer/.exe (eg /home/user/my files/Setup.exe):")
            if not os.path.isfile(installer):
                print("File does not exist, check it was entered correctly")
                installer = None
        #installer = '"'+installer+'"'
        wine = proton_dir+ext+"/bin/wineserver"
        os.environ["WINEDLLPATH"] = proton_dir+ext+"/lib64/wine:"+proton_dir+ext+"/lib/wine"
        os.environ["PATH"] = proton_dir+ext+"/bin/:"+proton_dir+ext+"/lib/:"+proton_dir+ext+"/lib64/:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/snap/bin"
        os.environ["WINEPREFIX"]=prefix_dir
        os.environ["LD_LIBRARY_PATH"]=proton_dir+ext+"/lib64:"+proton_dir+ext+"/lib:"+steam_dir+"/ubuntu12_32:"+steam_dir+"/ubuntu12_32/panorama:"
        p = subprocess.call([wine, installer, "-w"])
        exe = None
        while exe == None:
            exe = input("Please enter main executable for runner (eg: /home/user/.local/share/native2proton/UP0001/pfx/drive_c/Program Files(x86)/Origin/Origin.exe)") 
            if not os.path.isfile(exe):
                print("File does not exist, check it was entered correctly")
                executable = None
        
        app_name = input("Please enter a name for this launcher (eg Origin): ")
        dll_overrides = input("Please enter the dll override string for this app (eg: xaudio2_7=n,b;dxgi=n;d3d11=n;nvapi,nvapi64=disabled): ")
        
        
        
    if os.path.isfile(base_dir + "/" + app_id + "/" + app_name + ".sh") == True:
        print("Runner exists. Removing old version...")
        os.remove(base_dir + "/" + app_id + "/" + app_name + ".sh")
    runner_data = open(base_dir+"/resources/runner_template.txt", 'r').read()
    default_overrides = "xaudio2_7=n,b;dxgi=n;d3d11=n"
    if dll_overrides == None:
        format_data = runner_data.format(exe, proton_dir, steam_dir, prefix_dir, app_id, default_overrides, ext)
    else:
        format_data = runner_data.format(exe, proton_dir, steam_dir, prefix_dir, app_id, dll_overrides, ext)
    filename = base_dir + "/" + app_id + "/" + app_name + ".sh"

    with open(filename, 'w') as runner:
        runner.write(format_data)
    runner.close()


    os.chmod(filename, 0o775)
    print("Runner created: "+base_dir + "/" + app_id + "/" + app_name + ".sh")

   



    print("Creating launcher shortcut")
    shortcut_data = open(base_dir+"/resources/desktop_template.txt", 'r').read()
    shortcut_format = shortcut_data.format(filename, base_dir, app_name)
    if not os.path.isdir(base_dir+"/launchers"):
        os.mkdir(base_dir+"/launchers")
    f = open(base_dir+"/launchers/"+app_name.replace(':','')+" N2P.desktop", 'w')
    f.write(shortcut_format)
    f.close()
    if app_type == "steam":
        print("#########################################")
        print("Launchers for Steam games must be added to Steam as a non-Steam game. Please add '"+base_dir+"/launchers/"+app_name+" N2P.desktop' as a non-Steam game")
        print("Then right click > Properties the new N2P game in your steam library and add this (including the quotes) to the launch options:")
        print('"'+filename+'"')
        print("#########################################")
        input("Press enter to add a non-Steam game")
        if os.path.isfile("/usr/games/steam"):
            subprocess.call(["/usr/games/steam", "steam://AddNonSteamGame"])
        else:
            subprocess.call(["steam", "steam://AddNonSteamGame"])
    else:
        if input("Would you like to add this as a Steam shortcut? (y/n)") == "y":
            print("You can find your new shortcut in: '"+filename+"'")
            print('Set your launch options to: '+'"'+filename+'" (including the quotes)')
            input("Press enter to add a steam shortcut")  
            subprocess.call(["steam", "steam://AddNonSteamGame"])
        if input("Would you like to run "+filename+" now? (y/n): ") == "y":
            subprocess.call(["/bin/bash", filename])
    print("App/Game has been installed")
    return


def create_prefix(base_dir, app_id, proton_dir, prefix_dir):
    # Create the prefix.  Copy default from Proton
    if not os.path.isdir(base_dir+"/"+app_id+"/pfx"):
        os.makedirs(base_dir+"/"+app_id+"/pfx", 0o755)
    print("Creating Wine Prefix...")
    ext="/dist"
    if not os.path.isdir(proton_dir+"/dist"):
        ext="/files"
    copy_prefix(proton_dir + ext + "/share/default_pfx", prefix_dir)
    print("Proton: "+proton_dir)
    
    os.environ["WINEDLLPATH"] = proton_dir+ext + "/lib64/wine:"+proton_dir+ext + "/lib/wine"
    os.environ["PATH"] = proton_dir+ext + "/bin/:"+proton_dir+ext + "/lib/:"+proton_dir+ext + "/lib64/:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/snap/bin"
    os.environ["WINEPREFIX"] = prefix_dir
    os.environ["LD_LIBRARY_PATH"] = proton_dir+ext + "/lib64:"+proton_dir+ext + "/lib:"+steam_dir+"/ubuntu12_32:"+steam_dir+"/ubuntu12_32/panorama:"
    wine = proton_dir+ext + "/bin/wineserver"
    #boot prefix by calling Proton's wineserver wineboot
    p = subprocess.call([wine, "-w", "wineboot"])
    i=5
    for c in range(i):
        print("Finishing... ("+str(i)+")")
        i = i-1
        time.sleep(1)
    #above loop is workaround to ensure process returns safely.  For some reason wineserver does not always call/return wineboot properly.
    
  
    print("Installing dxvk...")
    
    dxvk_dst = prefix_dir+"/drive_c/windows/system32"
    dxvk_dst_32 = prefix_dir+"/drive_c/windows/syswow64"
    if  os.path.isfile(dxvk_dst+"/d3d11.dll"):
        os.remove(dxvk_dst+"/d3d11.dll")
    if os.path.isfile(dxvk_dst+"/dxgi.dll"):
        os.remove(dxvk_dst+"/dxgi.dll") 
    if  os.path.isfile(dxvk_dst_32+"/d3d11.dll"):
        os.remove(dxvk_dst_32+"/d3d11.dll")
    if os.path.isfile(dxvk_dst_32+"/dxgi.dll"):
        os.remove(dxvk_dst_32+"/dxgi.dll")      
    
    shutil.copy(proton_dir + ext + "/lib64/wine/dxvk/d3d11.dll", dxvk_dst + "/d3d11.dll")
    shutil.copy(proton_dir + ext + "/lib64/wine/dxvk/dxgi.dll", dxvk_dst + "/dxgi.dll")
    shutil.copy(proton_dir + ext + "/lib/wine/dxvk/d3d11.dll", dxvk_dst_32 + "/d3d11.dll")
    shutil.copy(proton_dir + ext + "/lib/wine/dxvk/dxgi.dll", dxvk_dst_32 + "/dxgi.dll")


def create_32bit_prefix(base_dir, app_id, proton_dir, prefix_dir):
    print("Creating 32bit Wine Prefix...")
    os.makedirs(base_dir + "/" + app_id + "/pfx", 0o755, exist_ok=True)

    # Create the prefix.  Copy default from Proton
    ext="/dist"
    if not os.path.isdir(proton_dir+"/dist"):
        ext="/files"
    copy_prefix(proton_dir + ext + "/share/default_pfx", prefix_dir)
    print("Proton: " + proton_dir)

    os.environ["WINEDLLPATH"] = proton_dir + ext + "/lib64/wine:"+proton_dir + ext + "/lib/wine"
    os.environ["PATH"] = proton_dir + ext + "/bin/:" + proton_dir + ext + "/lib/:" + proton_dir + ext + "/lib64/:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/snap/bin"
    os.environ["WINEPREFIX"] = prefix_dir
    os.environ["LD_LIBRARY_PATH"] = proton_dir + ext + "/lib64:" + proton_dir + ext + "/lib:" + steam_dir + "/ubuntu12_32:" + steam_dir + "/ubuntu12_32/panorama:"
    wine = proton_dir + ext + "/bin/wineserver"

    # boot prefix by calling Proton's wineserver wineboot
    p_64 = subprocess.call([wine, "-w", "wineboot"])
    i = 5
    for c in range(i):
        print("Finishing... ("+str(i)+")")
        i = i-1
        time.sleep(1)
    # above loop is workaround to ensure process returns safely.  For some reason wineserver does not always call/return wineboot properly.

    shutil.rmtree(prefix_dir, ignore_errors=True)
    os.makedirs(base_dir + "/" + app_id + "/pfx", 0o755, exist_ok=True)

    # Resetting environment variables to stay clear of any possible interferences
    os.environ["WINEARCH"] = "win32"
    os.environ["WINEDLLPATH"] = ""
    os.environ["PATH"] = "/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/snap/bin"
    os.environ["LD_LIBRARY_PATH"] = ""

    try:
        p_32 = subprocess.call('winecfg')
    except Exception:
        p_32 = subprocess.call('/usr/bin/winecfg')
        pass

    os.makedirs(base_dir + "/" + app_id + "/pfx/drive_c/windows/syswow64", exist_ok=True)

    print("Installing dxvk...")

    dxvk_dst = prefix_dir + "/drive_c/windows/system32"
    dxvk_dst_32 = prefix_dir + "/drive_c/windows/syswow64"
    if os.path.isfile(dxvk_dst + "/d3d11.dll"):
        os.remove(dxvk_dst + "/d3d11.dll")
    if os.path.isfile(dxvk_dst + "/dxgi.dll"):
        os.remove(dxvk_dst + "/dxgi.dll")
    if os.path.isfile(dxvk_dst_32 + "/d3d11.dll"):
        os.remove(dxvk_dst_32 + "/d3d11.dll")
    if os.path.isfile(dxvk_dst_32 + "/dxgi.dll"):
        os.remove(dxvk_dst_32 + "/dxgi.dll")

    shutil.copy(proton_dir + ext + "/lib64/wine/dxvk/d3d11.dll", dxvk_dst + "/d3d11.dll")
    shutil.copy(proton_dir + ext + "/lib64/wine/dxvk/dxgi.dll", dxvk_dst + "/dxgi.dll")
    shutil.copy(proton_dir + ext + "/lib/wine/dxvk/d3d11.dll", dxvk_dst_32 + "/d3d11.dll")
    shutil.copy(proton_dir + ext + "/lib/wine/dxvk/dxgi.dll", dxvk_dst_32 + "/dxgi.dll")

    print("32bit Wine Prefix successfully created.")
    print("Please execute the following commands to set Proton to 32bit before starting the game")
    print("$ cd ~/.steam/steam/steamapps/common/Proton\ 3.7/")
    print("$ sed -i 's/wine64/wine/' proton")
    print("Please run the following command after your session to reset Proton back to default")
    print("$ sed -i 's/wine/wine64/' proton")


def use_winetricks(base_dir):
    prefixes = []
    all_paths = os.listdir(base_dir) 
    for path in all_paths:
        if not path.startswith("."):
            prefixes.append(path)
    for index, prefix in enumerate(prefixes):
        print("["+str(index)+"] "+prefix)
    print("[m] Enter prefix directory manually")

    prefix_choice = input("Select prefix: ")
    if prefix_choice == "m":
        prefix = input("Enter prefix directory in full: (eg /home/you/prefix2")
    else:
        prefix = base_dir+"/"+prefixes[int(prefix_choice)]+"/pfx"
    print("Prefix: "+prefix)
    input("Stop")

    ext="/dist"
    if not os.path.isdir(proton_dir+"/dist"):
        ext="/files"
    os.environ["WINEDLLPATH"] = proton_dir+ext + "/lib64/wine:"+proton_dir+ext + "/lib/wine"
    os.environ["PATH"] = proton_dir+ext + "/bin/:"+proton_dir+ext + "/lib/:"+proton_dir+ext + "/lib64/:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/snap/bin"
    os.environ["WINEPREFIX"] = prefix
    if not os.path.isdir(prefix + "/drive_c/Program Files (x86)"):
        use_32bit = True
    else:
        use_32bit = False

    if use_32bit:
        print("Using workaround for 32bit prefix...")
        if os.path.isdir(prefix + "/drive_c/windows/syswow64"):
            os.rename(prefix + "/drive_c/windows/syswow64", prefix + "/drive_c/windows/~syswow64")

    exec_cmd = input("Enter winetricks command (eg: winetricks corefonts xact)")
    splitcmd = exec_cmd.split()
    splitcmd[0] = base_dir+"/.winetricks/winetricks"
    subprocess.call(splitcmd)

    if use_32bit:
        print("Reverting workaround for 32bit prefix...")
        os.rename(prefix + "/drive_c/windows/~syswow64", prefix + "/drive_c/windows/syswow64")

            
def steam_cmd(base_dir, n2p_library, app_name,app_id):
    steam_user = input("Please enter your Steam username: ")
    steamcmd = base_dir+"/.steamcmd/steamcmd.sh"
    login = "+login "+steam_user
    install_dir = str('+force_install_dir "'+n2p_library+'/'+app_name+'"')
    app_update = "+app_update "+app_id
    subprocess.call([steamcmd, "+@sSteamCmdForcePlatformType windows", login, install_dir, app_update, "validate", "+quit"])
    return
    
#GLOBAL VARIABLES
home = os.path.expanduser("~")
base_dir = home+"/.local/share/native2proton"
config = configparser.ConfigParser()
n2p_library = None
proton_dir = None
steam_dir = None
userdata_dir = None
steam_user_id = None



#MAIN

#check for pervious installation
if os.path.isfile(base_dir+"/settings.conf"):
    print("Config found")
    config_file = base_dir+"/settings.conf"
    config.read_file(open(r''+config_file))
    n2p_library = config.get('DEFAULTS', 'n2p_library')
    proton_dir = config.get('DEFAULTS', 'proton_dir')
    steam_dir = config.get('DEFAULTS', 'steam_dir')
    print("")
else:
    #set up
    n2p_config(home, base_dir, config)

print("Default download location: "+n2p_library)
print("Proton location: "+proton_dir)
menulist = ["Install game", "Use winetricks on prefix", "Install Non-Steam App [Experimental]", "Recreate config", "Quit"]
for index, menuitem in enumerate(menulist):
    print("["+str(index)+"] "+ menuitem)
choice = input("What would you like to do? ")

if choice == "0":
    install_game(base_dir, n2p_library, proton_dir, steam_dir, "steam")
elif choice == "1":
    use_winetricks(base_dir)
elif choice == "2":
    install_game(base_dir, n2p_library, proton_dir, steam_dir, "nonsteam")
elif choice == "3":
    n2p_config(home, base_dir, config)
elif choice == "4":
    sys.exit()
