# fab --list
# fab --hosts splunk install-TA-nix

from __future__ import with_statement
import os, sys, re, difflib, getpass
from time import strftime, localtime, sleep
from fabric import task, Connection, Config

sudo_pass = getpass.getpass("Enter sudo password:")
config = Config(overrides={'sudo': {'password': sudo_pass}})
c = Connection('splunk', config=config)

@task
def test_connection(c):
    result = c.run('uname -s', hide='stderr')
    print(f"Successfully connected to {c.host} running {result.stdout.strip()}.")

@task
def install_TA_nix(c):
    if c.run('test -f /opt/splunk/etc/deployment-apps/Splunk_TA_nix', warn=True).failed:
        print("Splunk_TA_nix not found.")
        c.put('splunk-add-on-for-unix-and-linux_920.tgz', '/tmp')
        c.sudo('tar -C /opt/splunk/etc/deployment-apps -xzf /tmp/splunk-add-on-for-unix-and-linux_920.tgz && echo App Installed', hide='stderr') # Hide redundant sudo prompt
        c.sudo('chown splunk:splunk /opt/splunk/etc/deployment-apps/Splunk_TA_nix', hide='stderr') # Hide redundant sudo prompt
