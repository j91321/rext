#This file is part of REXT
#core.utils.py - script contains useful static methods
#Author: Ján Trenčanský
#License: ADD LATER

import os
import re


def validate_mac(mac):
    xr = re.compile(r'^([a-fA-F0-9]{2}([:-]?)[a-fA-F0-9]{2}(\2[a-fA-F0-9]{2}){4})$')
    rr = xr.match(mac)
    return rr


def list_dirs(path):
    """
    List directories in specified path
    :param path:Path to parent directory
    :return:List of child directories
    """
    dirs = {name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))}
    if "__pycache__" in dirs:
        dirs.remove("__pycache__")
    elif ".cache" in dirs:
        dirs.remove(".cache")
    return dirs


def list_files(path):
    """
    Lits files in path
    :param path: Path to directory
    :return: List of files in directory without extension
    """
    files = {os.path.splitext(file)[0] for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))}
    if "__init__" in files:
        files.remove("__init__")
    return files


def make_import_name(string):
    string = "modules." + string
    return re.sub('/', '.', string)


def change_prompt(interpreter, path):
    if path is not None:
        interpreter.prompt = path + ">"
    else:
        interpreter.prompt = ">"