import boto3
import json
import urllib.request
import os
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError

# EC2 client reused across executions
ec2 = boto3.client('ec2')

# Slack webhook is optional and controlled via env variable
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')


def get_backup_type(vol_id):
    try:
        # Checking if this volume already has manager-created snapshots
        response = ec2.describe_snapshots(
            Filters=[
                {'Name': 'volume-id', 'Values': [vol_id]},
                {'Name': 'tag:CreatedBy', 'Values': ['EBSLifecycleManager']}
            ]
        )
        snapshots = response.get("Snapshots", [])
        return "Initial" if len(snapshots) == 0 else "Incremental"
    except ClientError:
        # Fallback to avoid blocking snapshot creation
        return "Unknown"


def backup_creation():
    created_count = 0
    try:
        # Only volumes explicitly marked for backup are considered
        vols = ec2.describe_volumes(
            Filters=[{'Name': 'tag:Backup', 'Values': ['true', 'True']}]
        )

        for volume in vols.get("Volumes", []):
            vol_id = volume["VolumeId"]
            tags = {t['Key']: t['Value'] for t in volume.get('Tags', [])}
            vol_name = tags.get('Name', 'Unnamed')

            backup_type = get_backup_type(vol_id)

            snap = ec2.create_snapshot(
                VolumeId=vol_id,
                Description=f"Snapshot of {vol_id} ({vol_name})",
                TagSpecifications=[
                    {
                        "ResourceType": "snapshot",
                        "Tags": [
                            {"Key": "CreatedBy", "Value": "EBSLifecycleManager"},
                            {"Key": "BackupType", "Value": backup_type},
                            {"Key": "Name", "Value": f"Backup-{vol_name}-{vol_id}"}
                        ],
                    }
                ],
            )
            print(f"[{backup_type}] Snapshot {snap['SnapshotId']} created for {vol_id}")
            created_count += 1

        print(f"Backup complete. Total created: {created_count}")
        return True, f"Created {created_count} snapshots."
    
    except Exception as e:
        # Any failure here should be surfaced clearly in the report
        print(f"Error creating backup: {e}")
        return False, str(e)


def backup_cleanup():
    deleted_count = 0
    try:
        # Hard retention rule to control snapshot sprawl
        retention_days = 7
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        print(f"Pruning snapshots older than: {cutoff_date}")
        
        response = ec2.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'tag:CreatedBy', 'Values': ['EBSLifecycleManager']}
            ]
        )

        for snap in response.get('Snapshots', []):
            snap_time = snap["StartTime"]
            snap_id = snap["SnapshotId"]

            if snap_time < cutoff_date:
                print(f"Deleting {snap_id} (Created: {snap_time})")
                ec2.delete_snapshot(SnapshotId=snap_id)
                deleted_count += 1

        print(f"Pruning complete. Total deleted: {deleted_count}")
        return True, f"Deleted {deleted_count} old snapshots."

    except Exception as e:
        print(f"Error pruning snapshots: {e}")
        return False, str(e)


def send_slack_notification(message):
    # Allows the function to run silently without Slack configured
    if not SLACK_URL:
        print("Silent Mode: No SLACK_WEBHOOK_URL set.")
        return
    
    payload = {
        "text": message,
        "username": "EBS Lifecycle Manager",
        "icon_emoji": ":floppy_disk:"
    }

    try:
        req = urllib.request.Request(
            SLACK_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
    except Exception as e:
        # Slack failure should never break the Lambda
        print(f"Failed to send Slack notification: {e}")


def lambda_handler(event, context):
    # Backup and cleanup are treated as independent operations
    backup_success, backup_msg = backup_creation()
    cleanup_success, cleanup_msg = backup_cleanup()

    status_symbol = "✔" if (backup_success and cleanup_success) else "⚠"
    
    final_message = (
        f"{status_symbol} *EBS Lifecycle Report*\n"
        f"> Backup: {backup_msg}\n"
        f"> Cleanup: {cleanup_msg}"
    )

    send_slack_notification(final_message)
    
    return {
        'statusCode': 200, 
        'body': final_message
    }