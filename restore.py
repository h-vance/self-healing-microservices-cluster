import boto3
import time

ec2 = boto3.client("ec2", region_name="us-east-1")

snapshot_id = "snap-06ba93e636ba16626"
instance_id = "i-01e50e9ba7b378cb8"
az = "us-east-1d"  # Make sure this matches your instance's Availability Zone

print(f"Restoring volume from {snapshot_id}...")
volume = ec2.create_volume(SnapshotId=snapshot_id, AvailabilityZone=az)
vol_id = volume["VolumeId"]

# Wait for AWS to provision the volume
print("Waiting for volume to become available...")
time.sleep(15)

print(f"Attaching {vol_id} to {instance_id}...")
ec2.attach_volume(VolumeId=vol_id, InstanceId=instance_id, Device="/dev/sdf")
print("Restore and attachment complete!")
