# This file is part of REXT
# updater.py - script that handles updating of REXT and it's components
# Author: Ján Trenčanský
# License: GNU GPL v3

import subprocess
import time
import re
import os
import sys

import interface.utils
import core.globals
from interface.messages import print_error, print_info


# Pull REXT from git repo
def update_rext():
    subprocess.Popen("git pull", shell=True).wait()
    time.sleep(4)


# Reset HEAD to discard local changes and pull
def update_rext_force():
    subprocess.Popen("git reset --hard", shell=True).wait()
    subprocess.Popen("git pull", shell=True).wait()
    time.sleep(4)


# Download OUI file, and recreate DB
def update_oui():
    if interface.utils.file_exists("./databases/oui.db") and core.globals.ouidb_conn is not None:
            connection = core.globals.ouidb_conn
            cursor = connection.cursor()
            # Truncate database
            print_info("Truncating oui table")
            cursor.execute("""DROP TABLE oui""")
            cursor.execute("""CREATE TABLE oui (
                             id INTEGER PRIMARY KEY NOT NULL,
                             oui TEXT UNIQUE,
                             name TEXT)""")
            # This is very important, sqlite3 creates transaction for every INSERT/UPDATE/DELETE
            # but can handle only dozen of transactions at a time.
            # BEGIN guarantees that only one transaction will be used.
            # Now the DB rebuild should take only seconds
            cursor.execute('begin')
            print_info("Downloading new OUI file")
            path = interface.utils.wget("http://standards.ieee.org/regauth/oui/oui.txt", "./output/tmp_oui.txt")
            if not path:
                print_error('Failed to download')
                return
            file = open(path, "r")
            regex = re.compile(r"\(base 16\)")
            for line in file:
                if regex.search(line) is not None:
                    line = "".join(line.split("\t"))
                    line = line.split("(")
                    oui = line[0].replace(" ", "")
                    company = line[1].split(")")[1]
                    company = company.replace("\n", "")
                    if company == " ":
                        company = "Private"
                    try:
                        cursor.execute("INSERT INTO oui (oui, name) VALUES (?, ?)", [oui, company])
                        status = '\rInserting {0}:{1}'
                        sys.stdout.write(status.format(company, oui))
                    except Exception as e:
                        # CONRAD CORP. and CERN + ROYAL MELBOURNE INST OF TECH share oui, this should be considered
                        # print(e)
                        # print(oui + " " + company)
                        # SELECT name FROM oui.oui WHERE oui = oui
                        # UPDATE oui.oui SET name = name+" OR "+company WHERE oui=oui
                        pass
            print()

            # Add a few OUIs manually (from NMAP oui file)
            cursor.execute("INSERT INTO oui (oui, name) VALUES ('525400', 'QEMU Virtual NIC')")
            cursor.execute("INSERT INTO oui (oui, name) VALUES ('B0C420', 'Bochs Virtual NIC')")
            cursor.execute("INSERT INTO oui (oui, name) VALUES ('DEADCA', 'PearPC Virtual NIC')")
            cursor.execute("INSERT INTO oui (oui, name) VALUES ('00FFD1', 'Cooperative Linux virtual NIC')")
            connection.commit()
            try:
                os.remove("./output/tmp_oui.txt")
            except OSError:
                pass





