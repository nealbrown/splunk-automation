# fab --list
# fab --hosts splunk install-TA-nix
# fab --hosts splunk install-deployment-apps

from __future__ import with_statement
import os, sys, re, difflib, getpass, tomllib, config
from time import strftime, localtime, sleep
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
def test_connection(c):
    result = c.run('uname -s', hide='stderr')
    print(f"Successfully connected to {c.host} running {result.stdout.strip()}.")

@task
def install_TA_nix(c):
    if c.run('test -d /opt/splunk/etc/deployment-apps/Splunk_TA_nix', warn=True).failed:
        print("Splunk_TA_nix not found.")
        c.put('../splunk-add-on-for-unix-and-linux_920.tgz', '/tmp')
        c.sudo('tar -C /opt/splunk/etc/deployment-apps -xzf /tmp/splunk-add-on-for-unix-and-linux_920.tgz', hide='both', pty=True, watchers=[sudopass]) # Hide redundant sudo prompt
        print("Splunk_TA_nix installed.")
        c.sudo('chown splunk:splunk /opt/splunk/etc/deployment-apps/Splunk_TA_nix', hide='both', pty=True, watchers=[sudopass]) # Hide redundant sudo prompt
    else:
        print("Splunk_TA_nix found already installed in deployment-apps.")

@task
def install_deployment_apps(c):
    for pkg in apps['app']:
        if c.run(f'test -d /opt/splunk/etc/deployment-apps/{pkg}', warn=True).failed:
            print(f"{pkg} not found in deployment-apps.")
            c.put(f'../{(apps['app'][pkg]['filename'])}', '/tmp')
            c.sudo(f'tar -C /opt/splunk/etc/deployment-apps -xzf /tmp/{(apps['app'][pkg]['filename'])}', hide='both', pty=True, watchers=[sudopass]) # Hide redundant sudo prompt
            print(f"App {pkg} Installed in deployment-apps.")
            c.sudo(f'chown splunk:splunk /opt/splunk/etc/deployment-apps/{pkg} ', hide='both', pty=True, watchers=[sudopass]) # Hide redundant sudo prompt
        else:
            print(f"App {pkg} found already installed in deployment-apps.")
