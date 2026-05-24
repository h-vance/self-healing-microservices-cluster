import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
response = ec2.describe_instances()

# Gather all Instance IDs
instance_ids = []
for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        instance_ids.append(instance["InstanceId"])

# Add a tag to all found instances
if instance_ids:
    ec2.create_tags(
        Resources=instance_ids, Tags=[{"Key": "Environment", "Value": "Dev"}]
    )
    print(f"Successfully tagged {len(instance_ids)} instances!")
else:
    print("No instances found.")
