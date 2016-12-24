# This file is part of REXT
# core.loader.py - script that handles dynamic loading an unloading scripts
# Author: Ján Trenčanský
# delete_module was written by Michael P. Reilly
# it was taken from https://mail.python.org/pipermail/tutor/2006-August/048596.html
# License: GNU GPL v3

import importlib
import importlib.util
import sqlite3
import interface.utils
import os
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
        # FIXME this is not the best way to parse dependencies probably, may break rext if == is used
        dependency = dependency[:dependency.find('>=')]
        # FIXME beautifulsoup4 is imported as bs4
        if dependency == 'beautifulsoup4':
            dependency = 'bs4'
        found = importlib.util.find_spec(dependency)
        if found is None:
            print_warning(dependency + " not found some modules may not work!")
    dependency_list.close()


def check_create_dirs():
    directories = ['./output']
    for dir in directories:
        if not os.path.exists(dir):
            os.makedirs(dir)


def open_database(path):
    if interface.utils.file_exists(path):
        connection = sqlite3.connect(path)
        return connection
    else:
        return None


def close_database(connection):
    connection.close()
