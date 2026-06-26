import argparse
import os

import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Create EBS snapshots for account volumes.")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument("--description", default="Automated Backup")
    parser.add_argument("--execute", action="store_true", help="Create snapshots instead of dry-run output.")
    return parser.parse_args()


def main():
    args = parse_args()
    ec2 = boto3.client("ec2", region_name=args.region)
    response = ec2.describe_volumes()

    for volume in response["Volumes"]:
        volume_id = volume["VolumeId"]
        if not args.execute:
            print(f"Dry run: would create snapshot for {volume_id}.")
            continue

        print(f"Creating snapshot for {volume_id}...")
        ec2.create_snapshot(VolumeId=volume_id, Description=args.description)

    print("Backup scan complete.")


if __name__ == "__main__":
    main()
