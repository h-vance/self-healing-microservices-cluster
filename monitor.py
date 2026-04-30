import requests
import smtplib
import boto3

url = "http://3.17.207.182"
instance_id = "i-02221e90b60217e1d"


def send_notification(email_msg):
    sender = "hvance788@gmail.com"
    receiver = "hvance788@gmail.com"
    password = "slryztetpzlzlbxb"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, email_msg)


def recover_server():
    print(f"Rebooting EC2 instance {instance_id}...")
    ec2 = boto3.client("ec2", region_name="us-east-2")
    ec2.reboot_instances(InstanceIds=[instance_id])


try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        print("Website is up and running!")
    else:
        print("Website returned an error. Sending email and recovering...")
        send_notification(
            f"Subject: ALERT: Website Down\n\nWebsite returned status code: {response.status_code}"
        )
        recover_server()
except Exception as e:
    print("Could not reach the website. Sending email and recovering...")
    send_notification(
        "Subject: ALERT: Website Down\n\nThe website is completely unreachable!"
    )
    recover_server()
