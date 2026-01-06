import boto3
import json
import urllib.request
import os
from botocore.exceptions import ClientError as CE

# EC2 client reused across Lambda executions
ec2 = boto3.client('ec2')

# Slack webhook is optional and controlled via env variable
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')


def send_slack_notification(message):
    # Allows this Lambda to run quietly if Slack is not configured
    if not SLACK_URL:
        print("Silent Mode: No SLACK_WEBHOOK_URL set.")
        return
    
    payload = {
        "text": message,
        "username": "Security Group Auditor",
        "icon_emoji": ":shield:"
    }

    try:
        req = urllib.request.Request(
            SLACK_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
    except Exception as e:
        # Slack failures should never break remediation
        print(f"Failed to send Slack notification: {e}")


def check_and_remediate_rules():
    found = 0
    revoked = 0

    try:
        res = ec2.describe_security_groups()

        for sg in res.get("SecurityGroups", []):
            for ip in sg.get("IpPermissions", []):

                from_port = ip.get("FromPort")
                to_port = ip.get("ToPort")

                # Skipping non-TCP or port-agnostic rules
                if from_port is None or to_port is None:
                    continue

                # Checking if this rule exposes SSH
                if from_port <= 22 <= to_port:
                    for cidr in ip.get("IpRanges", []):

                        # World-open SSH is considered a violation
                        if cidr.get("CidrIp", "") == "0.0.0.0/0":
                            found += 1

                            print(f"Revoking rule on {sg['GroupId']} (Port 22 from World)")
                            
                            ec2.revoke_security_group_ingress(
                                GroupId=sg['GroupId'],
                                IpPermissions=[
                                    {
                                        'IpProtocol': ip['IpProtocol'],
                                        'FromPort': from_port,
                                        'ToPort': to_port,
                                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                                    }
                                ]
                            )

                            revoked += 1

        message = f"Found {found} and revoked {revoked} rules allowing Port 22 from internet."
        print(message)
        return True, message
    
    except CE as e:
        # AWS-side failures are reported with partial progress context
        error_message = f"AWS error after finding {found}/revoking {revoked}: {e}"
        print(error_message)
        return False, error_message
    except Exception as e:
        # Catch-all for unexpected runtime issues
        error_message = f"Critical error after finding {found}/revoking {revoked}: {e}"
        print(error_message)
        return False, error_message


def lambda_handler(event, context):
    success, message = check_and_remediate_rules()

    # Only notify if something changed or if the run failed
    if not success or "Found 0" not in message:
        send_slack_notification(message)

    if success:
        return {'statusCode': 200, 'body': message}
    else:
        return {'statusCode': 500, 'body': message}