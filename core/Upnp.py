# This file is part of REXT
# core.Upnp.py - super class for UPNP scripts
# Author: Ján Trenčanský
# Original: Craig Heffner
# Disclaimer: most of the code is ported to python 3 from his awesome miranda-upnp tool
# his tool has only one disadvantage, very bad UI in my opinion
# https://code.google.com/archive/p/mirandaupnptool/
# License: GNU GPL v3

import cmd
import socket
import struct
import select
import requests
import time
import traceback

import core.globals
import interface.utils
from interface.messages import print_error, print_help, print_info, print_warning, print_red, print_blue


class Upnp(cmd.Cmd):
    host = "239.255.255.250"  # Should be modifiable
    port = 1900  # and this
    msearchHeaders = {'MAN': '"ssdp:discover"', 'MX': '2'}
    upnp_version = '1.0'
    max_recv = 8192
    max_hosts = 0
    timeout = 0  # and this
    http_headers = []
    enum_hosts = {}
    verbose = False  # and this
    uniq = True  # and this
    log_file = False  # and this
    batch_file = None  # and this
    interface = None  # and this
    csock = False
    ssock = False
    mreq = None

    def __init__(self):
        cmd.Cmd.__init__(self)
        interface.utils.change_prompt(self, core.globals.active_module_path + core.globals.active_script)
        self.initialize_sockets()
        self.cmdloop()

    def initialize_sockets(self):
        try:
            # This is needed to join a multicast group
            self.mreq = struct.pack("4sl", socket.inet_aton(self.host), socket.INADDR_ANY)
            # Set up client socket
            self.csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.csock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            # Set up server socket
            self.ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # BSD systems also need to set SO_REUSEPORT
            try:
                self.ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass

            # Only bind to this interface
            if self.interface is not None:
                print_info("Binding to interface: " + self.interface)
                self.ssock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                                      struct.pack("%ds" % (len(self.interface) + 1,), self.interface))
                self.csock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                                      struct.pack("%ds" % (len(self.interface) + 1,), self.interface))

            try:
                self.ssock.bind(('', self.port))
            except Exception:
                print_warning("failed to bind: " + self.host + ":" + str(self.port) + " ")
            try:
                self.ssock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)
            except Exception:
                print_warning("failed to join multicast group")
        except Exception:
            print_error("failed to initialize UPNP sockets")
            return False
        return True

    # Clean up file/socket descriptors
    def cleanup(self):
        self.csock.close()
        self.ssock.close()

    # Send network data
    def send(self, data, socket):
        # By default, use the client socket that's part of this class
        if not socket:
            socket = self.csock
        try:
            socket.sendto(bytes(data, 'UTF-8'), (self.host, self.port))
            return True
        except Exception as e:
            print_error("send method failed for " + self.host + ":" + str(self.port))
            print(e)
            return False

    # Receive network data
    def recieve(self, size, socket):
        if not socket:
            socket = self.ssock

        if self.timeout:
            socket.setblocking(0)
            ready = select.select([socket], [], [], self.timeout)[0]
        else:
            socket.setblocking(1)
            ready = True
        try:
            if ready:
                return socket.recv(size)
            else:
                return False
        except:
            return False

    # Create new UDP socket on ip, bound to port
    def create_new_listener(self, ip, port):
        try:
            newsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            newsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # BSD systems also need to set SO_REUSEPORT
            try:
                newsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except:
                pass
            newsock.bind((ip, port))
            return newsock
        except Exception:
            return False

    # Return the class's primary server socket
    def listener(self):
        return self.ssock

    # Return the class's primary client socket
    def sender(self):
        return self.csock

    # Parse a URL, return the host and the page
    def parse_url(self, url):
        delim = '://'
        host = False
        page = False

        # Split the host and page
        try:
            (host, page) = url.split(delim)[1].split('/', 1)
            page = '/' + page
        except:
            # If '://' is not in the url, then it's not a full URL, so assume that it's just a relative path
            page = url

        return host, page

    # Pull the header info for the specified HTTP header - case insensitive
    def parse_header(self, data, header):
        delimiter = "%s:" % header
        lowerdelim = delimiter.lower()
        dataarray = data.split("\r\n")

        # Loop through each line of the headers
        for line in dataarray:
            lowerline = line.lower()
            # Does this line start with the header we're looking for?
            if lowerline.startswith(lowerdelim):
                try:
                    return line.split(':', 1)[1].strip()
                except:
                    print_error("parsing header data failed for: " + header)

    # Parses SSDP notify and reply packets, and populates the ENUM_HOSTS dict
    def parseSSDPInfo(self, data, showUniq, verbose):
        data = data.decode('utf-8')  # When Ctl-C is pressed data is set to False and exception should be raised
        host_found = False
        found_location = False
        message_type = None
        xml_file = None
        host = False
        page = False
        upnp_type = None
        known_headers = {'NOTIFY': 'notification', 'HTTP/1.1 200 OK': 'reply'}

        # Use the class defaults if these aren't specified
        if not showUniq:
            showUniq = self.uniq
        if not verbose:
            verbose = self.verbose

        # Is the SSDP packet a notification, a reply, or neither?
        for text, message_type in known_headers.items():
            if data.upper().startswith(text):
                break
            else:
                message_type = False

        # If this is a notification or a reply message...
        if message_type:
            # Get the host name and location of its main UPNP XML file
            xml_file = self.parse_header(data, "LOCATION")
            upnp_type = self.parse_header(data, "SERVER")
            (host, page) = self.parse_url(xml_file)

            # Sanity check to make sure we got all the info we need
            if xml_file is None or host == False or page == False:
                print_error("parsing recieved header:")
                print_red(data)
                return False

            # Get the protocol in use (i.e., http, https, etc)
            protocol = xml_file.split('://')[0] + '://'

            # Check if we've seen this host before; add to the list of hosts if:
            # 1. This is a new host
            # 2. We've already seen this host, but the uniq hosts setting is disabled
            for hostID, hostInfo in self.enum_hosts.items():
                if hostInfo['name'] == host:
                    host_found = True
                    if self.uniq:
                        return False

            if (host_found and not self.uniq) or not host_found:
                # Get the new host's index number and create an entry in ENUM_HOSTS
                index = len(self.enum_hosts)
                self.enum_hosts[index] = {
                    'name': host,
                    'dataComplete': False,
                    'proto': protocol,
                    'xml_file': xml_file,
                    'serverType': None,
                    'upnpServer': upnp_type,
                    'deviceList': {}
                }
                # Be sure to update the command completer so we can tab complete through this host's data structure
                # self.updateCmdCompleter(self.ENUM_HOSTS)

            # Print out some basic device info
            print_blue("SSDP " + message_type + " message from " + host)

            if xml_file:
                found_location = True
                print_blue("XML file is located at " + xml_file)

            if upnp_type:
                print_blue("Device is running: " + upnp_type)

            return True

    # Send GET request for a UPNP XML file
    def get_xml(self, url):
        headers = {'USER-AGENT': 'uPNP/' + self.upnp_version,
                   'CONTENT-TYPE': 'text/xml; charset="utf-8"'}

        try:
            # Use urllib2 for the request, it's awesome
            #req = urllib.Request(url, None, headers) # This is GET
            #response = urllib.urlopen(req)
            response = requests.get(url, headers=headers, timeout=60)
            output = response.text
            headers = response.headers
            return headers, output
        except Exception:
            print("Request for '%s' failed" % url)
            return False, False

    def do_exit(self, e):
        return True

    def do_run(self, e):
        self.cleanup()
        pass

    def do_set(self, e):
        args = e.split(' ')
        try:
            if args[0] == "host":
                if interface.utils.validate_ipv4(args[1]):
                    self.host = args[1]
                else:
                    print_error("please provide valid IPv4 address")
            elif args[0] == "port":
                if str.isdigit(args[1]):
                    self.port = args[1]
                else:
                    print_error("port value must be integer")
        except IndexError:
            print_error("please specify value for variable")

    def do_info(self, e):
        print(self.__doc__)

    def do_host(self, e):
        print(self.host)

    def do_port(self, e):
        print(str(self.port))

    def help_exit(self):
        print_help("Exit script")

    def help_run(self):
        print_help("Run script")

    def help_host(self):
        print_help("Prints current value of host")

    def help_port(self):
        print_help("Prints current value of port")

    def help_set(self):
        print_help("Set value of variable: \"set host 192.168.1.1\"")

    def help_info(self, e):
        print_help("Show info about loaded module")
