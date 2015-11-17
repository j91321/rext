# This file is part of REXT
# core.Decryptor.py - super class for decrypt scripts
# Author: Ján Trenčanský
# License: GNU GPL v3

import cmd

import core.globals
import interface.utils
from interface.messages import print_error, print_help


class RextDecryptor(cmd.Cmd):
    input_file = ""

    def __init__(self):
        cmd.Cmd.__init__(self)
        interface.utils.change_prompt(self, core.globals.active_module_path + core.globals.active_script)
        self.cmdloop()

    def do_exit(self, e):
        return True

    def do_run(self, e):
        pass

    def do_set(self, e):
        args = e.split(' ')
        try:
            if args[0] == "file":
                if interface.utils.file_exists(args[1]):
                    self.input_file = args[1]
                else:
                    print_error("file does not exist")
        except IndexError:
            print_error("please specify value for variable")

    def do_file(self, e):
        print(self.input_file)

    def help_exit(self):
        print_help("Exit script")

    def help_run(self):
        print_help("Run script")

    def help_file(self):
        print_help("Prints current value of file")

    def help_set(self):
        print_help("Set value of variable: \"set file /tmp/FW.bin\"")