import boto3
import json
import urllib.request
import urllib.parse
from botocore.exceptions import ClientError as CE
import os

# S3 client reused across invocations for better performance
s3_client = boto3.client('s3')

# Slack webhook is injected via environment variable
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')


def get_presigned(key, bucket):
    try:
        # Generate a temporary download link for the uploaded object
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
        print(f"✔ URL generated for '{key}'")
        return url
    except CE as e:
        # Catch AWS-specific errors explicitly
        print(f"✖ AWS Error: {e}")
        return None
    

def send_slack_notification(download_link, filename):
    # No point continuing if the webhook is not configured
    if not SLACK_URL:
        print("✖ Error: SLACK_WEBHOOK_URL is missing!")
        return False
    
    message = f"*New Client Upload*\nFile: {filename}\nLink: <{download_link}|Download>"
    payload = {
        "text": message,
        "username": "S3 Drop-Box"
    }

    # Manual HTTP request to avoid extra dependencies
    req = urllib.request.Request(
        SLACK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            print("✔ Notification sent to Slack.")
            return True
        else:
            print(f"✖ Slack API Error: {response.getcode()}")
            return False
        
    except Exception as e:
        # Covers network issues, timeouts, etc.
        print(f"✖ Network Error: {e}")
        return False
    

def lambda_handler(event, context):
    try:
        # Guard clause to ensure this is actually an S3-triggered event
        if 'Records' not in event:
            print("✖ Event is missing 'Records'. Is this a test event?")
            return {'statusCode': 400, 'body': 'Not an S3 Event'}
            
        record = event['Records'][0]
        raw_key = record['s3']['object']['key']
        bucket_name = record['s3']['bucket']['name']

        # Decode the S3 key to get the actual filename
        filename = urllib.parse.unquote_plus(raw_key)

    except (KeyError, IndexError) as e:
        # Defensive handling for malformed events
        print(f"✖ parsing error: {e}")
        return {'statusCode': 500, 'body': 'Invalid Event Structure'}

    url = get_presigned(filename, bucket_name)
    if not url:
        return {'statusCode': 500, 'body': 'Failed to generate URL'}

    sent = send_slack_notification(url, filename)

    if sent:
        return {'statusCode': 200, 'body': 'Process complete'}
    else:
        return {'statusCode': 500, 'body': 'Failed to send notification'}