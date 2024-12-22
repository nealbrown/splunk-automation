# aws-vault exec default -- python splunkboto.py
# equiv to aws ssm send-command \
    # --instance-ids "instance-ID" \
    # --document-name "AWS-RunShellScript" \
    # --comment "IP config" \
    # --parameters commands=ifconfig \
    # --output text

import boto3

client = boto3.client('ssm', region_name='us-east-1')

params={
    'commands': ['touch /tmp/ssm-success'],
}

response = client.send_command(
    InstanceIds=['i-asdfg'],
    DocumentName='AWS-RunShellScript',
    DocumentVersion='1',
    TimeoutSeconds=30,
    Comment='Download and install Splunk deployment-apps via Boto',
    Parameters=params
)