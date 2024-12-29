import typer, requests, config, os
from rich import print
from xml.dom import minidom
from typing_extensions import Annotated
from config import splunkapps as apps
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = typer.Typer()
serverclasses_app = typer.Typer()
app.add_typer(serverclasses_app, name="serverclasses")

@serverclasses_app.command("get-serverclasses")
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
    ):
    """
    First we retrieve and return a sessionkey to use for API auth prior to running a subcommand.
    Then each subcommand can operate on applications or serverclasses as specified in their individual descriptions.
    """
    r = requests.get("https://" + host + ":8089" + "/services/auth/login",
        data={'username':user,'password':password}, verify=False)
    global session_key
    session_key = minidom.parseString(r.text).getElementsByTagName('sessionKey')[0].firstChild.nodeValue
    if session_key:
        print(f"Retrieved api auth sessionkey: {session_key}") 
    else:
        raise typer.Exit(code=1)
    if ctx.invoked_subcommand is None:
        print("No further command specified. Session key will expire in 60 minutes.")

if __name__ == "__main__":
    app()