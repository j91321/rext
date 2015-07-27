#This file is part of REXT
#cmdui.py - command line interface script
#Author: Ján Trenčanský
#License: GNU GPL v3

import cmd

import interface.utils
import core.globals
from core import loader
from core import updater
from interface.messages import print_error, print_help, print_blue


class Interpreter(cmd.Cmd):
    #
    modules = {}
    active_module = modules
    active_module_import_name = ""

    def __init__(self):
        loader.check_dependencies()
        core.globals.ouidb_conn = loader.open_database("./databases/oui.db")
        if core.globals.ouidb_conn is None:
            print_error("OUI database could not be open, please provide OUI database")
        cmd.Cmd.__init__(self)
        self.prompt = ">"
        #Load banner
        with open("./interface/banner.txt", "r") as file:
            banner = ""
            for line in file.read():
                banner += line
            self.intro = banner
            file.close()
        #Load list of available modules in modules
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

    def emptyline(self):
        pass

    def postloop(self):
        print("Bye!")

    def do_exit(self, args):
        loader.close_database(core.globals.ouidb_conn)
        return True

    #Interpreter commands section

    def do_show(self, module):
        if module == "":
            if isinstance(self.active_module, dict):
                for key in self.active_module.keys():
                    print(key)
            elif isinstance(self.active_module, set):
                for file in self.active_module:
                    print(file)
        elif module == "modules":
            for key in self.modules.keys():
                print(key)
        elif module in self.modules.keys():
            for key in self.modules.get(module).keys():
                print(key)
        elif (self.active_module is dict) and (module in self.active_module.keys()):
            for key in self.active_module.get(module):
                print(key)
        else:
            print_error("Invalid argument for command show " + module)

    def do_load(self, module):
        if isinstance(self.active_module, set):
            core.globals.active_script = module
            module_path = core.globals.active_module_path + module
            self.active_module_import_name = interface.utils.make_import_name(module_path)
            loader.load_module(self.active_module_import_name)  # Module is loaded and executed
            try:
                loader.delete_module(self.active_module_import_name)  # Module is unloaded so it can be used again
            except ValueError:
                pass
            core.globals.active_module_import_name = ""
        elif isinstance(self.active_module, dict):
            if module in self.active_module.keys():
                self.active_module = self.active_module.get(module)
                core.globals.active_module_path += module + "/"
                interface.utils.change_prompt(self, core.globals.active_module_path)
            else:
                print_error(module + " not found")

    def do_unload(self, e):
        self.active_module = self.modules
        interface.utils.change_prompt(self, None)
        core.globals.active_module_path = ""

    def do_update(self, e):
        args = e.split(' ')
        if args[0] == "oui":
            print_blue("Updating OUI DB (not implemented)")
            updater.update_oui()
        elif args[0] == "force":
            print_blue("Discarding local changes and updating REXT")
            updater.update_rext_force()
        elif args[0] == "":
            print_blue("Updating REXT please wait...")
            updater.update_rext()
            print_blue("Update successful")

    #Help to commands section

    def help_show(self):
        print_help("List available modules and vendors")

    def help_load(self):
        print_help("load command help")

    def help_update(self):
        print_help("update command help")

    def help_exit(self):
        print_help("Exit REXT")

