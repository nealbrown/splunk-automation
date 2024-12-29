import typer, requests, config
from rich import print
from xml.dom import minidom
from typing_extensions import Annotated
from config import splunkapps as apps
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = typer.Typer(pretty_exceptions_show_locals=False)
serverclass_app = typer.Typer(pretty_exceptions_show_locals=False, help="Retrieve and manage serverclasses.")
deploymentapps_app = typer.Typer(pretty_exceptions_show_locals=False, help="Manage deploymentapps.")
app.add_typer(serverclass_app, name="serverclass")
app.add_typer(deploymentapps_app, name="deploymentapps")

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    password: Annotated[
        str,typer.Option(envvar="SPLUNK_PASSWORD", prompt=True, hide_input=True)
        ],
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
    user: Annotated[
        str, typer.Option(envvar="SPLUNK_USER")] = "admin", 
    debug: Annotated[
        bool, typer.Option(envvar="SPLUNK_DEBUG")] = True, 
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

@serverclass_app.command()
def get_serverclasses(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
    ):
    """
    Output Existing Serverclasses
    """
    print(f"Retrieving Serverclasses on {host}")
    r = requests.get("https://" + host + ":8089" + "/services/deployment/server/serverclasses",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    print("Serverclasses: " + r.text)

@serverclass_app.command()
def create_serverclass(
    serverclass: Annotated[
        str, typer.Option()],
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
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
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
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
        str, typer.Option(help="Whitelist or Blacklist with Int e.g. whitelist.0")] = "whitelist.0",    
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
    ):
    """
    Add host to serverclass.
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

@deploymentapps_app.command()
def get_deploymentapps(
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
    ):
    """
    Output Existing DeploymentApps
    """
    r = requests.get("https://" + host + ":8089" + "/services/deployment/server/applications",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    print("Deployment Applications: " + r.text)

@deploymentapps_app.command()
def add_serverclass_to_app(
    serverclass: Annotated[
        str, typer.Option()],
    application: Annotated[
        str, typer.Option()],
    host: Annotated[
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
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
        str, typer.Option(envvar="SPLUNK_HOST")] = "splunk-ds-1",
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