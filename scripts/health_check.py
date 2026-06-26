import argparse
import os
import time

import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Print EC2 instance health by region.")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--watch", action="store_true", help="Run continuously.")
    return parser.parse_args()


def check_server_status(region):
    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instances()

    print("Checking server status...")
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]
            print(f"{instance_id}: {state}")


def main():
    args = parse_args()

    while True:
        check_server_status(args.region)
        if not args.watch:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
