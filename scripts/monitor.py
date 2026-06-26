import argparse
import os
import smtplib
from email.message import EmailMessage

import boto3
import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Check a URL and optionally reboot an EC2 instance.")
    parser.add_argument("--url", default=os.getenv("MONITOR_URL"), help="URL to check.")
    parser.add_argument(
        "--instance-id",
        default=os.getenv("RECOVERY_INSTANCE_ID"),
        help="EC2 instance to reboot when the URL is unhealthy.",
    )
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--execute", action="store_true", help="Actually reboot the instance.")
    return parser.parse_args()


def send_notification(subject, body):
    sender = os.getenv("SMTP_SENDER")
    receiver = os.getenv("SMTP_RECEIVER")
    password = os.getenv("SMTP_PASSWORD")

    if not all([sender, receiver, password]):
        print("SMTP env vars are incomplete; skipping email notification.")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver
    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(message)


def recover_server(instance_id, region, execute):
    if not instance_id:
        print("No recovery instance configured; skipping reboot.")
        return

    if not execute:
        print(f"Dry run: would reboot EC2 instance {instance_id} in {region}.")
        return

    print(f"Rebooting EC2 instance {instance_id} in {region}...")
    ec2 = boto3.client("ec2", region_name=region)
    ec2.reboot_instances(InstanceIds=[instance_id])


def main():
    args = parse_args()
    if not args.url:
        raise SystemExit("Set MONITOR_URL or pass --url.")

    try:
        response = requests.get(args.url, timeout=args.timeout)
        if response.status_code == 200:
            print("Website is up and running.")
            return

        message = f"Website returned status code: {response.status_code}"
    except requests.RequestException as error:
        message = f"Website is unreachable: {error}"

    print(f"{message}. Sending notification and starting recovery path...")
    send_notification("ALERT: Website Down", message)
    recover_server(args.instance_id, args.region, args.execute)


if __name__ == "__main__":
    main()
