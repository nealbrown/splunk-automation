# export SPLUNK_PASSWORD=changeme
# To add or manage individual apps or serverclasses call the subcommand with its required flags
# 
# To populate a deployment server first ensure the inventory in config/splunkapps.toml is complete 
# and that the app tgz's are present on the path specified
# 
# Install the apps via the accompanying fabfile
# then run
# python main.py serverclass create-all-serverclasses
# python main.py serverclass add-hosts-to-serverclasses
# python main.py deploymentapps add-all-serverclasses-to-app

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
default_splunk_host     = "splunk-ds-1" # SPLUNK_HOST
default_splunk_user     = "admin"       # SPLUNK_USER
default_splunk_debug    = True          # SPLUNK_DEBUG

# No ENV VAR support
default_allow_list      = "whitelist.0"

# Note that instead of using typing.List we expect singular arguments unless we are pulling from the toml config file

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    password: Annotated[
        str,typer.Option(envvar="SPLUNK_PASSWORD", prompt=True, hide_input=True)
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

    Required: --host (has default) --user (has default) and --password (no default, will prompt). Optional: --no-debug to hide sessionkey output.
    
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
        print("Serverclasses Found: ")
        dom = minidom.parseString(r.text)
        name = dom.getElementsByTagName('title')
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
    ):
    """
    Create new serverclasses using toml inventory from config dir.
    """
    for pkg in apps['app']:
        r = requests.post("https://" + host + ":8089" + "/services/deployment/server/serverclasses",
            headers = { 'Authorization': ('Splunk %s' %session_key)},
            data={"name": {pkg}}, verify=False)
        print("New Serverclass: " + r.text)

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
        data={list : client }, verify=False)
    print("Add Host: " + r.text)

@serverclass_app.command()
def add_hosts_to_serverclasses(
    list: Annotated[
        str, typer.Option(help="Whitelist or Blacklist with Int e.g. whitelist.0")] = default_allow_list,
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = default_splunk_host, 
    ):
    """
    Add all client hosts to serverclasses using toml inventory from config dir and --list default of whitelist.0

    # python main.py serverclass add-hosts-to-serverclasses

    Note this endpoint can change, TODO pull this from the output above

    /servicesNS/nobody/search/deployment/server/serverclasses/Splunk_TA_nix
    
    /servicesNS/nobody/system/deployment/server/serverclasses/Splunk_TA_nix
    """
    for pkg in apps['app']:
        r = requests.post("https://" + host + ":8089" + "/servicesNS/nobody/search/deployment/server/serverclasses/" + pkg,
            headers = { 'Authorization': ('Splunk %s' %session_key)},
            data={ list : {(apps['app'][pkg]['servers'])} }, verify=False)
        print("Add Host: " + r.text)

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
    ):
    """
    Add Serverclasses to app using toml inventory from config dir.

    # python splunkapi.py add_all_serverclasses_to_app
    """
    for pkg in apps['app']:
        r = requests.post("https://" + host + ":8089" + "/servicesNS/nobody/system/deployment/server/applications/" + pkg,
            headers = { 'Authorization': ('Splunk %s' %session_key)},
            data={"serverclass": {pkg}}, verify=False)
        print("App Added: " + r.text)

if __name__ == "__main__":
    app()