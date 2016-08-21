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


def print_success(*args, **kwargs):
    print(Color.GREEN + Color.BOLD + "[+]" + Color.ENDC, *args, **kwargs)


def print_error(*args, **kwargs):
    print(Color.RED + Color.BOLD + "[-]" + Color.ENDC, *args, **kwargs)


def print_failed(*args, **kwargs):
    print(Color.RED + Color.BOLD + "[-]" + Color.ENDC, *args, **kwargs)


def print_warning(*args, **kwargs):
    print(Color.YELLOW + Color.BOLD + "[!]" + Color.ENDC, *args, **kwargs)


def print_help(*args, **kwargs):
    print(Color.PURPLE + Color.BOLD + "[?]" + Color.ENDC, *args, **kwargs)


def print_info(*args, **kwargs):
    print(Color.BLUE + Color.BOLD + "[*]" + Color.ENDC, *args, **kwargs)


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
