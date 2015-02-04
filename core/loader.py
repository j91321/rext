#This file is part of REXT
#core.loader.py - script that handles dynamic loading an unloading scripts
#Author: Ján Trenčanský
#delete_module was written by Michael P. Reilly
#it was taken from https://mail.python.org/pipermail/tutor/2006-August/048596.html
#License: ADD LATER

import importlib


def load_module(modname):
    importlib.import_module(modname)


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