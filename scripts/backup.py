import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
response = ec2.describe_volumes()

for volume in response["Volumes"]:
    vol_id = volume["VolumeId"]
    print(f"Creating snapshot for {vol_id}...")
    ec2.create_snapshot(VolumeId=vol_id, Description="Automated Backup")

print("Backups initiated!")
