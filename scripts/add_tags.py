import argparse
import os

import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Tag EC2 instances in an account and region.")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument("--key", default="Environment")
    parser.add_argument("--value", default="Dev")
    parser.add_argument("--execute", action="store_true", help="Apply tags instead of dry-run output.")
    return parser.parse_args()


def main():
    args = parse_args()
    ec2 = boto3.client("ec2", region_name=args.region)
    response = ec2.describe_instances()

    instance_ids = [
        instance["InstanceId"]
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]

    if not instance_ids:
        print("No instances found.")
        return

    tag = {"Key": args.key, "Value": args.value}
    if not args.execute:
        print(f"Dry run: would tag {len(instance_ids)} instances with {tag}.")
        return

    ec2.create_tags(Resources=instance_ids, Tags=[tag])
    print(f"Successfully tagged {len(instance_ids)} instances.")


if __name__ == "__main__":
    main()
