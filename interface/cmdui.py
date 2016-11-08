# This file is part of REXT
# cmdui.py - command line interface script
# Author: Ján Trenčanský
# License: GNU GPL v3

import cmd
import sys

import interface.utils
import core.globals
from core import loader
from core import updater
from interface.messages import print_error, print_help, print_info, print_success


class Interpreter(cmd.Cmd):
    #
    modules = {}
    commands = {'modules': [], 'show': []}
    active_module = modules
    active_module_import_name = ""

    def __init__(self, stdout=sys.stdout):
        loader.check_dependencies()
        loader.check_create_dirs()
        core.globals.ouidb_conn = loader.open_database("./databases/oui.db")
        if core.globals.ouidb_conn is None:
            print_error("OUI database could not be open, please provide OUI database")
        cmd.Cmd.__init__(self, stdout=stdout)  # stdout had to be added for tests
        self.prompt = ">"
        # Load banner
        with open("./interface/banner.txt", "r", encoding="utf-8") as file:
            banner = ""
            for line in file.read():
                banner += line
            self.intro = banner
            file.close()
        # Load list of available modules in modules
        module_directory_names = interface.utils.list_dirs("./modules")  # List directories in module directory
        for module_name in module_directory_names:
            path = "./modules/" + module_name
            vendors = interface.utils.list_dirs(path)
            vendors_dict = {}
            for vendor in vendors:
                vendor_path = path + "/" + vendor
                files = interface.utils.list_files(vendor_path)
                vendors_dict[vendor] = files
            self.modules[module_name] = vendors_dict
            for expl in list(vendors_dict.items()):
                if len(list(expl[1])) > 0:
                    for items in list(expl[1]):
                        pathmodule = '{}/{}/{}'.format(module_name, expl[0], items)
                        if pathmodule not in self.commands['modules']:
                            self.commands['modules'].append(pathmodule)
            for commands in self.commands['modules']:
                self.commands['show'].append(commands.split('/')[0])

    def emptyline(self):
        pass

    def postloop(self):
        print("Bye!")

    def do_exit(self, args):
        loader.close_database(core.globals.ouidb_conn)
        return True

    # Interpreter commands section
    # This was not written with performance in mind exactly...
    def do_show(self, module):
        if module == "":
            if isinstance(self.active_module, dict):
                for key in sorted(self.active_module.keys()):
                    print(key)
            elif isinstance(self.active_module, set):
                for file in sorted(self.active_module):
                    print(file)
        elif module == "modules":
            for key in sorted(self.modules.keys()):
                print(key)
        elif module in self.modules.keys():
            for key in sorted(self.modules.get(module).keys()):
                print(key)
        elif (self.active_module is dict) and (module in self.active_module.keys()):
            for key in sorted(self.active_module.get(module)):  # Yeah lot of sorting going on I know
                print(key)
        else:
            print_error("Invalid argument for command show " + module)

    def do_load(self, module):
        tokens = module.split("/")
        while tokens:  # That'll do pig.
            module = tokens.pop(0)
            if module in self.modules:  # Basic idea if first word is exploits, scanners etc. go to REXT root
                self.do_unload(None)
            if isinstance(self.active_module, set):  # If you are in the last layer and only .py files load them
                core.globals.active_script = module
                module_path = core.globals.active_module_path + module
                self.active_module_import_name = interface.utils.make_import_name(module_path)
                loader.load_module(self.active_module_import_name)  # Module is loaded and executed
                try:
                    loader.delete_module(self.active_module_import_name)  # Module is unloaded so it can be used again
                except ValueError:
                    pass
                core.globals.active_module_import_name = ""
            elif isinstance(self.active_module, dict):  # Else change directory depth
                if module in self.active_module.keys():
                    self.active_module = self.active_module.get(module)
                    core.globals.active_module_path += module + "/"
                    interface.utils.change_prompt(self, core.globals.active_module_path)
                else:
                    print_error(module + " not found")  # If error occurred then print error and break parsing
                    break

    def do_unload(self, e):
        self.active_module = self.modules  # Change every setting to REXT root
        interface.utils.change_prompt(self, None)
        core.globals.active_module_path = ""

    def do_update(self, e):
        args = e.split(' ')
        if args[0] == "oui":
            print_info("Updating OUI DB. Database rebuild may take several minutes.")
            # print_blue("Do you wish to continue? (y/n)")
            # Add if here
            updater.update_oui()
            print_success("OUI database updated successfully.")
        elif args[0] == "force":
            print_info("Discarding local changes and updating REXT")
            updater.update_rext_force()
        elif args[0] == "":
            print_info("Updating REXT please wait...")
            updater.update_rext()
            print_success("Update successful")

    # autocomplete section
    def complete_load(self, text, line, begidx, endidx):
        modules = self.commands['modules']
        module_line = line.partition(' ')[2]
        igon = len(module_line) - len(text)
        return [s[igon:] for s in modules if s.startswith(module_line)]

    def complete_show(self, text, line, begidx, endidx):
        modules = self.commands['show']
        module_line = line.partition(' ')[2]
        igon = len(module_line) - len(text)
        return [s[igon:] for s in modules if s.startswith(module_line)]

    # Help to commands section

    def help_show(self):
        print_help("list available modules and vendors")

    def help_load(self):
        print_help("load module")
        print("Usage: load <path>")

    def help_update(self):  # Recreate this with python formatter
        print_help("update REXT functionality")
        print("Usage: update <argument>")
        print("Available arguments:\n"
                     "\tno argument\n\t\tupdate REXT using git\n"
                     "\toui\n\t\tupdate MAC vendor database\n"
                     "\tforce\n\t\tdo git reset --hard and update\n")

    def help_unload(self):
        print_help("return to root of REXT modules")

    def help_exit(self):
        print_help("Exit REXT")

