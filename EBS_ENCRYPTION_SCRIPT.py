import boto3
import csv


def fetch_unencrypted_volumes():
    print("+================================================================+")
    print("+                                                                +")
    print("+                      EBS Encryption Started                    +")
    print("+                                                                +")
    print("+================================================================+")
    # Initialize the EC2 client
    ec2_client = boto3.client('ec2')

    csv_filename = 'output.csv'
    header = ['Instance Id', 'Encrypted Volume Id', 'Unencrypted Volume Id', 'Device Name', 'Snapshot Id']

    with open(csv_filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if csv_file.tell() == 0:
            writer.writerow(header)

    # Fetch a list of instances
    reservations = ec2_client.describe_instances()['Reservations']

    instance_ids = []
    unencrypted_volume_ids = []

    for reservation in reservations:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            for block_device in instance['BlockDeviceMappings']:
                volume_id = block_device['Ebs']['VolumeId']
                # Describe the volume to check if it's encrypted
                volume_info = ec2_client.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]
                encrypted = volume_info['Encrypted']
                if not encrypted:
                    instance_ids.append(instance_id)
                    unencrypted_volume_ids.append(volume_id)
                else:
                     print(f"Volume {volume_id} is already encrypted.")
                     test = []
                     test.append(instance_id)
                     test.append(volume_id)
                     test.append("Already Encrypted")
                     test.append("-")
                     test.append("-")
                     with open(csv_filename, 'a', newline='') as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow(test)

    return instance_ids, unencrypted_volume_ids

def encrypt_attach_delete_volumes(instance_ids, unencrypted_volume_ids):
    # Initialize the EC2 client
    ec2_client = boto3.client('ec2')


    for instance_id, unencrypted_volume_id in zip(instance_ids, unencrypted_volume_ids):
        try:
            # Describe the unencrypted volume to check its properties
            volume_info = ec2_client.describe_volumes(VolumeIds=[unencrypted_volume_id])['Volumes'][0]

            # Check if the volume is already encrypted
            if volume_info['Encrypted']:
                print(f"Volume {unencrypted_volume_id} is already encrypted.")
                continue

            # Detach the unencrypted volume from the instance
            test = []
            csv_filename = 'output.csv'

            ec2_client.detach_volume(InstanceId=instance_id, VolumeId=unencrypted_volume_id)
            ec2_client.get_waiter('volume_available').wait(VolumeIds=[unencrypted_volume_id])

            # Create a snapshot of the unencrypted volume
            snapshot_response = ec2_client.create_snapshot(
                VolumeId=unencrypted_volume_id,
                Description=f"Snapshot for encrypting volume {unencrypted_volume_id}"
            )

            # Wait for the snapshot to complete
            snapshot_id = snapshot_response['SnapshotId']
            ec2_client.get_waiter('snapshot_completed').wait(SnapshotIds=[snapshot_id])

            # Create a new encrypted volume from the snapshot
            encrypted_volume_response = ec2_client.create_volume(
                SnapshotId=snapshot_id,
                AvailabilityZone=volume_info['AvailabilityZone'],
                Encrypted=True,
                VolumeType=volume_info['VolumeType']
            )

            # Wait for the new encrypted volume to be available
            encrypted_volume_id = encrypted_volume_response['VolumeId']
            ec2_client.get_waiter('volume_available').wait(VolumeIds=[encrypted_volume_id])

            # Attach the new encrypted volume to the instance with the original device name
            original_device_name = volume_info['Attachments'][0]['Device']
            ec2_client.attach_volume(InstanceId=instance_id, VolumeId=encrypted_volume_id, Device=original_device_name)

            print(f"Encrypted volume {encrypted_volume_id} attached to instance {instance_id} with device {original_device_name}.")


            # Delete the unencrypted volume
            ec2_client.delete_volume(VolumeId=unencrypted_volume_id)
            print(f"Unencrypted volume {unencrypted_volume_id} deleted.")

            test.append(instance_id)
            test.append(encrypted_volume_id)
            test.append(unencrypted_volume_id)
            test.append(original_device_name)
            test.append(snapshot_id)
            print(f"{instance_id} {encrypted_volume_id} {unencrypted_volume_id} {original_device_name} {snapshot_id}")
            with open(csv_filename, 'a', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(test)
    
        except Exception as e:
            print(f"Error encrypting, attaching, and deleting volume: {str(e)}")


if __name__ == '__main__':

    instance_ids, unencrypted_volume_ids = fetch_unencrypted_volumes()
    encrypt_attach_delete_volumes(instance_ids, unencrypted_volume_ids)
