# Name:UPNP console
# File:upnp_console.py
# Author: Ján Trenčanský
# Original: Craig Heffner
# License: GNU GPL v3
# Created: 30.07.2016
# Last modified: 21.08.2016
# Disclaimer: most of the code is ported to python 3 from his awesome miranda-upnp tool
# his tool has only one disadvantage, very bad UI in my opinion
# https://code.google.com/archive/p/mirandaupnptool/

import core.io
import time
import base64
import cmd
import socket
import struct
import select
import requests
import xml.dom.minidom
import re
import traceback
import sys

import core.globals
import interface.utils
from interface.messages import print_error, print_help, print_info, print_warning, print_red, \
    print_success


class Upnp(cmd.Cmd):
    """
# Name:UPNP console
# Author: Ján Trenčanský
# Original: Craig Heffner
# License: GNU GPL v3
# Disclaimer: most of the code is ported to python 3 from his awesome miranda-upnp tool
# his tool has only one disadvantage, very bad UI in my opinion
# https://code.google.com/archive/p/mirandaupnptool/
    """
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
    soapEnd = None

    def __init__(self):
        cmd.Cmd.__init__(self)
        interface.utils.change_prompt(self, core.globals.active_module_path + core.globals.active_script)
        self.soapEnd = re.compile('</.*:envelope>')
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
    def send(self, data, sock):
        # By default, use the client socket that's part of this class
        if not sock:
            sock = self.csock
        try:
            sock.sendto(bytes(data, 'UTF-8'), (self.host, self.port))
            return True
        except Exception as e:
            print_error("send method failed for " + self.host + ":" + str(self.port))
            traceback.print_tb(e)
            return False

    # Receive network data
    def recieve(self, size, sock):
        if not sock:
            sock = self.ssock

        if self.timeout:
            sock.setblocking(0)
            ready = select.select([sock], [], [], self.timeout)[0]
        else:
            sock.setblocking(1)
            ready = True
        try:
            if ready:
                return sock.recv(size)
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
        # page = False

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
    def parse_ssdp_info(self, data, show_uniq, verbose):
        data = data.decode('utf-8')  # When Ctl-C is pressed data is set to False and exception should be raised
        host_found = False
        # found_location = False
        message_type = None
        # xml_file = None
        # host = False
        # page = False
        # upnp_type = None
        known_headers = {'NOTIFY': 'notification', 'HTTP/1.1 200 OK': 'reply'}

        # Use the class defaults if these aren't specified
        # if not show_uniq:
        #     show_uniq = self.uniq
        # if not verbose:
        #     verbose = self.verbose

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
            if xml_file is None or host is False or page is False:
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
            print_info("SSDP " + message_type + " message from " + host)

            if xml_file:
                # found_location = True
                print_info("XML file is located at " + xml_file)

            if upnp_type:
                print_info("Device is running: " + upnp_type)

            return True

    # Send GET request for a UPNP XML file
    def get_xml(self, url):
        headers = {'USER-AGENT': 'uPNP/' + self.upnp_version,
                   'CONTENT-TYPE': 'text/xml; charset="utf-8"'}

        try:
            # Use urllib2 for the request, it's awesome
            # req = urllib.Request(url, None, headers) # This is GET
            # response = urllib.urlopen(req)
            response = requests.get(url, headers=headers, timeout=60)
            output = response.text
            headers = response.headers
            return headers, output
        except Exception:
            print_error("Request for '%s' failed" % url)
            return False, False

            # Pull the name of the device type from a device type string

    # The device type string looks like: 'urn:schemas-upnp-org:device:WANDevice:1'
    def parse_device_type_name(self, string):
        delim1 = 'device:'
        delim2 = ':'

        if delim1 in string and not string.endswith(delim1):
            return string.split(delim1)[1].split(delim2, 1)[0]
        return False

    # Pull the name of the service type from a service type string
    # The service type string looks like: 'urn:schemas-upnp-org:service:Layer3Forwarding:1'
    def parse_service_type_name(self, string):
        delim1 = 'service:'
        delim2 = ':'

        if delim1 in string and not string.endswith(delim1):
            return string.split(delim1)[1].split(delim2, 1)[0]
        return False

    # Get info about a service's state variables
    def parse_service_state_vars(self, xml_root, service_pointer):

        na = 'N/A'
        var_vals = ['sendEvents', 'dataType', 'defaultValue', 'allowedValues']
        service_state_table = 'serviceStateTable'
        state_variable = 'stateVariable'
        name_tag = 'name'
        data_type = 'dataType'
        send_events = 'sendEvents'
        allowed_value_list = 'allowedValueList'
        allowed_value = 'allowedValue'
        allowed_value_range = 'allowedValueRange'
        minimum = 'minimum'
        maximum = 'maximum'

        # Create the serviceStateVariables entry for this service in ENUM_HOSTS
        service_pointer['serviceStateVariables'] = {}

        # Get a list of all state variables associated with this service
        try:
            state_vars = xml_root.getElementsByTagName(service_state_table)[0].getElementsByTagName(state_variable)
        except:
            # Don't necessarily want to throw an error here, as there may be no service state variables
            return False

        # Loop through all state variables
        for var in state_vars:
            for tag in var_vals:
                # Get variable name
                try:
                    var_name = str(var.getElementsByTagName(name_tag)[0].childNodes[0].data)
                except:
                    print_error(
                        'Failed to get service state variable name for service %s!' % service_pointer['fullName'])
                    continue

                service_pointer['serviceStateVariables'][var_name] = {}
                try:
                    service_pointer['serviceStateVariables'][var_name]['dataType'] = str(
                        var.getElementsByTagName(data_type)[0].childNodes[0].data)
                except:
                    service_pointer['serviceStateVariables'][var_name]['dataType'] = na
                try:
                    service_pointer['serviceStateVariables'][var_name]['sendEvents'] = str(
                        var.getElementsByTagName(send_events)[0].childNodes[0].data)
                except:
                    service_pointer['serviceStateVariables'][var_name]['sendEvents'] = na

                service_pointer['serviceStateVariables'][var_name][allowed_value_list] = []

                # Get a list of allowed values for this variable
                try:
                    vals = var.getElementsByTagName(allowed_value_list)[0].getElementsByTagName(allowed_value)
                except:
                    pass
                else:
                    # Add the list of allowed values to the ENUM_HOSTS dictionary
                    for val in vals:
                        service_pointer['serviceStateVariables'][var_name][allowed_value_list].append(
                            str(val.childNodes[0].data))

                # Get allowed value range for this variable
                try:
                    val_list = var.getElementsByTagName(allowed_value_range)[0]
                except:
                    pass
                else:
                    # Add the max and min values to the ENUM_HOSTS dictionary
                    service_pointer['serviceStateVariables'][var_name][allowed_value_range] = []
                    try:
                        service_pointer['serviceStateVariables'][var_name][allowed_value_range].append(
                            str(val_list.getElementsByTagName(minimum)[0].childNodes[0].data))
                        service_pointer['serviceStateVariables'][var_name][allowed_value_range].append(
                            str(val_list.getElementsByTagName(maximum)[0].childNodes[0].data))
                    except:
                        pass
        return True

    # Parse details about each service (arguements, variables, etc)
    def parse_service_info(self, service, index):
        # argIndex = 0
        arg_tags = ['direction', 'relatedStateVariable']
        action_list = 'actionList'
        action_tag = 'action'
        name_tag = 'name'
        argument_list = 'argumentList'
        argument_tag = 'argument'

        # Get the full path to the service's XML file
        xml_file = self.enum_hosts[index]['proto'] + self.enum_hosts[index]['name']
        if not xml_file.endswith('/') and not service['SCPDURL'].startswith('/'):
            try:
                xml_service_file = self.enum_hosts[index]['xml_file']
                slash_index = xml_service_file.rfind('/')
                xml_file = xml_service_file[:slash_index] + '/'
            except:
                xml_file += '/'

        if self.enum_hosts[index]['proto'] in service['SCPDURL']:
            xml_file = service['SCPDURL']
        else:
            xml_file += service['SCPDURL']
        service['actions'] = {}

        # Get the XML file that describes this service
        (xml_headers, xml_data) = self.get_xml(xml_file)
        if not xml_data:
            print_error('Failed to retrieve service descriptor located at:', xml_file)
            return False

        try:
            xml_root = xml.dom.minidom.parseString(xml_data)

            # Get a list of actions for this service
            try:
                action_list = xml_root.getElementsByTagName(action_list)[0]
            except:
                print_error('Failed to retrieve action list for service %s!' % service['fullName'])
                return False
            actions = action_list.getElementsByTagName(action_tag)
            if not actions:
                return False

            # Parse all actions in the service's action list
            for action in actions:
                # Get the action's name
                try:
                    action_name = str(action.getElementsByTagName(name_tag)[0].childNodes[0].data).strip()
                except:
                    print_error('Failed to obtain service action name (%s)!' % service['fullName'])
                    continue

                # Add the action to the ENUM_HOSTS dictonary
                service['actions'][action_name] = {}
                service['actions'][action_name]['arguments'] = {}

                # Parse all of the action's arguments
                try:
                    arg_list = action.getElementsByTagName(argument_list)[0]
                except:
                    # Some actions may take no arguments, so continue without raising an error here...
                    continue

                # Get all the arguments in this action's argument list
                arguments = arg_list.getElementsByTagName(argument_tag)
                if not arguments:
                    if self.verbose:
                        print_error('Action', action_name, 'has no arguments!')
                    continue

                # Loop through the action's arguments, appending them to the ENUM_HOSTS dictionary
                for argument in arguments:
                    try:
                        arg_name = str(argument.getElementsByTagName(name_tag)[0].childNodes[0].data)
                    except:
                        print_error('Failed to get argument name for', action_name)
                        continue
                    service['actions'][action_name]['arguments'][arg_name] = {}

                    # Get each required argument tag value and add them to ENUM_HOSTS
                    for tag in arg_tags:
                        try:
                            service['actions'][action_name]['arguments'][arg_name][tag] = str(
                                argument.getElementsByTagName(tag)[0].childNodes[0].data)
                        except:
                            print_error('Failed to find tag %s for argument %s!' % (tag, arg_name))
                            continue

            # Parse all of the state variables for this service
            self.parse_service_state_vars(xml_root, service)

        except Exception as e:
            print_error(
                'Caught exception while parsing Service info for service %s: %s' % (service['fullName'], str(e)))
            return False

        return True

    # Parse the list of services specified in the XML file
    def parse_service_list(self, xml_root, device, index):
        # serviceEntryPointer = False
        dict_name = "services"
        service_list_tag = "serviceList"
        service_tag = "service"
        service_name_tag = "serviceType"
        service_tags = ["serviceId", "controlURL", "eventSubURL", "SCPDURL"]

        try:
            device[dict_name] = {}
            # Get a list of all services offered by this device
            for service in xml_root.getElementsByTagName(service_list_tag)[0].getElementsByTagName(service_tag):
                # Get the full service descriptor
                service_name = str(service.getElementsByTagName(service_name_tag)[0].childNodes[0].data)

                # Get the service name from the service descriptor string
                service_display_name = self.parse_service_type_name(service_name)
                if not service_display_name:
                    continue

                # Create new service entry for the device in ENUM_HOSTS
                service_entry_pointer = device[dict_name][service_display_name] = {}
                service_entry_pointer['fullName'] = service_name

                # Get all of the required service info and add it to ENUM_HOSTS
                for tag in service_tags:
                    service_entry_pointer[tag] = str(service.getElementsByTagName(tag)[0].childNodes[0].data)

                # Get specific service info about this service
                self.parse_service_info(service_entry_pointer, index)
        except Exception as e:
            print_error('Caught exception while parsing device service list:', e)

    # Parse device info from the retrieved XML file
    def parse_device_info(self, xml_root, index):
        # device_entry_pointer = False
        dev_tag = "device"
        device_type = "deviceType"
        device_list_entries = "deviceList"
        device_tags = ["friendlyName", "modelDescription", "modelName", "modelNumber", "modelURL", "presentationURL",
                       "UDN", "UPC", "manufacturer", "manufacturerURL"]

        # Find all device entries listed in the XML file
        for device in xml_root.getElementsByTagName(dev_tag):
            try:
                # Get the deviceType string
                device_type_name = str(device.getElementsByTagName(device_type)[0].childNodes[0].data)
            except:
                continue

            # Pull out the action device name from the deviceType string
            device_display_name = self.parse_device_type_name(device_type_name)
            if not device_display_name:
                continue

            # Create a new device entry for this host in the ENUM_HOSTS structure
            device_entry_pointer = self.enum_hosts[index][device_list_entries][device_display_name] = {}
            device_entry_pointer['fullName'] = device_type_name

            # Parse out all the device tags for that device
            for tag in device_tags:
                try:
                    device_entry_pointer[tag] = str(device.getElementsByTagName(tag)[0].childNodes[0].data)
                except Exception as e:
                    if self.verbose:
                        print_error('Device', device_entry_pointer['fullName'], 'does not have a', tag)
                    continue
            # Get a list of all services for this device listing
            self.parse_service_list(device, device_entry_pointer, index)

        return

        # Display all info for a given host

    def show_complete_host_info(self, index, fp=False):
        # na = 'N/A'
        service_keys = ['controlURL', 'eventSubURL', 'serviceId', 'SCPDURL', 'fullName']
        if not fp:
            fp = sys.stdout

        if index < 0 or index >= len(self.enum_hosts):
            fp.write('Specified host does not exist...\n')
            return
        try:
            host_info = self.enum_hosts[index]
            if not host_info['dataComplete']:
                print_warning(
                    "Cannot show all host info because I don't have it all yet. Try running 'host info %d' first...\n" % index)
            fp.write('Host name:         %s\n' % host_info['name'])
            fp.write('UPNP XML File:     %s\n\n' % host_info['xml_file'])

            fp.write('\nDevice information:\n')
            for deviceName, deviceStruct in host_info['deviceList'].items():
                fp.write('\tDevice Name: %s\n' % deviceName)
                for serviceName, serviceStruct in deviceStruct['services'].items():
                    fp.write('\t\tService Name: %s\n' % serviceName)
                    for key in service_keys:
                        fp.write('\t\t\t%s: %s\n' % (key, serviceStruct[key]))
                    fp.write('\t\t\tServiceActions:\n')
                    for actionName, actionStruct in serviceStruct['actions'].items():
                        fp.write('\t\t\t\t%s\n' % actionName)
                        for argName, argStruct in actionStruct['arguments'].items():
                            fp.write('\t\t\t\t\t%s \n' % argName)
                            for key, val in argStruct.items():
                                if key == 'relatedStateVariable':
                                    fp.write('\t\t\t\t\t\t%s:\n' % val)
                                    for k, v in serviceStruct['serviceStateVariables'][val].items():
                                        fp.write('\t\t\t\t\t\t\t%s: %s\n' % (k, v))
                                else:
                                    fp.write('\t\t\t\t\t\t%s: %s\n' % (key, val))

        except Exception as e:
            print_error('Caught exception while showing host info:')
            traceback.print_stack(e)

            # Wrapper function...

    def get_host_information(self, xml_data, xml_headers, index):
        if self.enum_hosts[index]['dataComplete']:
            return

        if 0 <= index < len(self.enum_hosts):
            try:
                xml_root = xml.dom.minidom.parseString(xml_data)
                self.parse_device_info(xml_root, index)
                # self.enum_hosts[index]['serverType'] = xml_headers.getheader('Server')
                self.enum_hosts[index]['serverType'] = xml_headers['Server']
                self.enum_hosts[index]['dataComplete'] = True
                return True
            except Exception as e:
                print_error('Caught exception while getting host info:')
                traceback.print_stack(e)
        return False

    def do_back(self, e):
        return True

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

    def complete_set(self, text, line, begidx, endidx):
        modules = ["host", "port"]
        module_line = line.partition(' ')[2]
        igon = len(module_line) - len(text)
        return [s[igon:] for s in modules if s.startswith(module_line)]

    def do_info(self, e):
        print(self.__doc__)

    def do_host(self, e):
        print_info(self.host)

    def do_port(self, e):
        print_info(str(self.port))

    def help_back(self):
        print_help("Exit script")

    def help_host(self):
        print_help("Prints current value of host")

    def help_port(self):
        print_help("Prints current value of port")

    def help_set(self):
        print_help("Set value of variable: \"set host 192.168.1.1\"")

    def help_info(self):
        print_help("Show info about loaded module")

    def help_msearch(self):
        print_help("Actively locate UPNP hosts")

    def help_device(self):
        print_help("Allows you to query host information and iteract with a host's actions/services.")
        print("""\n\tdevice <list | get | info | summary | details | send> [host index #]
        'list' displays an index of all known UPNP hosts along with their respective index numbers
        'get' gets detailed information about the specified host
        'details' gets and displays detailed information about the specified host
        'summary' displays a short summary describing the specified host
        'info' allows you to enumerate all elements of the hosts object
        'send' allows you to send SOAP requests to devices and services

        Example:
            > device list
            > device get 0
            > device summary 0
            > device info 0 deviceList
            > device send 0 <device name> <service name> <action name>

        Notes:
            - All device commands EXCEPT for the 'device send', 'device info' and 'device list' commands take only one argument: the device index number.
            - The device index number can be obtained by running 'device list', which takes no futher arguments.
            - The 'device send' command requires that you also specify the device's device name, service name, and action name that you wish to send,
                in that order (see the last example in the Example section of this output). This information can be obtained by viewing the
                'device details' listing, or by querying the host information via the 'device info' command.
            - The 'device info' command allows you to selectively enumerate the device information data structure. All data elements and their
                corresponding values are displayed; a value of '{}' indicates that the element is a sub-structure that can be further enumerated
                (see the 'device info' example in the Example section of this output).
        """)
        print_help("Originally this was miranda host command, but REXT already has host command")

    def help_add(self):
        print_help("Allows you to manually add device (e.g. shodan search result)")
        print("\tusage:add [device name] [device xml root]")
        print("\texample: add 192.168.1.2:49152 http://192.168.1.2:49152/description.xml")

    def help_pcap(self):
        print_help("Passively listens for SSDP NOTIFY messages from UPNP devices")

    # Passively listen for UPNP NOTIFY packets
    def do_pcap(self, e):
        print_info('Entering passive mode, Ctrl+C')

        count = 0
        start = time.time()

        while True:
            try:
                if 0 < self.max_hosts <= count:
                    break

                if 0 < self.timeout < (time.time() - start):
                    raise Exception("Timeout exceeded")

                if self.parse_ssdp_info(self.recieve(1024, False), False, False):
                    count += 1

            except Exception as e:
                print("\n")
                print_info("Passive mode halted...")
                break

    def do_msearch(self, e):
        default_st = "upnp:rootdevice"
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
        st = default_st

        # Build the request
        request = "M-SEARCH * HTTP/1.1\r\n" \
                  "HOST:%s:%d\r\n" \
                  "ST:%s\r\n" % (self.host, self.port, st)
        for header, value in self.msearchHeaders.items():
            request += header + ':' + value + "\r\n"
        request += "\r\n"

        print_info("Entering discovery mode for '%s', Ctl+C to stop..." % st)

        # Have to create a new socket since replies will be sent directly to our IP, not the multicast IP
        server = self.create_new_listener(myip, lport)
        if not server:
            print_error('Failed to bind port %d' % lport)
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

                if self.parse_ssdp_info(self.recieve(1024, server), False, False):
                    count += 1

            except AttributeError:  # On Ctrl-C parseSSDPInfo raises AttributeError exception
                print('\n')
                print_info('Discover mode halted...')
                break

    def get_host_info(self, host_info, index):

        if host_info is not None:
            # If this host data is already complete, just display it
            if host_info['dataComplete']:
                print_warning('Data for this host has already been enumerated!')
                return
            try:
                # Get extended device and service information
                if host_info:
                    print_info("Requesting device and service info for " +
                               host_info['name'] + " (this could take a few seconds)...")
                    if not host_info['dataComplete']:
                        (xml_headers, xml_data) = self.get_xml(host_info['xml_file'])
                        # print(xmlHeaders)
                        # print(xmlData)
                        if not xml_data:
                            print_error('Failed to request host XML file:' + host_info['xml_file'])
                            return
                        if not self.get_host_information(xml_data, xml_headers, index):
                            print_error("Failed to get device/service info for " + host_info['name'])
                            return
                    print_success('Host data enumeration complete!')
                    # hp.updateCmdCompleter(hp.ENUM_HOSTS)
                    return
            except KeyboardInterrupt:
                return

    def getUserInput(self, shellPrompt):
        defaultShellPrompt = 'upnp> '

        if shellPrompt == False:
            shellPrompt = defaultShellPrompt

        try:
            uInput = input(shellPrompt).strip()
            argv = uInput.split()
            argc = len(argv)
        except KeyboardInterrupt as e:
            print('\n')
            return 0, None
        return argc, argv

    # Send SOAP request
    def send_soap(self, host_name, service_type, control_url, action_name, action_arguments):
        arg_list = ''
        soap_response = ''

        if '://' in control_url:
            url_array = control_url.split('/', 3)
            if len(url_array) < 4:
                control_url = '/'
            else:
                control_url = '/' + url_array[3]

        soap_request = 'POST %s HTTP/1.1\r\n' % control_url

        # Check if a port number was specified in the host name; default is port 80
        if ':' in host_name:
            host_name_array = host_name.split(':')
            host = host_name_array[0]
            try:
                port = int(host_name_array[1])
            except:
                print_error('Invalid port specified for host connection:', host_name[1])
                return False
        else:
            host = host_name
            port = 80

        # Create a string containing all of the SOAP action's arguments and values
        for arg, (val, dt) in action_arguments.items():
            arg_list += '<%s>%s</%s>' % (arg, val, arg)

        # Create the SOAP request
        soap_body = '<?xml version="1.0"?>\n' \
                    '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' \
                    '<SOAP-ENV:Body>\n' \
                    '\t<m:%s xmlns:m="%s">\n' \
                    '%s\n' \
                    '\t</m:%s>\n' \
                    '</SOAP-ENV:Body>\n' \
                    '</SOAP-ENV:Envelope>' % (action_name, service_type, arg_list, action_name)

        # Specify the headers to send with the request
        headers = {
            'Host': host_name,
            'Content-Length': len(soap_body),
            'Content-Type': 'text/xml',
            'SOAPAction': '"%s#%s"' % (service_type, action_name)
        }

        # Generate the final payload
        for head, value in headers.items():
            soap_request += '%s: %s\r\n' % (head, value)
        soap_request += '\r\n%s' % soap_body

        # Send data and go into recieve loop
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            # DEBUG = 0
            # if DEBUG:
            #     print(soap_request)

            sock.send(bytes(soap_request, 'UTF-8'))
            while True:
                data = sock.recv(self.max_recv)
                if not data:
                    break
                else:
                    soap_response += data.decode('UTF-8')
                    if self.soapEnd.search(soap_response.lower()) is not None:
                        break

            sock.close()
            (header, body) = soap_response.split('\r\n\r\n', 1)
            if not header.upper().startswith('HTTP/1.') and ' 200 ' in header.split('\r\n')[0]:
                print_error('SOAP request failed with error code:', header.split('\r\n')[0].split(' ', 1)[1])
                error_msg = self.extract_single_tag(body, 'errorDescription')
                if error_msg:
                    print_error('SOAP error message:', error_msg)
                return False
            else:
                return body
        except Exception as e:
            print_error('Caught socket exception:')
            traceback.print_tb(e)
            sock.close()
            return False
        except KeyboardInterrupt:
            sock.close()
            return False

    # Extract the contents of a single XML tag from the data
    def extract_single_tag(self, data, tag):
        start_tag = "<%s" % tag
        end_tag = "</%s>" % tag

        try:
            tmp = data.split(start_tag)[1]
            index = tmp.find('>')
            if index != -1:
                index += 1
                return tmp[index:].split(end_tag)[0].strip()
        except:
            pass
        return None

    def do_add(self, e):
        args = e.split(' ')
        if len(args) != 2:
            print_error("Invalid number of arguments")
        else:
            index = len(self.enum_hosts)
            self.enum_hosts[index] = {
                'name': args[0],
                'dataComplete': False,
                'proto': 'http://',
                'xml_file': args[1],
                'serverType': None,
                'upnpServer': None,
                'deviceList': {}
            }

    def do_device(self, e):  # This was originally host command but since REXT uses host on something else...
        # host_info = None
        args = e.split(' ')
        if args[0] == "get":
            if len(args) != 2:
                print_error("Invalid number of arguments")
                return
            try:
                index = int(args[1])
                host_info = self.enum_hosts[index]
            except Exception:
                print_error("Second argument is not a number")
                return
            self.get_host_info(host_info, index)
        elif args[0] == "details":
            try:
                index = int(args[1])
                host_info = self.enum_hosts[index]
            except Exception as e:
                print_error("Index error")
                return

            try:
                # If this host data is already complete, just display it
                if host_info['dataComplete']:
                    self.show_complete_host_info(index)
                else:
                    print_error("Can't show host info because I don't have it. Please run 'host get %d'" % index)
            except KeyboardInterrupt as e:
                pass
            return
        elif args[0] == "list":
            if len(self.enum_hosts) == 0:
                print_info("No known hosts - try running the 'msearch' or 'pcap' commands")
                return
            for index, host_info in self.enum_hosts.items():
                print_info("[%d] %s" % (index, host_info['name']))
            return
        elif args[0] == "summary":
            try:
                index = int(args[1])
                host_info = self.enum_hosts[index]
            except:
                print_error("Please provide correct device id")
                return

            print('Host:', host_info['name'])
            print('XML File:', host_info['xml_file'])
            for device_name, deviceData in host_info['deviceList'].items():
                print(device_name)
                for k, v in deviceData.items():
                    if isinstance(v, dict):
                        continue
                    else:
                        print("\t%s: %s" % (k, v))
                        # try:
                        # v.has_key(False) # Has key removed in python3
                        # except:
                        #    print("\t%s: %s" % (k,v))
            print('')
            return
        elif args[0] == 'info':
            output = self.enum_hosts
            data_structs = []
            for arg in args[1:]:
                try:
                    arg = int(arg)
                except:
                    pass
                output = output[arg]
            try:
                for k, v in output.items():
                    if isinstance(v, dict):
                        data_structs.append(k)
                    else:
                        print(k, ':', v)
                        continue
                        # try:
                        #     v.has_key(False)
                        #     dataStructs.append(k)
                        # except:
                        #     print(k,':',v)
                        #     continue
            except:
                print(output)

            for struct in data_structs:
                print(struct, ': {}')
            return
        elif args[0] == 'send':
            # Send SOAP requests
            # index = False
            in_arg_counter = 0

            if len(args) != 5:
                # showHelp(argv[0])
                return
            else:
                try:
                    index = int(args[1])
                    host_info = self.enum_hosts[index]
                except:
                    print('indexError')
                    return
                device_name = args[2]
                service_name = args[3]
                action_name = args[4]
                # action_args = False
                send_args = {}
                ret_tags = []
                # controlURL = False
                # full_service_name = False

                # Get the service control URL and full service name
                try:
                    control_url = host_info['proto'] + host_info['name']
                    control_url2 = host_info['deviceList'][device_name]['services'][service_name]['controlURL']
                    if not control_url.endswith('/') and not control_url2.startswith('/'):
                        control_url += '/'
                    control_url += control_url2
                except Exception as e:
                    print('Caught exception:')
                    traceback.print_tb(e)
                    print("Are you sure you've run 'host get %d' and specified the correct service name?" % index)
                    return False

                # Get action info
                try:
                    action_args = \
                    host_info['deviceList'][device_name]['services'][service_name]['actions'][action_name][
                        'arguments']
                    full_service_name = host_info['deviceList'][device_name]['services'][service_name]['fullName']
                except Exception as e:
                    print('Caught exception:')
                    traceback.print_tb(e)
                    print("Are you sure you've specified the correct action?")
                    return False

                for argName, argVals in action_args.items():
                    action_state_var = argVals['relatedStateVariable']
                    state_var = host_info['deviceList'][device_name]['services'][service_name]['serviceStateVariables'][
                        action_state_var]

                    if argVals['direction'].lower() == 'in':
                        print_info("Required argument:")
                        print("\tArgument Name: ", argName)
                        print("\tData Type:     ", state_var['dataType'])
                        if 'allowedValueList' in state_var:
                            print("\tAllowed Values:", state_var['allowedValueList'])
                        if 'allowedValueRange' in state_var:
                            print("\tValue Min:     ", state_var['allowedValueRange'][0])
                            print("\tValue Max:     ", state_var['allowedValueRange'][1])
                        if 'defaultValue' in state_var:
                            print("\tDefault Value: ", state_var['defaultValue'])
                        prompt = "\tSet %s value to: " % argName
                        try:
                            # Get user input for the argument value
                            (argc, argv) = self.getUserInput(prompt)
                            if argv is None:
                                print_warning('Stopping send request...')
                                return
                            u_input = ''

                            if argc > 0:
                                in_arg_counter += 1

                            for val in argv:
                                u_input += val + ' '

                            u_input = u_input.strip()
                            if state_var['dataType'] == 'bin.base64' and u_input:
                                u_input = base64.encodebytes(bytes(u_input, 'UTF-8'))

                            send_args[argName] = (u_input.strip(), state_var['dataType'])
                        except KeyboardInterrupt:
                            print("")
                            return
                        print('')
                    else:
                        ret_tags.append((argName, state_var['dataType']))

                # Remove the above inputs from the command history
                # while inArgCounter:
                #     try:
                #         readline.remove_history_item(readline.get_current_history_length() - 1)
                #     except:
                #         pass
                #
                #     inArgCounter -= 1

                # print 'Requesting',controlURL
                soap_response = self.send_soap(host_info['name'], full_service_name, control_url, action_name,
                                               send_args)
                if soap_response:
                    # It's easier to just parse this ourselves...
                    for (tag, dataType) in ret_tags:
                        tag_value = self.extract_single_tag(soap_response, tag)
                        if dataType == 'bin.base64' and tag_value is not None:
                            # print(tagValue)
                            tag_value = base64.decodebytes(bytes(tag_value, 'UTF-8'))
                        print(tag, ':', tag_value)
            return

    # Creates dictionary structure from host_enum data if data enumeration was completed
    def parse_device_autocomplete(self, index):
        autocomplete_structure = {}
        host = self.enum_hosts[index]
        if host['dataComplete']:
            try:
                for device, deviceData in host['deviceList'].items():
                    autocomplete_structure[device] = {}
                    for service, serviceData in deviceData['services'].items():
                        autocomplete_structure[device][service] = {}
                        for action, actionData in serviceData['actions'].items():
                            autocomplete_structure[device][service][action] = []
            except KeyError:
                print_error("Error in autocomplete")
        return autocomplete_structure

    def complete_device(self, text, line, begidx, endidx):
        number_of_hosts = range(len(self.enum_hosts))
        complete_dict = {'get': number_of_hosts, 'info': number_of_hosts,
                   'summarny': number_of_hosts, 'list': [],
                   'details': number_of_hosts, 'send': number_of_hosts}

        # Trick for finding integers in string
        # Maybe I should also check if send command is actually present
        # but index of device is always last argument in command except send command
        index = [int(s) for s in line.split() if s.isdigit()]
        if index:
            complete_dict['send'] = {index[0]: self.parse_device_autocomplete(index[0])}
        complete_array = interface.utils.dict_to_str(complete_dict)
        complete_line = line.partition(' ')[2]
        igon = len(complete_line) - len(text)
        return [s[igon:] for s in complete_array if s.startswith(complete_line)]

Upnp()
