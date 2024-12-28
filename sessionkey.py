import typer, requests, config
from rich import print
from xml.dom import minidom
from typing_extensions import Annotated
from config import splunkapps as apps
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = typer.Typer()

@app.command()
def get_session_key(
    password: Annotated[
        str,typer.Option(envvar="SPLUNK_PASSWORD", prompt=True, hide_input=True)
        ],
    host: Annotated[
        str, typer.Argument(envvar="SPLUNK_HOST")] = "splunk-ds-1", 
    user: Annotated[
        str, typer.Argument(envvar="SPLUNK_USER")] = "admin", 
    ):
    r = requests.get("https://" + host + ":8089" + "/services/auth/login",
        data={'username':user,'password':password}, verify=False)
    global session_key 
    session_key = minidom.parseString(r.text).getElementsByTagName('sessionKey')[0].firstChild.nodeValue
    if session_key:
        print(f"Retrieved sessionkey: {session_key}") 
        return session_key
    else:
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()