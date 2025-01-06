# splunk-automation
<h1>Python REST API calls for Splunk</h1>

Specifically addressing missing features in the Splunk Terraform provider such as managing deployment apps on a Splunk deployment server.  

This project will not support features such as local apps which are available in the Terraform provider

* https://registry.terraform.io/providers/splunk/splunk/latest/docs/resources/apps_local

Python fabfile for deploying apps from local host or S3 onto deployment server

`Typer` CLI app for creating and managing serverclasses, app assignments, and client assignments, all pulled from a simple `TOML` inventory file.

For Splunk Cloud app management see https://github.com/guilhemmarchand/splunk-cloud-automation/tree/main/manage-apps

Splunk Docs on CI/CD (Github) 
* https://www.splunk.com/en_us/blog/tips-and-tricks/ci-cd-automation-for-splunk-apps-using-github-actions.html
* https://www.splunk.com/en_us/blog/tips-and-tricks/ci-cd-automation-for-splunk-apps-using-github-actions-part-2.html

***

<h2>Prerequisites</h2>

<h3>Local</h3>

<b>Usable local python install: check via `python -v` or `python3 -v`. `venv` recommended.</b>

Tested on Python `3.9` (Ubuntu 22LTS) and `3.12/3.13` (Current at time of writing).  Note that we use `tomli` since `tomllib` was not added until after `3.9`.  Untested on `< 3.9`.

For docker use a bind mount to mount the repo into the `python` container via
```
docker run -it --mount type=bind,source=".",target="/code" --entrypoint bash python
```

Running the fabric app tgz deploy will require ssh access to the target so may need a further mount for the ssh key
`--mount type=bind,source="/home/user/.ssh",target="/root/.ssh"` 

On <b>Windows</b> see https://github.com/nealbrown/devops-windows/blob/main/docker-entrypoint.sh for ensuring proper perms on the key in the container and https://github.com/nealbrown/devops-windows/blob/main/docker-ps.ps1#L25C33-L25C54 for Windows pathing.

And access to the tgzs from within the container: `--mount type=bind,source="/home/user/Downloads",target="/root/Downloads"

<h3>Remote</h3>

On the splunk client host, either a UF or HF: 
```
./splunk set deploy-poll deployment-server.example.com:8089
```

<h3>CI/CD</h3>

Tested on Gitlab (Free) with SSH Key for Fabric and Splunk Password passed via Env Vars 
(which Gitlab cannot mask see https://gitlab.com/gitlab-org/gitlab/-/issues/220187)

***

<h2>Usage</h2>

```
export SPLUNK_HOST=deployment-server.example.com
export SPLUNK_USER=splunkadmin                              # defaults to 'admin'
export SPLUNK_PASSWORD=changeme                             # if not set, will prompt interactively
fab --hosts splunk install-deployment-apps                  # will copy tgzs from parent dir onto deploymentserver and unpack into deployment-apps, assumes tgzs in ~/Downloads
python main.py serverclass create-all-serverclasses         # creates all serverclasses including allowlists found in config/file.toml default splunkapps.toml
python main.py deploymentapps add-all-serverclasses-to-app  # add serverclasses to apps under forwarder management on the deployment server
```
Clients that check in will pull their apps based on matching any allowlist (what splunk calls a whitelist) entry

***

<h3>Known Issues</h3>

If an app is simply <b>missing</b> on the deployment server (doesn't exist in `deployment-apps`, potentially due to Fabric failing) the serverclass will still be created and <b>no error will be raised</b>, but no clients will deploy the app regardless of the allowlist configured for the serverclass.

Note that the Splunk REST API does not create the typical `/opt/splunk/etc/system/local/serverclass.conf` as one would create manually per the docs, but instead `/opt/splunk/etc/apps/search/local/serverclass.conf`:

```
root@splunk-ds-1:/opt/splunk# cat etc/apps/search/local/serverclass.conf 
[serverClass:Splunk_TA_nix]
whitelist.0 = splunk-hf-1
whitelist.1 = splunk-hf-2
whitelist.2 = splunk-hf-*

[serverClass:Splunk_TA_aws]
whitelist.0 = splunk-hf-1
whitelist.1 = splunk-hf-3

[serverClass:Splunk_TA_windows]
whitelist.0 = splunk-hf-2
```

***

Further Documentation


* https://docs.splunk.com/Documentation/Splunk/9.4.0/RESTREF/RESTdeploy
* https://docs.fabfile.org/en/stable/getting-started.html
* https://typer.tiangolo.com/tutorial/
* https://toml.io/en/
* https://code.visualstudio.com/docs/containers/quickstart-python

