# fab --list
# fab --hosts splunk install-TA-nix

from __future__ import with_statement
import os, sys, re, difflib, getpass
from time import strftime, localtime, sleep
from fabric import task, Connection, Config

sudo_pass = getpass.getpass("What's your sudo password?")
config = Config(overrides={'sudo': {'password': sudo_pass}})
c = Connection('splunk', config=config)

@task
def install_TA_nix(ctx):
    if c.run('test -f /opt/splunk/etc/apps/Splunk_TA_nix', warn=True).failed:
        print("Splunk_TA_nix not found.")
        c.run('uname -a')
        c.put('splunk-add-on-for-unix-and-linux_920.tgz', '/tmp')
        c.sudo('tar -C /opt/splunk/etc/apps -xzf /tmp/splunk-add-on-for-unix-and-linux_920.tgz && echo App Installed', hide='stderr') # Hide redundant sudo prompt
        c.sudo('chown splunk:splunk /opt/splunk/etc/apps/Splunk_TA_nix', hide='stderr') # Hide redundant sudo prompt