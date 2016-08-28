# This file is part of REXT
# core.Misc.py - super class for misc scripts
# Author: Ján Trenčanský
# License: GNU GPL v3

import cmd

import core.globals
import interface.utils
from interface.messages import print_help


class RextMisc(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        interface.utils.change_prompt(self, core.globals.active_module_path + core.globals.active_script)
        self.cmdloop()

    def do_info(self, e):
        print(self.__doc__)

    def do_back(self, e):
        return True

    def do_run(self, e):
        pass

    def help_back(self):
        print_help("Exit script")

    def help_run(self):
        print_help("Run script")

    def help_info(self, e):
        print_help("Show info about loaded module")