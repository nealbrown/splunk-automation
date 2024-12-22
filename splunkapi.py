import os, sys, getpass, requests, json
from jsonargparse import ArgumentParser
from xml.dom import minidom
from pprint import pprint
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def main():
    # Main parser
    parser = ArgumentParser(prog="splunkapi",
    env_prefix="SPLUNK", default_env=True,
    description="Splunk API interface using jsonargparse",
    default_config_files=['splunkapi.yaml'],  # Specify default config file
    )
    # We need individual subcommand parsers here for specific arguments
    parser_get_serverclasses    = ArgumentParser()
    parser_get_deploymentapps   = ArgumentParser()

    # export SPLUNKAPI_CREATE_SERVERCLASS_SERVERCLASS=name # to set subcommand argument
    parser_create_serverclass   = ArgumentParser(env_prefix="SPLUNK", default_env=True)
    parser_create_serverclass.add_argument("--serverclass", type=str, help='Serverclass to Add')

    # Main parser global args
    parser.add_argument("--host", type=str, help='Splunk Host Name or IP', default="localhost")
    parser.add_argument("--user", type=str, help='Splunk Username', default="admin")
    parser.add_argument("--password", type=str, help='Splunk Password')
    
    # Add all subcommands, include their parsers
    subcommands = parser.add_subcommands()
    subcommands.add_subcommand("create_serverclass", parser_create_serverclass)
    subcommands.add_subcommand("get_serverclasses", parser_get_serverclasses)
    subcommands.add_subcommand("get_deploymentapps", parser_get_deploymentapps)

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
    # Always start by retrieving the session key
    get_session_key(args)
    # Map input to function name safely
    func = globals()[ args.subcommand ]
    func(args,session_key)

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

def get_deploymentapps(args, sessionkey):
    # Output Existing DeploymentApps
    r = requests.get("https://" + args.host + ":8089" + "/services/deployment/server/applications",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    pprint("Applications: " + r.text)

def create_serverclass(args, sessionkey):
    # Create a New Serverclass using subcommand args
    r = requests.post("https://" + args.host + ":8089" + "/services/deployment/server/serverclasses",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"name": args.create_serverclass.serverclass}, verify=False)
    pprint("New Serverclass: " + r.text)

def add_serverclass_to_app(args, sessionkey):
    # Add Serverclass to App
    r = requests.post("https://" + args.host + ":8089" + "/servicesNS/nobody/system/deployment/server/applications/Splunk_TA_nix",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"serverclass": "Splunk_TA_nix"}, verify=False)
    pprint("App Added: " + r.text)

def reload_deploymentserver(args, sessionkey):
    # Reload Deployment Server
    r = requests.post("https://" + args.host + ":8089" + "/services/deployment/server/config/_reload",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    pprint("Deployment Server Reloaded: " + r.text)

def add_host_to_serverclass(args, sessionkey):
    # Add host(s) to Serverclass, note this endpoint can change, TODO pull this from the output above
    # /servicesNS/nobody/search/deployment/server/serverclasses/Splunk_TA_nix
    # /servicesNS/nobody/system/deployment/server/serverclasses/Splunk_TA_nix
    r = requests.post("https://" + args.host + ":8089" + "/servicesNS/nobody/search/deployment/server/serverclasses/Splunk_TA_nix",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"whitelist.0": "splunk-hf-*"}, verify=False)
    pprint("Add Host: " + r.text)

if __name__ == '__main__':
    main()