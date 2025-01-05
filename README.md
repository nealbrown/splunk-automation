# splunk-automation
Python REST API calls for Splunk

Specifically addressing missing features in the Splunk Terraform provider such as managing deployment apps on a Splunk deployment server.  

This project will not support features such as local apps which are available in the Terraform provider

* https://registry.terraform.io/providers/splunk/splunk/latest/docs/resources/apps_local

Python fabfile for deploying apps from local host or S3 onto deployment server

Typer CLI app for creating and managing serverclasses, app assignments, and client assignments, all pulled from a simple TOML inventory file.

For Splunk Cloud app management see https://github.com/guilhemmarchand/splunk-cloud-automation/tree/main/manage-apps

Splunk Docs on CI/CD (Github) 
* https://www.splunk.com/en_us/blog/tips-and-tricks/ci-cd-automation-for-splunk-apps-using-github-actions.html
* https://www.splunk.com/en_us/blog/tips-and-tricks/ci-cd-automation-for-splunk-apps-using-github-actions-part-2.html

***

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
