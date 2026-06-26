import argparse
import os
from datetime import datetime, timedelta, timezone

import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Find or delete old account-owned EBS snapshots.")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument("--older-than-days", type=int, default=30)
    parser.add_argument("--execute", action="store_true", help="Delete old snapshots instead of dry-run output.")
    return parser.parse_args()


def main():
    args = parse_args()
    ec2 = boto3.client("ec2", region_name=args.region)
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]
    snapshots = ec2.describe_snapshots(OwnerIds=[account_id])["Snapshots"]
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=args.older_than_days)
    found = False

    for snapshot in snapshots:
        if snapshot["StartTime"] >= cutoff_date:
            continue

        found = True
        snapshot_id = snapshot["SnapshotId"]
        if not args.execute:
            print(f"Dry run: old snapshot found: {snapshot_id} ({snapshot['StartTime']}).")
            continue

        print(f"Deleting old snapshot {snapshot_id}...")
        ec2.delete_snapshot(SnapshotId=snapshot_id)

    if not found:
        print("No old snapshots found.")


if __name__ == "__main__":
    main()
