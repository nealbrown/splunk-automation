# export SPLUNK_PASSWORD=changeme
# To add or manage individual apps or serverclasses call the subcommand with its required flags
# 
# To populate a deployment server first ensure the inventory in config/splunkapps.toml is complete 
# and that the app tgz's are present on the path specified
# 
# Install the apps via the accompanying fabfile
# then run
# python main.py serverclass create-all-serverclasses
# python main.py deploymentapps add-all-serverclasses-to-app
# 
# To update allowlists for existing serverclasses use
# python main.py serverclass add-hosts-to-serverclasses

import typer, requests, config, json, datetime
from rich import print
from xml.dom import minidom
from typing_extensions import Annotated
from config import splunkapps as apps
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Create Typers for each function
# Use pretty_exceptions_show_locals=False to avoid printing password in exceptions
app = typer.Typer(pretty_exceptions_show_locals=False)
reload_deploymentserver_app   = typer.Typer(pretty_exceptions_show_locals=False, help="Reload deployment server.")
serverclass_app               = typer.Typer(pretty_exceptions_show_locals=False, help="Retrieve and manage serverclasses.")
deploymentapps_app            = typer.Typer(pretty_exceptions_show_locals=False, help="Manage deploymentapps.")
app.add_typer(serverclass_app, name="serverclass")
app.add_typer(deploymentapps_app, name="deploymentapps")
app.add_typer(reload_deploymentserver_app, name="reload_deploymentserver")

# Defaults will be used if ENV VAR not set, except for password which has no default
default_splunk_host     = "splunk"      # SPLUNK_HOST
default_splunk_user     = "admin"       # SPLUNK_USER
default_splunk_debug    = False         # SPLUNK_DEBUG

# No ENV VAR support
default_allow_list      = "whitelist.0"

# Note that instead of using typing.List we expect singular arguments unless we are pulling from the toml config file

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    password: Annotated[
        str,typer.Option(envvar="SPLUNK_PASSWORD", prompt="SPLUNK_PASSWORD not set, enter admin password", hide_input=True)
        ],
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host, 
    user: Annotated[
        str, typer.Option(envvar="SPLUNK_USER")] = default_splunk_user, 
    debug: Annotated[
        bool, typer.Option(envvar="SPLUNK_DEBUG")] = default_splunk_debug, 
    ):
    """
    Callback to retrieve and return a sessionkey to use for API auth prior to running a subcommand.
    Then each subcommand can operate on applications or serverclasses as specified in their individual descriptions.

    Required: --host (has default) --user (has default) and --password (no default, will prompt).
    All can be set via ENV VAR (preferred)

    We keep the subcommands in the same process so they can reference the global variable.
    """
    r = requests.get("https://" + host + ":8089" + "/services/auth/login",
        data={'username':user,'password':password}, verify=False)
    global session_key
    session_key = minidom.parseString(r.text).getElementsByTagName('sessionKey')[0].firstChild.nodeValue
    if session_key:
        if debug:
            print(f"Debug Output: Successfully retrieved api auth sessionkey: {session_key}") 
    else:
        raise typer.Exit(code=1)
    if ctx.invoked_subcommand is None:
        print("No further command specified. Session key will expire in 60 minutes.")

@reload_deploymentserver_app.command()
def reload_deploymentserver(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host, 
    ):
    """
    Reload Deployment Server- not necessary in most cases because the API call itself will trigger a reload.

    Turned out the response doesn't even contain the config refresh time just the current time.
    """
    r = requests.post("https://" + host + ":8089" + "/services/deployment/server/config/_reload",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    dom = minidom.parseString(r.text) 
    keys = dom.getElementsByTagName('s:key')
    for n in keys:
        if n.getAttribute('name') == 'loadTime':
            loadTime = int(n.childNodes[0].nodeValue)
            epoch_date_time = str(datetime.datetime.fromtimestamp(loadTime))
            print("Deployment Server Config Retrieved at: " + epoch_date_time)   
           
@serverclass_app.command()
def get_serverclasses(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host,
    debug: Annotated[
        bool, typer.Option(envvar="SPLUNK_DEBUG")] = default_splunk_debug,  
    ):
    """
    Output Existing Serverclasses
    """
    print(f"Retrieving Serverclasses on {host}")
    r = requests.get("https://" + host + ":8089" + "/services/deployment/server/serverclasses",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    r.encoding = r.apparent_encoding
    if r.status_code == requests.codes.ok:
        if debug:
            print(f"Debug Output: XML of Serverclasses: {r.text}") 
        dom = minidom.parseString(r.text)
        name = dom.getElementsByTagName('title')
        print("Serverclasses Found: ")
        for n in name[1:]: # We have to skip the top level "serverclasses" element
            print(" ".join(t.nodeValue for t in n.childNodes if t.nodeType == t.TEXT_NODE))

@serverclass_app.command()
def create_serverclass(
    serverclass: Annotated[
        str, typer.Option()],
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host, 
    ):
    """
    Create a new serverclass.  Requires --serverclass.

    python main.py serverclass create-serverclass --serverclass Splunk_TA_nix
    """
    r = requests.post("https://" + host + ":8089" + "/services/deployment/server/serverclasses",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"name": serverclass}, verify=False)
    print("New Serverclass: " + r.text)

@serverclass_app.command()
def create_all_serverclasses(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host,
    debug: Annotated[
        bool, typer.Option(envvar="SPLUNK_DEBUG")] = default_splunk_debug,  
    ):
    """
    Create new serverclasses using toml inventory from config dir.
    """
    for pkg in apps['app']:
        print(f"Serverclass [bold blue]{pkg}[/bold blue] Loaded From Inventory.")
        # Create our list of allowlist entries
        # TODO add a denylist option
        # TODO improve this dict construction 
        # We get the clients to add to the serverclass from the toml file with the index as the value 
        servers_from_toml = {key: client for client, key in enumerate(apps['app'][pkg]['servers'])}
        # then we reverse the dict to get the index as the key
        inv_map_servers = {client: key for key, client in servers_from_toml.items()}
        prefix = "whitelist." # This is the default prefix for allowlists in the Splunk API
        # We build the allowlist dict from the reversed dict with the prefix required by the API
        allowlists = {prefix + str(key): value for key, value in inv_map_servers.items()}
        # Prepend the serverclass name to the dict of allowlists
        data = { "name": pkg } | allowlists
        if debug:
            print(f"Debug Data to be sent to API: {data}")
        r = requests.post("https://" + host + ":8089" + "/services/deployment/server/serverclasses",
            headers = { 'Authorization': ('Splunk %s' %session_key)},
            data = data, verify = False)
        if debug:
            print("Debug URL: " + r.request.url)
            print("Debug Body: " + r.request.body)
            print("Debug Headers: ")
            print(r.request.headers)
        dom = minidom.parseString(r.text)
        name = dom.getElementsByTagName('title')
        if name:
            for n in name[1:]: # We have to skip the top level "serverclasses" element
                print("Serverclass Created: " + " ".join(t.nodeValue for t in n.childNodes if t.nodeType == t.TEXT_NODE))
        else:
            print(f"Serverclass Already Exists: {pkg}")

@serverclass_app.command()
def add_host_to_serverclass(
    serverclass: Annotated[
        str, typer.Option()],
    client: Annotated[
        str, typer.Option(help="Client hostname name or glob e.g. splunk-hf-1 or \"splunk-hf-*\"")],
    list: Annotated[
        str, typer.Option(help="Whitelist or Blacklist with Int e.g. whitelist.0")] = default_allow_list,    
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host, 
    ):
    """
    Add client host to serverclass.
    Requires --serverclass and --client, optional --list defaults to 'whitelist.0'

    # python main.py serverclass add-host-to-serverclass --serverclass Splunk_TA_nix --client splunk-hf-1
    # python main.py serverclass add-host-to-serverclass --serverclass Splunk_TA_nix --client "splunk-hf-*" --list whitelist.1

    Note this endpoint can change, TODO pull this from the output above

    /servicesNS/nobody/search/deployment/server/serverclasses/Splunk_TA_nix
    
    /servicesNS/nobody/system/deployment/server/serverclasses/Splunk_TA_nix
    """
    r = requests.post("https://" + host + ":8089" + "/servicesNS/nobody/search/deployment/server/serverclasses/" + serverclass,
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={ list : client }, verify=False)
    print("Add Host: " + r.text)

@serverclass_app.command()
def add_hosts_to_serverclasses(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host,
    debug: Annotated[
        bool, typer.Option(envvar="SPLUNK_DEBUG")] = default_splunk_debug,   
    ):
    """
    Add client hosts to serverclasses using toml inventory from config dir

    # python main.py serverclass add-hosts-to-serverclasses

    Note this endpoint can change, TODO pull this from the output above

    /servicesNS/nobody/search/deployment/server/serverclasses/Splunk_TA_nix
    
    /servicesNS/nobody/system/deployment/server/serverclasses/Splunk_TA_nix
    """
    for pkg in apps['app']:
        print(f"Serverclass [bold blue]{pkg}[/bold blue] Loaded From Inventory.")
        servers_from_toml = {k: v for v, k in enumerate(apps['app'][pkg]['servers'])}
        inv_map_servers = {v: k for k, v in servers_from_toml.items()}
        prefix = "whitelist." # This is the default prefix for allowlists in the Splunk API
        allowlists = {prefix + str(key): value for key, value in inv_map_servers.items()}
        # Prepend the serverclass name to the list of allowlists
        if debug:
            print(f"Debug Output: Data to be sent to API: {allowlists}")
        r = requests.post("https://" + host + ":8089" + "/services/deployment/server/serverclasses/" + pkg,
            headers = { 'Authorization': ('Splunk %s' %session_key)},
            data = allowlists, verify = False)
        if debug:
            print(r.request.url)
            print(r.request.body)
            print(r.request.headers)
        dom = minidom.parseString(r.text)
        name = dom.getElementsByTagName('title')
        if name:
            for n in name[1:]: # We have to skip the top level "serverclasses" element
                print(f"Host(s) {allowlists} [bold]Added to Serverclass[/bold]: " + " ".join(t.nodeValue for t in n.childNodes if t.nodeType == t.TEXT_NODE))

@deploymentapps_app.command()
def get_deploymentapps(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host,
    debug: Annotated[
        bool, typer.Option(envvar="SPLUNK_DEBUG")] = default_splunk_debug,  
    ):
    """
    Output Existing DeploymentApps
    """
    print(f"Retrieving DeploymentApps on {host}")
    r = requests.get("https://" + host + ":8089" + "/services/deployment/server/applications",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    r.encoding = r.apparent_encoding
    if r.status_code == requests.codes.ok:
        if debug:
            print(f"Debug Output: XML of DeploymentApps: {r.text}") 
        print("Deployment Applications Found: ")
        dom = minidom.parseString(r.text)
        name = dom.getElementsByTagName('title')
        for n in name[1:]: # We have to skip the top level "applications" element
            print(" ".join(t.nodeValue for t in n.childNodes if t.nodeType == t.TEXT_NODE))

@deploymentapps_app.command()
def add_serverclass_to_app(
    serverclass: Annotated[
        str, typer.Option()],
    application: Annotated[
        str, typer.Option()],
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host, 
    ):
    """
    Add Serverclass to App.  
    Requires --application and --serverclass to add to app.

    # python main.py deploymentapps add-serverclass-to-app --application Splunk_TA_nix --serverclass Splunk_TA_nix
    """
    r = requests.post("https://" + host + ":8089" + "/servicesNS/nobody/system/deployment/server/applications/" + application,
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={"serverclass": serverclass}, verify=False)
    print("App Added: " + r.text)

@deploymentapps_app.command()
def add_all_serverclasses_to_app(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host,
    debug: Annotated[
        bool, typer.Option(envvar="SPLUNK_DEBUG")] = default_splunk_debug, 
    ):
    """
    Add Serverclasses to app using toml inventory from config dir.

    # python splunkapi.py add_all_serverclasses_to_app
    """
    for pkg in apps['app']:
        print(f"Application [bold purple]{pkg}[/bold purple] Loaded From Inventory.")
        r = requests.post("https://" + host + ":8089" + "/servicesNS/nobody/system/deployment/server/applications/" + pkg,
            headers = { 'Authorization': ('Splunk %s' %session_key)},
            data={"serverclass": {pkg}}, verify=False)
        r.encoding = r.apparent_encoding
        if r.status_code == requests.codes.ok:
            if debug:
                print(f"Debug Output: XML of DeploymentApps: {r.text}") 
        dom = minidom.parseString(r.text)
        name = dom.getElementsByTagName('title')
        for n in name[1:]: # We have to skip the top level "applications" element
            print(f"App Added:" + " ".join(t.nodeValue for t in n.childNodes if t.nodeType == t.TEXT_NODE))
        
if __name__ == "__main__":
    app()
