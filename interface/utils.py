# This file is part of REXT
# core.utils.py - script contains useful static methods
# Author: Ján Trenčanský
# License: GNU GPL v3

import os
import re
import socket
import sys
import string
import urllib
import urllib.request
import core.globals


def validate_mac(mac):
    xr = re.compile(r'^([a-fA-F0-9]{2}([:-]?)[a-fA-F0-9]{2}(\2[a-fA-F0-9]{2}){4})$')
    rr = xr.match(mac)
    if rr:
        return True
    else:
        return False


def lookup_mac(mac):
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
    if ".cache" in dirs:
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


def make_import_name(input_value):
    input_value = "modules." + input_value
    return re.sub('/', '.', input_value)


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
        # Found this somewhere, don't remember where sorry
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


# Used for autocomplete, autocomplete of cmd expects simple list of all possibilities, but it's easier to define
# all menu options as data structure of nested dictionaries and lists
def dict_to_str(input_value):
    output = []
    for key in input_value.keys():
        items = input_value.get(key)
        if isinstance(items, dict):
            new_list = dict_to_str(items)
            for item in new_list:
                output.append(''.join('{} {}'.format(key, str(item))))
        elif isinstance(items, list) or isinstance(items, range):
            if len(items) == 0:
                output.append(''.join('{}'.format(key)))
            else:
                for item in items:
                    output.append(''.join('{} {}'.format(key, str(item))))
    return output


# Takes bytearray as argument and searches for all strings that are 4 letters or more in length
# works similar to unix strings program
def strings(input_array, minimum=4):
    result = ""
    for c in input_array:
        char = chr(c)
        if char in string.digits or char in string.ascii_letters or char in string.punctuation:
            result += char
            continue
        if len(result) >= minimum:
            yield result
        result = ""
    if len(result) >= minimum:
        yield result
