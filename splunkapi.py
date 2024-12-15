import os
import configargparse
from pprint import pprint
import getpass
import splunklib.client as client

parser = configargparse.ArgumentParser(
   description="Splunklib interface using configargparse",
   default_config_files=['splunklib.ini'],  # Specify default config file
   )

parser.add_argument('--host', env_var='SPLUNK_HOST', type=str, help='Splunk Host Name or IP')
parser.add_argument('--user', env_var='SPLUNK_USER', type=str, help='Splunk Username')
parser.add_argument('--password', env_var='SPLUNK_PASS', type=str, help='Splunk Password')

args = parser.parse_args()

if not args.host:
    print('Splunk host not set.')
    args.host = input("Please enter hostname or IP of Splunk Host: ")
if not args.user:
    print('Splunk user not set.')
    args.username = input("Please enter admin username: ")
if not args.password:
    print('Splunk password not set.')
    args.password = getpass.getpass('Please enter admin password, will not be echoed: ')

service = client.connect(host=args.host, port=8089, username=args.user, password=args.password)
assert isinstance(service, client.Service)
for app in service.apps:
    pprint(app.state)