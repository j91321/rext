#This file is part of REXT
#core.loader.py - script that handles dynamic loading an unloading scripts
#Author: Ján Trenčanský
#delete_module was written by Michael P. Reilly
#it was taken from https://mail.python.org/pipermail/tutor/2006-August/048596.html
#License: GNU GPL v3

import importlib
import importlib.util
from interface.messages import print_error, print_warning


def load_module(modname):
    try:
        importlib.import_module(modname)
    except ImportError:
        print_error("module doesn't exist")


def delete_module(modname, paranoid=None):
    from sys import modules
    try:
        thismod = modules[modname]
    except KeyError:
        raise ValueError(modname)
    these_symbols = dir(thismod)
    if paranoid:
        try:
            paranoid[:]  # sequence support
        except:
            raise ValueError('must supply a finite list for paranoid')
        else:
            these_symbols = paranoid[:]
    del modules[modname]
    for mod in modules.values():
        try:
            delattr(mod, modname)
        except AttributeError:
            pass
        if paranoid:
            for symbol in these_symbols:
                if symbol[:2] == '__':  # ignore special symbols
                    continue
                try:
                    delattr(mod, symbol)
                except AttributeError:
                    pass


def check_dependencies():
    dependency_list = open("./requirements.txt", 'rt', encoding='utf-8')
    while True:
        dependency = dependency_list.readline()
        if not dependency:
            break
        dependency = dependency[:dependency.find('==')]
        found = importlib.util.find_spec(dependency)
        if found is None:
            print_warning(dependency + " not found some modules may not work!")
    dependency_list.close()
