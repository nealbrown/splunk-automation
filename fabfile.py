"""Deploy splunk app tgz files to deployment server and untar"""
# fab --list
# fab --hosts splunk install-TA-nix
# fab --hosts splunk install-deployment-apps

from __future__ import with_statement
import pathlib
import getpass
import config
from invoke import Responder
from fabric import task, Connection, Config
from config import splunkapps as apps

sudo_pass = getpass.getpass("Enter sudo password:")
config = Config(overrides={'sudo': {'password': sudo_pass}})
sudopass = Responder(
    pattern=r'\[sudo\] password:',
    response=sudo_pass + "\n",
)
c = Connection('localhost', config=config)

@task
def test_connection(conn):
    """Test connection to Splunk server."""
    result = conn.run('uname -s', hide='stderr')
    print(f"Successfully connected to {c.host} as {c.user} running {result.stdout.strip()}.")

@task
def install_ta_nix(conn):
    """Install Splunk_TA_nix."""
    tgz_path = pathlib.Path.home().joinpath("Downloads")
    if conn.run('test -d /opt/splunk/etc/deployment-apps/Splunk_TA_nix', warn=True).failed:
        print("Splunk_TA_nix not found.")
        conn.put(tgz_path + '/splunk-add-on-for-unix-and-linux_920.tgz', '/tmp')
        conn.sudo(
            'tar -C /opt/splunk/etc/deployment-apps \
            -xzf /tmp/splunk-add-on-for-unix-and-linux_920.tgz',
            # Hide redundant sudo prompt via hide='both'
            hide='both', pty=True, watchers=[sudopass])
        print("Splunk_TA_nix installed.")
        conn.sudo('chown splunk:splunk /opt/splunk/etc/deployment-apps/Splunk_TA_nix',
        hide='both', pty=True, watchers=[sudopass])
    else:
        print("Splunk_TA_nix found already installed in deployment-apps.")

@task
def install_deployment_apps(conn):
    """Install deployment apps."""
    tgz_path = pathlib.Path.home().joinpath("Downloads")
    for pkg in apps['app']:
        if conn.run(f'test -d /opt/splunk/etc/deployment-apps/{pkg}', warn=True).failed:
            print(f"{pkg} not found in deployment-apps.")
            # note the / here since pathlib strips trailing slashes
            conn.put(f'{tgz_path}/{(apps['app'][pkg]['filename'])}', '/tmp')
            conn.sudo(f'tar -C /opt/splunk/etc/deployment-apps \
                -xzf /tmp/{(apps['app'][pkg]['filename'])}',
                # Hide redundant sudo prompt via hide='both'
                hide='both', pty=True, watchers=[sudopass])
            print(f"App {pkg} Installed in deployment-apps.")
            conn.sudo(f'chown splunk:splunk /opt/splunk/etc/deployment-apps/{pkg} ',
            hide='both', pty=True, watchers=[sudopass])
        else:
            print(f"App {pkg} found already installed in deployment-apps.")

@task
# fab -H localhost:2222 install-deployment-apps-from-s3
# to use existing SSM tunnel, requires proper auth config in ~/.ssh/config
def install_deployment_apps_from_s3(conn):
    """Install deployment apps from S3."""
    for pkg in apps['app']:
        if conn.run(f'test -d /opt/splunk/etc/deployment-apps/{pkg}', warn=True).failed:
            print(f"{pkg} not found in deployment-apps.")
            print(f"Retrieving {pkg} from \
                {(apps['aws_s3_bucket'])}/deployment-apps/{(apps['app'][pkg]['filename'])}.")
            conn.sudo(f'aws s3 cp --region us-east-1 \
                {(apps['aws_s3_bucket'])}/deployment-apps/{(apps['app'][pkg]['filename'])} /tmp/',
                 pty=False)
            conn.sudo(f'tar -C /opt/splunk/etc/deployment-apps \
                -xzf /tmp/{(apps['app'][pkg]['filename'])}', pty=False)
            print(f"App {pkg} Installed in deployment-apps.")
            conn.sudo(f'chown splunk:splunk /opt/splunk/etc/deployment-apps/{pkg}', pty=False)
        else:
            print(f"App {pkg} found already installed in deployment-apps.")
