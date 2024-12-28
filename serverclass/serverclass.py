import typer, requests, config
from config import splunkapps as apps

app = typer.Typer()

@app.command()
def get_serverclasses(args, sessionkey):
    """
    Output Existing Serverclasses
    """
    r = requests.get("https://" + args.host + ":8089" + "/services/deployment/server/serverclasses",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        data={}, verify=False)
    print("Serverclasses: " + r.text)

if __name__ == "__main__":
    app()