import os, sys, configargparse, getpass, requests, json
from xml.dom import minidom
from pprint import pprint
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def main():
    parser = configargparse.ArgumentParser(
    description="Splunklib interface using configargparse",
    default_config_files=['splunkapi.ini'],  # Specify default config file
    )

    parser.add_argument('--host', env_var='SPLUNK_HOST', type=str, help='Splunk Host Name or IP', default="localhost")
    parser.add_argument('--user', env_var='SPLUNK_USER', type=str, help='Splunk Username', default="admin")
    parser.add_argument('--password', env_var='SPLUNK_PASS', type=str, help='Splunk Password')

    args = parser.parse_args()

    # Since there is a default host, in order to prompt interactively use e.g. python splunkapi.py --host ''
    if not args.host:
        print('Splunk host not set.')
        args.host = input("Please enter hostname or IP of Splunk Host: ")
    if not args.user:
        print('Splunk user not set.')
        args.user = input("Please enter admin username: ")
    if not args.password:
        print('Splunk password not set.')
        args.password = getpass.getpass('Please enter admin password, will not be echoed: ')
    
    get_session_key(args)
    get_serverclasses(args, session_key)
    return args
   
def get_session_key(args):
    # First we login with user/pass and get a session key then append that header to all following requests
    r = requests.get("https://" + args.host + ":8089" + "/services/auth/login",
        data={'username':args.user,'password':args.password}, verify=False)
    global session_key 
    session_key = minidom.parseString(r.text).getElementsByTagName('sessionKey')[0].firstChild.nodeValue
    return session_key

def get_serverclasses(args, sessionkey):
    # Output Existing Serverclasses
    r = requests.get("https://" + args.host + ":8089" + "/services/deployment/server/serverclasses",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    pprint("Serverclasses: " + r.text)

def get_deploymentapps():
    # Output Existing DeploymentApps
    r = requests.get("https://" + args.host + ":8089" + "/services/deployment/server/applications",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    pprint("Applications: " + r.text)

def create_serverclass():
    # Create a New Serverclass
    r = requests.post("https://" + args.host + ":8089" + "/services/deployment/server/serverclasses",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"name": "Splunk_TA_nix"}, verify=False)
    pprint("New Serverclass: " + r.text)

def add_serverclass_to_app():
    # Add Serverclass to App
    r = requests.post("https://" + args.host + ":8089" + "/servicesNS/nobody/system/deployment/server/applications/Splunk_TA_nix",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"serverclass": "Splunk_TA_nix"}, verify=False)
    pprint("App Added: " + r.text)

def reload_deploymentserver():
    # Reload Deployment Server
    r = requests.post("https://" + args.host + ":8089" + "/services/deployment/server/config/_reload",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    pprint("Deployment Server Reloaded: " + r.text)

def add_host_to_serverclass():
    # Add host(s) to Serverclass, note this endpoint can change, TODO pull this from the output above
    # /servicesNS/nobody/search/deployment/server/serverclasses/Splunk_TA_nix
    # /servicesNS/nobody/system/deployment/server/serverclasses/Splunk_TA_nix
    r = requests.post("https://" + args.host + ":8089" + "/servicesNS/nobody/search/deployment/server/serverclasses/Splunk_TA_nix",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"whitelist.0": "splunk-hf-*"}, verify=False)
    pprint("Add Host: " + r.text)

if __name__ == '__main__':
    main()