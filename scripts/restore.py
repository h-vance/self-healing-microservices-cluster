import argparse
import os

import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Restore and attach an EBS volume from a snapshot.")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--availability-zone", required=True)
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument("--device", default="/dev/sdf")
    parser.add_argument("--execute", action="store_true", help="Create and attach the volume.")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.execute:
        print(
            "Dry run: would create a volume from "
            f"{args.snapshot_id} in {args.availability_zone} and attach it to "
            f"{args.instance_id} as {args.device}."
        )
        return

    ec2 = boto3.client("ec2", region_name=args.region)
    print(f"Restoring volume from {args.snapshot_id}...")
    volume = ec2.create_volume(
        SnapshotId=args.snapshot_id,
        AvailabilityZone=args.availability_zone,
        TagSpecifications=[
            {
                "ResourceType": "volume",
                "Tags": [{"Key": "RestoredBy", "Value": "restore.py"}],
            }
        ],
    )
    volume_id = volume["VolumeId"]

    print(f"Waiting for {volume_id} to become available...")
    ec2.get_waiter("volume_available").wait(VolumeIds=[volume_id])

    print(f"Attaching {volume_id} to {args.instance_id}...")
    ec2.attach_volume(
        VolumeId=volume_id,
        InstanceId=args.instance_id,
        Device=args.device,
    )
    print("Restore and attachment complete.")


if __name__ == "__main__":
    main()
