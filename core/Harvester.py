#This file is part of REXT
#core.Harvester.py - super class for harvester scripts
#Author: Ján Trenčanský
#License: GNU GPL v3

import cmd

import core.globals
import interface.utils
from interface.messages import print_help


class RextHarvester(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        interface.utils.change_prompt(self, core.globals.active_module_path + core.globals.active_script)
        self.cmdloop()

    def do_exit(self, e):
        return True

    def do_run(self, e):
        pass

    def help_exit(self):
        print_help("Exit script")

    def help_run(self, e):
        print_help("Run script")