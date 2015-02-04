#This file is part of REXT
#core.Scanner.py - super class for scanner scripts
#Author: Ján Trenčanský
#License: ADD LATER

import cmd
import core.globals
import core.utils


class RextScanner(cmd.Cmd):
    host = ""
    port = "80"

    def __init__(self):
        cmd.Cmd.__init__(self)
        core.utils.change_prompt(self, core.globals.active_module_path + core.globals.active_script)
        self.cmdloop()

    def do_exit(self, e):
        return True

    def do_run(self, e):
        pass

    def do_set(self, e):
        args = e.split(' ')
        if args[0] == "host":
            self.host = args[1]
        elif args[0] == "port":
            self.port = args[1]

    def do_host(self, e):
        print(self.host)

    def do_port(self, e):
        print(self.port)

    def help_exit(self):
        print("Exit script")

    def help_run(self, e):
        print("Run script")

    def help_host(self):
        print("Prints current value of host")

    def help_port(self):
        print("Prints current value of port")