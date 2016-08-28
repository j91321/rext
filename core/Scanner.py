# This file is part of REXT
# core.Scanner.py - super class for scanner scripts
# Author: Ján Trenčanský
# License: GNU GPL v3

import cmd

import core.globals
import interface.utils
from interface.messages import print_help, print_error, print_info


class RextScanner(cmd.Cmd):
    host = ""
    port = "80"

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

    def do_set(self, e):
        args = e.split(' ')
        try:
            if args[0] == "host":
                if interface.utils.validate_ipv4(args[1]):
                    self.host = args[1]
                else:
                    print_error("please provide valid IPv4 address")
            elif args[0] == "port":
                if str.isdigit(args[1]):
                    self.port = args[1]
                else:
                    print_error("port value must be integer")
        except IndexError:
            print_error("please specify value for variable")

    def complete_set(self, text, line, begidx, endidx):
        modules = ["host", "port"]
        module_line = line.partition(' ')[2]
        igon = len(module_line) - len(text)
        return [s[igon:] for s in modules if s.startswith(module_line)]

    def do_host(self, e):
        print_info(self.host)

    def do_port(self, e):
        print_info(self.port)

    def help_back(self):
        print_help("Exit script")

    def help_run(self):
        print_help("Run script")

    def help_host(self):
        print_help("Prints current value of host")

    def help_port(self):
        print_help("Prints current value of port")

    def help_set(self):
        print_help("Set value of variable: \"set host 192.168.1.1\"")

    def help_info(self, e):
        print_help("Show info about loaded module")