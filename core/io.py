# This file is part of REXT
# core.io.py - Input / Output utils, for writing files and databases
# Author: Ján Trenčanský
# License: GNU GPL v3

import datetime
import os
import core.globals
from interface.messages import print_error, print_info


# FIXME: If minute changes between two writes of one module, this will create two directories
def writefile(stream, filename):
    dirpath = "output/" + core.globals.active_script + "_" + datetime.datetime.today().strftime('%Y-%b-%d-%H:%M')
    try:
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        open(dirpath + "/" + filename, 'wb').write(stream)
        return dirpath
    except OSError:
        print_error("Unable to create directory")


def writetextfile(text, filename):
    dirpath = "output/" + core.globals.active_script + "_" + datetime.datetime.today().strftime('%Y-%b-%d-%H:%M')
    try:
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        open(dirpath + "/" + filename, 'w').write(text)
        return dirpath
    except OSError:
        print_error("Unable to create directory")


# Modified from http://stackoverflow.com/questions/3041986/python-command-line-yes-no-input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print_info(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print_error("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")
