#!/usr/bin/env python3
import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def get_latest_ami_id(ssm_client, ssm_parameter_name):
    result = None
    try:
        response = ssm_client.get_parameter(Name=ssm_parameter_name)
        result = response['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            print(f"SSM Parameter {ssm_parameter_name} not found")
        else:
            print(f"Error retrieving latest AMI from SSM: {e}")
    return result


def get_latest_snapshot_ids(ec2_client, latest_ami_id):
    latest_snapshot_ids = set()
    if latest_ami_id:
        try:
            response = ec2_client.describe_images(ImageIds=[latest_ami_id])
            images = response.get('Images', [])
            if images:
                for block_device in images[0].get('BlockDeviceMappings', []):
                    ebs = block_device.get('Ebs', {})
                    snapshot_id = ebs.get('SnapshotId')
                    if snapshot_id:
                        latest_snapshot_ids.add(snapshot_id)
        except ClientError as e:
            print(f"Error retrieving snapshots for latest AMI: {e}")
    return latest_snapshot_ids


def cleanup_amis(ec2_client, latest_ami_id, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_images(
            Owners=['self'],
            Filters=[
                {'Name': 'name', 'Values': ['github-ec2-runner-*']},
                {'Name': 'state', 'Values': ['available', 'pending', 'failed']}
            ]
        )
        images = response.get('Images', [])
        for image in images:
            image_id = image['ImageId']
            if image_id == latest_ami_id:
                print(f"Skipping latest AMI: {image_id}")
                continue
            try:
                if dry_run:
                    print(f"[DRY RUN] Would deregister AMI: {image_id} ({image.get('Name', 'N/A')})")
                else:
                    ec2_client.deregister_image(ImageId=image_id)
                    print(f"Deregistered AMI: {image_id} ({image.get('Name', 'N/A')})")
                deleted_count += 1
            except ClientError as e:
                print(f"Error deregistering AMI {image_id}: {e}")
    except ClientError as e:
        print(f"Error listing AMIs: {e}")
    return deleted_count


def cleanup_snapshots(ec2_client, latest_snapshot_ids, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'description', 'Values': ['*github-ec2-runner-*']},
            ]
        )
        snapshots = response.get('Snapshots', [])
        for snapshot in snapshots:
            snapshot_id = snapshot['SnapshotId']
            if snapshot_id in latest_snapshot_ids:
                print(f"Skipping latest snapshot: {snapshot_id}")
                continue
            try:
                if dry_run:
                    print(f"[DRY RUN] Would delete snapshot: {snapshot_id} ({snapshot.get('Description', 'N/A')})")
                else:
                    ec2_client.delete_snapshot(SnapshotId=snapshot_id)
                    print(f"Deleted snapshot: {snapshot_id} ({snapshot.get('Description', 'N/A')})")
                deleted_count += 1
            except ClientError as e:
                print(f"Error deleting snapshot {snapshot_id}: {e}")
    except ClientError as e:
        print(f"Error listing snapshots: {e}")
    return deleted_count


def cleanup_security_groups(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': ['Packer*']},
            ]
        )
        security_groups = response.get('SecurityGroups', [])
        for sg in security_groups:
            sg_id = sg['GroupId']
            sg_name = sg['GroupName']
            try:
                if dry_run:
                    print(f"[DRY RUN] Would delete security group: {sg_id} ({sg_name})")
                else:
                    ec2_client.delete_security_group(GroupId=sg_id)
                    print(f"Deleted security group: {sg_id} ({sg_name})")
                deleted_count += 1
            except ClientError as e:
                if e.response['Error']['Code'] == 'DependencyViolation':
                    print(f"Cannot delete security group {sg_id} ({sg_name}): Still in use")
                else:
                    print(f"Error deleting security group {sg_id}: {e}")
    except ClientError as e:
        print(f"Error listing security groups: {e}")
    return deleted_count


def cleanup_instances(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': ['Packer*']},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping', 'pending']}
            ]
        )
        instance_ids = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_ids.append(instance['InstanceId'])
        for instance_id in instance_ids:
            try:
                if dry_run:
                    print(f"[DRY RUN] Would terminate instance: {instance_id}")
                else:
                    ec2_client.terminate_instances(InstanceIds=[instance_id])
                    print(f"Terminated instance: {instance_id}")
                deleted_count += 1
            except ClientError as e:
                print(f"Error terminating instance {instance_id}: {e}")
    except ClientError as e:
        print(f"Error listing instances: {e}")
    return deleted_count


def cleanup_key_pairs(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_key_pairs(
            Filters=[
                {'Name': 'key-name', 'Values': ['packer_*']}
            ]
        )
        key_pairs = response.get('KeyPairs', [])
        for key_pair in key_pairs:
            key_name = key_pair['KeyName']
            try:
                if dry_run:
                    print(f"[DRY RUN] Would delete key pair: {key_name}")
                else:
                    ec2_client.delete_key_pair(KeyName=key_name)
                    print(f"Deleted key pair: {key_name}")
                deleted_count += 1
            except ClientError as e:
                print(f"Error deleting key pair {key_name}: {e}")
    except ClientError as e:
        print(f"Error listing key pairs: {e}")
    return deleted_count


def cleanup_volumes(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_volumes(
            Filters=[
                {'Name': 'status', 'Values': ['available']},
                {'Name': 'tag:Name', 'Values': ['Packer*']}
            ]
        )
        volumes = response.get('Volumes', [])
        for volume in volumes:
            volume_id = volume['VolumeId']
            try:
                if dry_run:
                    print(f"[DRY RUN] Would delete volume: {volume_id}")
                else:
                    ec2_client.delete_volume(VolumeId=volume_id)
                    print(f"Deleted volume: {volume_id}")
                deleted_count += 1
            except ClientError as e:
                print(f"Error deleting volume {volume_id}: {e}")
    except ClientError as e:
        print(f"Error listing volumes: {e}")
    return deleted_count


def run_cleanup(label, cleanup_fn):
    print("-" * 80)
    print(f"CLEANING UP {label}")
    print("-" * 80)
    count = cleanup_fn()
    print(f"{label.title()} cleaned: {count}")
    print()
    return count


def print_header(args, resource_types_set):
    print("=" * 80)
    print("PACKER ARTIFACTS CLEANUP")
    print("=" * 80)
    print(f"Region: {args.region}")
    print(f"SSM Parameter: {args.ssm_parameter_name}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Resource Types: {', '.join(sorted(resource_types_set))}")
    print()


def print_protected_resources(latest_ami_id, latest_snapshot_ids):
    if latest_ami_id:
        print(f"Protected latest AMI: {latest_ami_id}")
    else:
        print("No latest AMI found in SSM Parameter Store")
    print()
    if latest_snapshot_ids:
        print(f"Protected latest snapshots: {', '.join(sorted(latest_snapshot_ids))}")
    else:
        print("No latest snapshots found")
    print()


def print_summary(total_deleted, dry_run):
    print("=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Total resources cleaned: {total_deleted}")
    if dry_run:
        print("\n[DRY RUN MODE - No resources were actually deleted]")
    print()


def handle_ami_cleanup(args):
    ec2_client = boto3.client('ec2', region_name=args.region)
    ssm_client = boto3.client('ssm', region_name=args.region)

    resource_types = args.resource_types.lower()
    if resource_types == 'all':
        resource_types_set = {'amis', 'snapshots', 'security-groups', 'instances', 'key-pairs', 'volumes'}
    else:
        resource_types_set = set(rt.strip() for rt in resource_types.split(','))

    print_header(args, resource_types_set)

    latest_ami_id = get_latest_ami_id(ssm_client, args.ssm_parameter_name)
    latest_snapshot_ids = get_latest_snapshot_ids(ec2_client, latest_ami_id)
    print_protected_resources(latest_ami_id, latest_snapshot_ids)

    cleanup_tasks = [
        ('instances', 'INSTANCES', lambda: cleanup_instances(ec2_client, args.dry_run)),
        ('volumes', 'VOLUMES', lambda: cleanup_volumes(ec2_client, args.dry_run)),
        ('amis', 'AMIS', lambda: cleanup_amis(ec2_client, latest_ami_id, args.dry_run)),
        ('snapshots', 'SNAPSHOTS', lambda: cleanup_snapshots(ec2_client, latest_snapshot_ids, args.dry_run)),
        ('security-groups', 'SECURITY GROUPS', lambda: cleanup_security_groups(ec2_client, args.dry_run)),
        ('key-pairs', 'KEY PAIRS', lambda: cleanup_key_pairs(ec2_client, args.dry_run)),
    ]

    total_deleted = 0
    for resource_type, label, cleanup_fn in cleanup_tasks:
        if resource_type in resource_types_set:
            total_deleted += run_cleanup(label, cleanup_fn)

    print_summary(total_deleted, args.dry_run)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Cleanup Packer artifacts for GitHub EC2 runners'
    )
    parser.add_argument(
        '--region',
        required=True,
        help='AWS region to clean up'
    )
    parser.add_argument(
        '--ssm-parameter-name',
        required=True,
        help='SSM parameter name containing latest AMI ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--resource-types',
        default='all',
        help='Comma-separated list of resource types to clean (amis,snapshots,security-groups,instances,key-pairs,volumes) or "all" (default: all)'
    )

    args = parser.parse_args()
    return handle_ami_cleanup(args)


if __name__ == '__main__':
    sys.exit(main())
