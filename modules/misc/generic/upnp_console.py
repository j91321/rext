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
import base64
import socket
import re
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
                        # print(xmlHeaders)
                        # print(xmlData)
                        if not xmlData:
                            print_red('Failed to request host XML file:' + host_info['xml_file'])
                            return
                        if self.getHostInfo(xmlData, xmlHeaders, index) == False:
                            print_error("Failed to get device/service info for " + host_info['name'])
                            return
                    print('Host data enumeration complete!')
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
    def sendSOAP(self, hostName, serviceType, controlURL, actionName, actionArguments):
        argList = ''
        soapResponse = ''

        if '://' in controlURL:
            urlArray = controlURL.split('/', 3)
            if len(urlArray) < 4:
                controlURL = '/'
            else:
                controlURL = '/' + urlArray[3]

        soapRequest = 'POST %s HTTP/1.1\r\n' % controlURL

        # Check if a port number was specified in the host name; default is port 80
        if ':' in hostName:
            hostNameArray = hostName.split(':')
            host = hostNameArray[0]
            try:
                port = int(hostNameArray[1])
            except:
                print('Invalid port specified for host connection:', hostName[1])
                return False
        else:
            host = hostName
            port = 80

        # Create a string containing all of the SOAP action's arguments and values
        for arg, (val, dt) in actionArguments.items():
            argList += '<%s>%s</%s>' % (arg, val, arg)

        # Create the SOAP request
        soapBody = '<?xml version="1.0"?>\n' \
                   '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' \
                   '<SOAP-ENV:Body>\n' \
                   '\t<m:%s xmlns:m="%s">\n' \
                   '%s\n' \
                   '\t</m:%s>\n' \
                   '</SOAP-ENV:Body>\n' \
                   '</SOAP-ENV:Envelope>' % (actionName, serviceType, argList, actionName)

        # Specify the headers to send with the request
        headers = {
            'Host': hostName,
            'Content-Length': len(soapBody),
            'Content-Type': 'text/xml',
            'SOAPAction': '"%s#%s"' % (serviceType, actionName)
        }

        # Generate the final payload
        for head, value in headers.items():
            soapRequest += '%s: %s\r\n' % (head, value)
        soapRequest += '\r\n%s' % soapBody

        # Send data and go into recieve loop
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            DEBUG = 0
            if DEBUG:
                print(soapRequest)

            sock.send(bytes(soapRequest, 'UTF-8'))
            while True:
                data = sock.recv(self.max_recv)
                if not data:
                    break
                else:
                    soapResponse += data.decode('UTF-8')
                    if self.soapEnd.search(soapResponse.lower()) != None:
                        break

            sock.close()
            (header, body) = soapResponse.split('\r\n\r\n', 1)
            if not header.upper().startswith('HTTP/1.') and ' 200 ' in header.split('\r\n')[0]:
                print('SOAP request failed with error code:', header.split('\r\n')[0].split(' ', 1)[1])
                errorMsg = self.extractSingleTag(body, 'errorDescription')
                if errorMsg:
                    print('SOAP error message:', errorMsg)
                return False
            else:
                return body
        except Exception as e:
            print('Caught socket exception:')
            traceback.print_tb(e)
            sock.close()
            return False
        except KeyboardInterrupt:
            sock.close()
            return False

    # Extract the contents of a single XML tag from the data
    def extractSingleTag(self, data, tag):
        startTag = "<%s" % tag
        endTag = "</%s>" % tag

        try:
            tmp = data.split(startTag)[1]
            index = tmp.find('>')
            if index != -1:
                index += 1
                return tmp[index:].split(endTag)[0].strip()
        except:
            pass
        return None

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
        elif args[0] == "details":
            try:
                index = int(args[1])
                hostInfo = self.enum_hosts[index]
            except Exception as e:
                print("Index error")
                return

            try:
                # If this host data is already complete, just display it
                if hostInfo['dataComplete'] == True:
                    self.showCompleteHostInfo(index, False)
                else:
                    print("Can't show host info because I don't have it. Please run 'host get %d'" % index)
            except KeyboardInterrupt as e:
                pass
            return
        elif args[0] == "list":
            if len(self.enum_hosts) == 0:
                print("No known hosts - try running the 'msearch' or 'pcap' commands")
                return
            for index, hostInfo in self.enum_hosts.items():
                print("\t[%d] %s" % (index, hostInfo['name']))
            return
        elif args[0] == "summary":
            try:
                index = int(args[1])
                hostInfo = self.enum_hosts[index]
            except:
                print("Index error")
                return

            print('Host:', hostInfo['name'])
            print('XML File:', hostInfo['xml_file'])
            for deviceName, deviceData in hostInfo['deviceList'].items():
                print(deviceName)
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
            dataStructs = []
            for arg in args[1:]:
                try:
                    arg = int(arg)
                except:
                    pass
                output = output[arg]
            try:
                for k, v in output.items():
                    if isinstance(v, dict):
                        dataStructs.append(k)
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

            for struct in dataStructs:
                print(struct, ': {}')
            return
        elif args[0] == 'send':
            # Send SOAP requests
            index = False
            inArgCounter = 0

            if len(args) != 5:
                # showHelp(argv[0])
                return
            else:
                try:
                    index = int(args[1])
                    hostInfo = self.enum_hosts[index]
                except:
                    print('indexError')
                    return
                deviceName = args[2]
                serviceName = args[3]
                actionName = args[4]
                actionArgs = False
                sendArgs = {}
                retTags = []
                controlURL = False
                fullServiceName = False

                # Get the service control URL and full service name
                try:
                    controlURL = hostInfo['proto'] + hostInfo['name']
                    controlURL2 = hostInfo['deviceList'][deviceName]['services'][serviceName]['controlURL']
                    if not controlURL.endswith('/') and not controlURL2.startswith('/'):
                        controlURL += '/'
                    controlURL += controlURL2
                except Exception as e:
                    print('Caught exception:')
                    traceback.print_tb(e)
                    print("Are you sure you've run 'host get %d' and specified the correct service name?" % index)
                    return False

                # Get action info
                try:
                    actionArgs = hostInfo['deviceList'][deviceName]['services'][serviceName]['actions'][actionName][
                        'arguments']
                    fullServiceName = hostInfo['deviceList'][deviceName]['services'][serviceName]['fullName']
                except Exception as e:
                    print('Caught exception:')
                    traceback.print_tb(e)
                    print("Are you sure you've specified the correct action?")
                    return False

                for argName, argVals in actionArgs.items():
                    actionStateVar = argVals['relatedStateVariable']
                    stateVar = hostInfo['deviceList'][deviceName]['services'][serviceName]['serviceStateVariables'][
                        actionStateVar]

                    if argVals['direction'].lower() == 'in':
                        print("Required argument:")
                        print("\tArgument Name: ", argName)
                        print("\tData Type:     ", stateVar['dataType'])
                        if 'allowedValueList' in stateVar:
                            print("\tAllowed Values:", stateVar['allowedValueList'])
                        if 'allowedValueRange' in stateVar:
                            print("\tValue Min:     ", stateVar['allowedValueRange'][0])
                            print("\tValue Max:     ", stateVar['allowedValueRange'][1])
                        if 'defaultValue' in stateVar:
                            print("\tDefault Value: ", stateVar['defaultValue'])
                        prompt = "\tSet %s value to: " % argName
                        try:
                            # Get user input for the argument value
                            (argc, argv) = self.getUserInput(prompt)
                            if argv is None:
                                print('Stopping send request...')
                                return
                            uInput = ''

                            if argc > 0:
                                inArgCounter += 1

                            for val in argv:
                                uInput += val + ' '

                            uInput = uInput.strip()
                            if stateVar['dataType'] == 'bin.base64' and uInput:
                                uInput = base64.encodebytes(bytes(uInput, 'UTF-8'))

                            sendArgs[argName] = (uInput.strip(), stateVar['dataType'])
                        except KeyboardInterrupt:
                            print("")
                            return
                        print('')
                    else:
                        retTags.append((argName, stateVar['dataType']))

                # Remove the above inputs from the command history
                # while inArgCounter:
                #     try:
                #         readline.remove_history_item(readline.get_current_history_length() - 1)
                #     except:
                #         pass
                #
                #     inArgCounter -= 1

                # print 'Requesting',controlURL
                soapResponse = self.sendSOAP(hostInfo['name'], fullServiceName, controlURL, actionName, sendArgs)
                if soapResponse != False:
                    # It's easier to just parse this ourselves...
                    for (tag, dataType) in retTags:
                        tagValue = self.extractSingleTag(soapResponse, tag)
                        if dataType == 'bin.base64' and tagValue is not None:
                            #print(tagValue)
                            tagValue = base64.decodebytes(bytes(tagValue, 'UTF-8'))
                        print(tag, ':', tagValue)
            return


Upnp()
