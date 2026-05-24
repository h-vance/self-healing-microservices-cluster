import boto3
import schedule
import time


def check_server_status():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    response = ec2.describe_instances()

    print("Checking server status...")
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            print(f"Instance ID: {instance['InstanceId']}")
            print(f"State: {instance['State']['Name']}")
            print("-" * 20)


# Schedule the job to run every 10 seconds
schedule.every(10).seconds.do(check_server_status)

# Keep the script running continuously
while True:
    schedule.run_pending()
    time.sleep(1)
