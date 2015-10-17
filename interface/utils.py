# This file is part of REXT
# core.utils.py - script contains useful static methods
# Author: Ján Trenčanský
# License: GNU GPL v3

import os
import re
import socket
import sys
import urllib
import urllib.request
import core.globals


def validate_mac(mac):
    xr = re.compile(r'^([a-fA-F0-9]{2}([:-]?)[a-fA-F0-9]{2}(\2[a-fA-F0-9]{2}){4})$')
    rr = xr.match(mac)
    return rr


def lookup_mac(mac):
    # TODO: Maybe add index over oui table
    mac = mac.replace(":", "")
    mac = mac.replace("-", "")
    cursor = core.globals.ouidb_conn.cursor()
    cursor.execute("SELECT name FROM oui WHERE oui == ?", [mac[:6]])
    company_name = (cursor.fetchone())
    if company_name is not None:
        company_name = company_name[0]
        return "(" + company_name + ")"
    else:
        return "(Unknown)"


def validate_ipv4(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def file_exists(file):  # I know this is useless wrapper but it's probably better not to import os everywhere
    if os.path.isfile(file):
        return True
    else:
        return False


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


def identify_os():
    if os.name == "nt":
        operating_system = "windows"
    elif os.name == "posix":
        operating_system = "posix"
    else:
        operating_system = "unknown"
    return operating_system


# Simple wget implementation with status bar
def wget(url, path):

    def hook(blocks, block_size, total_size):
        current = blocks * block_size
        percent = 100.0 * current / total_size
        # Found this somewhere
        line = '[{0}{1}]'.format('=' * int(percent / 2), ' ' * (50 - int(percent / 2)))
        status = '\r{0:3.0f}%{1} {2:3.1f}/{3:3.1f} MB'
        sys.stdout.write(status.format(percent, line, current/1024/1024, total_size/1024/1024))

    try:
        (path, headers) = urllib.request.urlretrieve(url, path, hook)
    except:
        os.remove(path)
        print()
        return False

    return path

