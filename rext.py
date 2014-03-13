#!/usr/bin/env python3

#Router EXploitation Toolkit
#Author: Ján Trenčanský
#License: ADD LATER
#Created: 7.9.2013
#Last modified: 7.9.2013
import cmd
import os
import glob

class Interpreter(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = ">"
        self.intro = """
================================
REXT:Router EXploitation Toolkit
Author:Ján Trenčanský
Version:0.0
Codename:Franjo
License:

Commands: show, load, help, exit
================================
"""
        
    def emptyline(self):
        pass
    
    def postloop(self):
        print("Bye!")
        
    def do_exit(self, args):
        return True        

    #Interpreter commands section

    def do_show(self, args):
        if ".." not in args:
            modules = glob.glob("./modules/" +args+"/*/*.py")
            for module in modules:
                print(module)
        else:
            print("What are you trying to do?")

    def do_load(self, e):
        import modules.harvesters.airlive.WT2000ARM
        modules.harvesters.airlive.WT2000ARM.Harvester()

    #Help to commands section

    def help_show(self):
        print("show command help")
        
    def help_load(self):
        print("load command help")
        
    def help_exit(self):
        print("Exit REXT")
        
if __name__ == "__main__":
    inter = Interpreter()
    inter.cmdloop()

