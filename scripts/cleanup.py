import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
# Ask AWS for all snapshots owned by your account
response = ec2.describe_snapshots(OwnerIds=["self"])

print("Checking for backups to clean up...")
for snapshot in response["Snapshots"]:
    # Only delete snapshots created by our backup script
    if snapshot["Description"] == "Automated Backup":
        snap_id = snapshot["SnapshotId"]
        print(f"Deleting snapshot {snap_id}...")
        ec2.delete_snapshot(SnapshotId=snap_id)

print("Cleanup complete!")
