import boto3
from datetime import datetime, timezone, timedelta


def find_old_snapshots():
    ec2 = boto3.client("ec2", region_name="us-east-2")
    sts = boto3.client("sts")

    # Get your AWS Account ID so we only search your personal snapshots
    account_id = sts.get_caller_identity()["Account"]
    snapshots = ec2.describe_snapshots(OwnerIds=[account_id])["Snapshots"]

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    found = False

    for snap in snapshots:
        if snap["StartTime"] < cutoff_date:
            print(
                f"Old snapshot found: {snap['SnapshotId']} (Created: {snap['StartTime']})"
            )
            # ec2.delete_snapshot(SnapshotId=snap['SnapshotId']) # Uncomment this line to actually delete them!
            found = True

    if not found:
        print("No old snapshots found!")


find_old_snapshots()
