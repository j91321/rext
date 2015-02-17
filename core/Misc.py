#This file is part of REXT
#core.Misc.py - super class for misc scripts
#Author: Ján Trenčanský
#License: ADD LATER

import cmd

import core.globals
import interface.utils


class RextMisc(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        interface.utils.change_prompt(self, core.globals.active_module_path + core.globals.active_script)
        self.cmdloop()

    def do_exit(self, e):
        return True

    def do_run(self, e):
        pass

    def help_exit(self):
        print("Exit script")

    def help_run(self, e):
        print("Run script")