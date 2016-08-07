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
import xml.dom.minidom
import time
import traceback
import sys

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

        #Pull the name of the device type from a device type string
    #The device type string looks like: 'urn:schemas-upnp-org:device:WANDevice:1'
    def parseDeviceTypeName(self,string):
        delim1 = 'device:'
        delim2 = ':'

        if delim1 in string and not string.endswith(delim1):
            return string.split(delim1)[1].split(delim2,1)[0]
        return False

    #Pull the name of the service type from a service type string
    #The service type string looks like: 'urn:schemas-upnp-org:service:Layer3Forwarding:1'
    def parseServiceTypeName(self,string):
        delim1 = 'service:'
        delim2 = ':'

        if delim1 in string and not string.endswith(delim1):
            return string.split(delim1)[1].split(delim2,1)[0]
        return False

    #Get info about a service's state variables
    def parseServiceStateVars(self,xmlRoot,servicePointer):

        na = 'N/A'
        varVals = ['sendEvents','dataType','defaultValue','allowedValues']
        serviceStateTable = 'serviceStateTable'
        stateVariable = 'stateVariable'
        nameTag = 'name'
        dataType = 'dataType'
        sendEvents = 'sendEvents'
        allowedValueList = 'allowedValueList'
        allowedValue = 'allowedValue'
        allowedValueRange = 'allowedValueRange'
        minimum = 'minimum'
        maximum = 'maximum'

        #Create the serviceStateVariables entry for this service in ENUM_HOSTS
        servicePointer['serviceStateVariables'] = {}

        #Get a list of all state variables associated with this service
        try:
            stateVars = xmlRoot.getElementsByTagName(serviceStateTable)[0].getElementsByTagName(stateVariable)
        except:
            #Don't necessarily want to throw an error here, as there may be no service state variables
            return False

        #Loop through all state variables
        for var in stateVars:
            for tag in varVals:
                #Get variable name
                try:
                    varName = str(var.getElementsByTagName(nameTag)[0].childNodes[0].data)
                except:
                    print('Failed to get service state variable name for service %s!' % servicePointer['fullName'])
                    continue

                servicePointer['serviceStateVariables'][varName] = {}
                try:
                    servicePointer['serviceStateVariables'][varName]['dataType'] = str(var.getElementsByTagName(dataType)[0].childNodes[0].data)
                except:
                    servicePointer['serviceStateVariables'][varName]['dataType'] = na
                try:
                    servicePointer['serviceStateVariables'][varName]['sendEvents'] = str(var.getElementsByTagName(sendEvents)[0].childNodes[0].data)
                except:
                    servicePointer['serviceStateVariables'][varName]['sendEvents'] = na

                servicePointer['serviceStateVariables'][varName][allowedValueList] = []

                #Get a list of allowed values for this variable
                try:
                    vals = var.getElementsByTagName(allowedValueList)[0].getElementsByTagName(allowedValue)
                except:
                    pass
                else:
                    #Add the list of allowed values to the ENUM_HOSTS dictionary
                    for val in vals:
                        servicePointer['serviceStateVariables'][varName][allowedValueList].append(str(val.childNodes[0].data))

                #Get allowed value range for this variable
                try:
                    valList = var.getElementsByTagName(allowedValueRange)[0]
                except:
                    pass
                else:
                    #Add the max and min values to the ENUM_HOSTS dictionary
                    servicePointer['serviceStateVariables'][varName][allowedValueRange] = []
                    try:
                        servicePointer['serviceStateVariables'][varName][allowedValueRange].append(str(valList.getElementsByTagName(minimum)[0].childNodes[0].data))
                        servicePointer['serviceStateVariables'][varName][allowedValueRange].append(str(valList.getElementsByTagName(maximum)[0].childNodes[0].data))
                    except:
                        pass
        return True

    #Parse details about each service (arguements, variables, etc)
    def parseServiceInfo(self,service,index):
        argIndex = 0
        argTags = ['direction','relatedStateVariable']
        actionList = 'actionList'
        actionTag = 'action'
        nameTag = 'name'
        argumentList = 'argumentList'
        argumentTag = 'argument'

        #Get the full path to the service's XML file
        xmlFile = self.enum_hosts[index]['proto'] + self.enum_hosts[index]['name']
        if not xmlFile.endswith('/') and not service['SCPDURL'].startswith('/'):
            try:
                xmlServiceFile = self.enum_hosts[index]['xml_file']
                slashIndex = xmlServiceFile.rfind('/')
                xmlFile = xmlServiceFile[:slashIndex] + '/'
            except:
                xmlFile += '/'

        if self.enum_hosts[index]['proto'] in service['SCPDURL']:
            xmlFile = service['SCPDURL']
        else:
            xmlFile += service['SCPDURL']
        service['actions'] = {}

        #Get the XML file that describes this service
        (xmlHeaders,xmlData) = self.get_xml(xmlFile)
        if not xmlData:
            print('Failed to retrieve service descriptor located at:',xmlFile)
            return False

        try:
            xmlRoot = xml.dom.minidom.parseString(xmlData)

            #Get a list of actions for this service
            try:
                actionList = xmlRoot.getElementsByTagName(actionList)[0]
            except:
                print('Failed to retrieve action list for service %s!' % service['fullName'])
                return False
            actions = actionList.getElementsByTagName(actionTag)
            if actions == []:
                return False

            #Parse all actions in the service's action list
            for action in actions:
                #Get the action's name
                try:
                    actionName = str(action.getElementsByTagName(nameTag)[0].childNodes[0].data).strip()
                except:
                    print('Failed to obtain service action name (%s)!' % service['fullName'])
                    continue

                #Add the action to the ENUM_HOSTS dictonary
                service['actions'][actionName] = {}
                service['actions'][actionName]['arguments'] = {}

                #Parse all of the action's arguments
                try:
                    argList = action.getElementsByTagName(argumentList)[0]
                except:
                    #Some actions may take no arguments, so continue without raising an error here...
                    continue

                #Get all the arguments in this action's argument list
                arguments = argList.getElementsByTagName(argumentTag)
                if arguments == []:
                    if self.verbose:
                        print('Action',actionName,'has no arguments!')
                    continue

                #Loop through the action's arguments, appending them to the ENUM_HOSTS dictionary
                for argument in arguments:
                    try:
                        argName = str(argument.getElementsByTagName(nameTag)[0].childNodes[0].data)
                    except:
                        print('Failed to get argument name for',actionName)
                        continue
                    service['actions'][actionName]['arguments'][argName] = {}

                    #Get each required argument tag value and add them to ENUM_HOSTS
                    for tag in argTags:
                        try:
                            service['actions'][actionName]['arguments'][argName][tag] = str(argument.getElementsByTagName(tag)[0].childNodes[0].data)
                        except:
                            print('Failed to find tag %s for argument %s!' % (tag,argName))
                            continue

            #Parse all of the state variables for this service
            self.parseServiceStateVars(xmlRoot,service)

        except Exception as e:
            print('Caught exception while parsing Service info for service %s: %s' % (service['fullName'],str(e)))
            return False

        return True

    #Parse the list of services specified in the XML file
    def parseServiceList(self,xmlRoot,device,index):
        serviceEntryPointer = False
        dictName = "services"
        serviceListTag = "serviceList"
        serviceTag = "service"
        serviceNameTag = "serviceType"
        serviceTags = ["serviceId","controlURL","eventSubURL","SCPDURL"]

        try:
            device[dictName] = {}
            #Get a list of all services offered by this device
            for service in xmlRoot.getElementsByTagName(serviceListTag)[0].getElementsByTagName(serviceTag):
                #Get the full service descriptor
                serviceName = str(service.getElementsByTagName(serviceNameTag)[0].childNodes[0].data)

                #Get the service name from the service descriptor string
                serviceDisplayName = self.parseServiceTypeName(serviceName)
                if not serviceDisplayName:
                    continue

                #Create new service entry for the device in ENUM_HOSTS
                serviceEntryPointer = device[dictName][serviceDisplayName] = {}
                serviceEntryPointer['fullName'] = serviceName

                #Get all of the required service info and add it to ENUM_HOSTS
                for tag in serviceTags:
                    serviceEntryPointer[tag] = str(service.getElementsByTagName(tag)[0].childNodes[0].data)

                #Get specific service info about this service
                self.parseServiceInfo(serviceEntryPointer,index)
        except Exception as e:
            print('Caught exception while parsing device service list:', e)

    # Parse device info from the retrieved XML file
    def parseDeviceInfo(self, xmlRoot,index):
        deviceEntryPointer = False
        devTag = "device"
        deviceType = "deviceType"
        deviceListEntries = "deviceList"
        deviceTags = ["friendlyName","modelDescription","modelName","modelNumber","modelURL","presentationURL","UDN","UPC","manufacturer","manufacturerURL"]

        #Find all device entries listed in the XML file
        for device in xmlRoot.getElementsByTagName(devTag):
            try:
                #Get the deviceType string
                deviceTypeName = str(device.getElementsByTagName(deviceType)[0].childNodes[0].data)
            except:
                continue

            #Pull out the action device name from the deviceType string
            deviceDisplayName = self.parseDeviceTypeName(deviceTypeName)
            if not deviceDisplayName:
                continue

            #Create a new device entry for this host in the ENUM_HOSTS structure
            deviceEntryPointer = self.enum_hosts[index][deviceListEntries][deviceDisplayName] = {}
            deviceEntryPointer['fullName'] = deviceTypeName

            #Parse out all the device tags for that device
            for tag in deviceTags:
                try:
                    deviceEntryPointer[tag] = str(device.getElementsByTagName(tag)[0].childNodes[0].data)
                except Exception as e:
                    if self.verbose:
                        print('Device',deviceEntryPointer['fullName'],'does not have a', tag)
                    continue
            #Get a list of all services for this device listing
            self.parseServiceList(device,deviceEntryPointer,index)

        return

#Display all info for a given host
    def showCompleteHostInfo(self,index,fp):
        na = 'N/A'
        serviceKeys = ['controlURL','eventSubURL','serviceId','SCPDURL','fullName']
        if fp == False:
            fp = sys.stdout

        if index < 0 or index >= len(self.enum_hosts):
            fp.write('Specified host does not exist...\n')
            return
        try:
            hostInfo = self.enum_hosts[index]
            if hostInfo['dataComplete'] == False:
                print("Cannot show all host info because I don't have it all yet. Try running 'host info %d' first...\n" % index)
            fp.write('Host name:         %s\n' % hostInfo['name'])
            fp.write('UPNP XML File:     %s\n\n' % hostInfo['xml_file'])

            fp.write('\nDevice information:\n')
            for deviceName,deviceStruct in hostInfo['deviceList'].items():
                fp.write('\tDevice Name: %s\n' % deviceName)
                for serviceName,serviceStruct in deviceStruct['services'].items():
                    fp.write('\t\tService Name: %s\n' % serviceName)
                    for key in serviceKeys:
                        fp.write('\t\t\t%s: %s\n' % (key,serviceStruct[key]))
                    fp.write('\t\t\tServiceActions:\n')
                    for actionName,actionStruct in serviceStruct['actions'].items():
                        fp.write('\t\t\t\t%s\n' % actionName)
                        for argName,argStruct in actionStruct['arguments'].items():
                            fp.write('\t\t\t\t\t%s \n' % argName)
                            for key,val in argStruct.items():
                                if key == 'relatedStateVariable':
                                    fp.write('\t\t\t\t\t\t%s:\n' % val)
                                    for k,v in serviceStruct['serviceStateVariables'][val].items():
                                        fp.write('\t\t\t\t\t\t\t%s: %s\n' % (k,v))
                                else:
                                    fp.write('\t\t\t\t\t\t%s: %s\n' % (key,val))

        except Exception as e:
            print('Caught exception while showing host info:')
            traceback.print_stack(e)

        # Wrapper function...
    def getHostInfo(self, xmlData, xmlHeaders, index):
        if self.enum_hosts[index]['dataComplete']:
            return

        if 0 <= index < len(self.enum_hosts):
            try:
                xmlRoot = xml.dom.minidom.parseString(xmlData)
                self.parseDeviceInfo(xmlRoot, index)
                #self.enum_hosts[index]['serverType'] = xmlHeaders.getheader('Server')
                self.enum_hosts[index]['serverType'] = xmlHeaders['Server']
                self.enum_hosts[index]['dataComplete'] = True
                return True
            except Exception as e:
                print('Caught exception while getting host info:')
                traceback.print_stack(e)
        return False

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
