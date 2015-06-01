#This file is part of REXT
#core.io.py - Input / Output utils, for writing files and databases
#Author: Ján Trenčanský
#License: GNU GPL v3

import datetime
import os
import core.globals
from interface.messages import print_error


def writefile(stream, filename):
    dirpath = "output/" + core.globals.active_script + "_" + datetime.datetime.today().isoformat()
    try:
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
            open(dirpath + "/" + filename, 'wb').write(stream)
            return dirpath
    except OSError:
        print_error("Unable to create directory")