# This file is part of REXT
# core.messages.py - script containing colors and messages
# Author: Ján Trenčanský
# License: GNU GPL v3
# Based on http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
from interface.utils import identify_os

if identify_os() == 'posix':

    class Color:
        BLUE = '\033[94m'
        GREEN = '\033[32m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        DARKCYAN = '\033[36m'
        BOLD = '\033[1m'
        UNDERL = '\033[4m'
        ENDC = '\033[0m'
else:
    class Color:
        BLUE = ''
        GREEN = ''
        YELLOW = ''
        RED = ''
        PURPLE = ''
        CYAN = ''
        DARKCYAN = ''
        BOLD = ''
        UNDERL = ''
        ENDC = ''


def print_success(msg):
    print(Color.GREEN + Color.BOLD + "Success: " + Color.ENDC + Color.GREEN + msg + Color.ENDC)


def print_error(msg):
    print(Color.RED + Color.BOLD + "Error: " + Color.ENDC + Color.RED + msg + Color.ENDC)


def print_failed(msg):
    print(Color.RED + Color.BOLD + "Failed: " + Color.ENDC + Color.RED + msg + Color.ENDC)


def print_warning(msg):
    print(Color.YELLOW + Color.BOLD + "Warning: " + Color.ENDC + Color.YELLOW + msg + Color.ENDC)


def print_help(msg):
    print(Color.PURPLE + Color.BOLD + "Help: " + Color.ENDC + Color.PURPLE + msg + Color.ENDC)


def print_info(msg):
    print(Color.BLUE + Color.BOLD + "Info: " + Color.ENDC + Color.BLUE + msg + Color.ENDC)


def print_green(msg):
    print(Color.GREEN + msg + Color.ENDC)


def print_yellow(msg):
    print(Color.YELLOW + msg + Color.ENDC)


def print_red(msg):
    print(Color.RED + msg + Color.ENDC)


def print_purple(msg):
    print(Color.PURPLE + msg + Color.ENDC)


def print_blue(msg):
    print(Color.BLUE + msg + Color.ENDC)
