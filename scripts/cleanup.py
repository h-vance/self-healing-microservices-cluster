import argparse
import os
from datetime import datetime, timedelta, timezone

import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Delete old automated EBS snapshots.")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument("--description", default="Automated Backup")
    parser.add_argument("--older-than-days", type=int, default=30)
    parser.add_argument("--execute", action="store_true", help="Delete snapshots instead of dry-run output.")
    return parser.parse_args()


def main():
    args = parse_args()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.older_than_days)
    ec2 = boto3.client("ec2", region_name=args.region)
    response = ec2.describe_snapshots(OwnerIds=["self"])

    for snapshot in response["Snapshots"]:
        if snapshot.get("Description") != args.description:
            continue
        if snapshot["StartTime"] >= cutoff:
            continue

        snapshot_id = snapshot["SnapshotId"]
        if not args.execute:
            print(f"Dry run: would delete snapshot {snapshot_id}.")
            continue

        print(f"Deleting snapshot {snapshot_id}...")
        ec2.delete_snapshot(SnapshotId=snapshot_id)

    print("Cleanup scan complete.")


if __name__ == "__main__":
    main()
