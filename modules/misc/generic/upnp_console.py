# Name:UPNP console
# File:upnp_console.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 30.07.2016
# Last modified: 30.07.2016
# Description: miranda-upnp.py

import core.Upnp
import core.io
import time
import traceback

from interface.messages import print_red, print_error, print_yellow, print_blue


class Upnp(core.Upnp.Upnp):
    """
UPNP console
    """

    def __init__(self):
        core.Upnp.Upnp.__init__(self)

    def do_msearch(self, e):
        defaultST = "upnp:rootdevice"
        st = "schemas-upnp-org"
        myip = ''
        lport = self.port

        # if argc >= 3:
        #     if argc == 4:
        #         st = argv[1]
        #         searchType = argv[2]
        #         searchName = argv[3]
        #     else:
        #         searchType = argv[1]
        #         searchName = argv[2]
        #     st = "urn:%s:%s:%s:%s" % (st,searchType,searchName,hp.UPNP_VERSION.split('.')[0])
        # else:
        st = defaultST

        # Build the request
        request = "M-SEARCH * HTTP/1.1\r\n" \
                  "HOST:%s:%d\r\n" \
                  "ST:%s\r\n" % (self.host, self.port, st)
        for header, value in self.msearchHeaders.items():
            request += header + ':' + value + "\r\n"
        request += "\r\n"

        print("Entering discovery mode for '%s', Ctl+C to stop..." % st)

        # Have to create a new socket since replies will be sent directly to our IP, not the multicast IP
        server = self.create_new_listener(myip, lport)
        if not server:
            print('Failed to bind port %d' % lport)
            return

        self.send(request, server)
        count = 0
        start = time.time()

        while True:
            try:
                if 0 < self.max_hosts <= count:
                    break

                if 0 < self.timeout < (time.time() - start):
                    raise Exception("Timeout exceeded")

                if self.parseSSDPInfo(self.recieve(1024, server), False, False):
                    count += 1

            except AttributeError:  # On Ctrl-C parseSSDPInfo raises AttributeError exception
                print('\nDiscover mode halted...')
                break

    def get_host_info(self, host_info, index):

        if host_info is not None:
            # If this host data is already complete, just display it
            if host_info['dataComplete']:
                print_yellow('Data for this host has already been enumerated!')
                return
            try:
                # Get extended device and service information
                if host_info:
                            print_blue("Requesting device and service info for " +
                                       host_info['name'] + " (this could take a few seconds)...")
                            if not host_info['dataComplete']:
                                (xmlHeaders, xmlData) = self.get_xml(host_info['xml_file'])
                                print(xmlHeaders)
                                print(xmlData)
                                if not xmlData:
                                    print_red('Failed to request host XML file:' + host_info['xmlFile'])
                                    return
                                #if self.getHostInfo(xmlData, xmlHeaders, index) == False:
                                #    print_error("Failed to get device/service info for " + host_info['name'])
                                #    return
                            print('Host data enumeration complete!')
                            #hp.updateCmdCompleter(hp.ENUM_HOSTS)
                            return
            except KeyboardInterrupt:
                return

    def do_device(self, e):  # This was originally host command but since REXT uses host on something else...
        host_info = None
        args = e.split(' ')
        if args[0] == "get":
            if len(args) != 2:
                print_red("Invalid number of arguments")
                return
            try:
                index = int(args[1])
                host_info = self.enum_hosts[index]
            except Exception:
                print_error("Second argument is not a number")
                return
            self.get_host_info(host_info, index)




Upnp()
