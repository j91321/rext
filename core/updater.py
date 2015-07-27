#This file is part of REXT
#updater.py - script that handles updating of REXT and it's components
#Author: Ján Trenčanský
#License: GNU GPL v3

import subprocess
import time


#Pull REXT from git repo
def update_rext():
    subprocess.Popen("git pull", shell=True).wait()
    time.sleep(4)


#Reset HEAD to discard local changes and pull
def update_rext_force():
    subprocess.Popen("git reset --hard", shell=True).wait()
    subprocess.Popen("git pull", shell=True).wait()
    time.sleep(4)


#Download OUI file, and recreate DB
def update_oui():
    pass
