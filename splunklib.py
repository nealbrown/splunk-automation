from pprint import pprint
import splunklib.client as client
service = client.connect(host='192.168.10.159', port=8089, username='admin', password='changeme')
assert isinstance(service, client.Service)
for app in service.apps:
    pprint(app.state)