#!/usr/bin/env python3
import argparse
import re
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


def get_snapshot_ids_for_ami(image):
    snapshot_ids = set()
    for block_device in image.get('BlockDeviceMappings', []):
        ebs = block_device.get('Ebs', {})
        snapshot_id = ebs.get('SnapshotId')
        if snapshot_id:
            snapshot_ids.add(snapshot_id)
    return snapshot_ids


def cleanup_amis(ec2_client, latest_ami_id, latest_snapshot_ids, dry_run, cleanup_snapshots_enabled):
    deleted_count = 0
    snapshots_to_delete = set()
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
            ami_snapshot_ids = get_snapshot_ids_for_ami(image)
            if cleanup_snapshots_enabled:
                snapshots_to_delete.update(ami_snapshot_ids - latest_snapshot_ids)
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
    return deleted_count, snapshots_to_delete


def cleanup_snapshots(ec2_client, snapshot_ids_to_delete, dry_run):
    deleted_count = 0
    for snapshot_id in sorted(snapshot_ids_to_delete):
        try:
            if dry_run:
                print(f"[DRY RUN] Would delete snapshot: {snapshot_id}")
            else:
                ec2_client.delete_snapshot(SnapshotId=snapshot_id)
                print(f"Deleted snapshot: {snapshot_id}")
            deleted_count += 1
        except ClientError as e:
            print(f"Error deleting snapshot {snapshot_id}: {e}")
    return deleted_count


def extract_ami_id_from_description(description):
    match = re.search(r'for (ami-[a-f0-9]+)', description)
    if match:
        return match.group(1)
    return None


def get_existing_ami_ids(ec2_client):
    existing_ami_ids = set()
    try:
        response = ec2_client.describe_images(Owners=['self'])
        for image in response.get('Images', []):
            existing_ami_ids.add(image['ImageId'])
    except ClientError as e:
        print(f"Error listing AMIs: {e}")
    return existing_ami_ids


def find_orphaned_snapshots(ec2_client, latest_snapshot_ids):
    orphaned_snapshots = set()
    existing_ami_ids = get_existing_ami_ids(ec2_client)
    try:
        response = ec2_client.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'description', 'Values': ['Created by CreateImage*']},
            ]
        )
        snapshots = response.get('Snapshots', [])
        for snapshot in snapshots:
            snapshot_id = snapshot['SnapshotId']
            if snapshot_id in latest_snapshot_ids:
                continue
            description = snapshot.get('Description', '')
            ami_id = extract_ami_id_from_description(description)
            if ami_id and ami_id not in existing_ami_ids:
                orphaned_snapshots.add(snapshot_id)
    except ClientError as e:
        print(f"Error listing snapshots: {e}")
    return orphaned_snapshots


def cleanup_security_groups(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': ['ami-builder-*']},
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


def cleanup_key_pairs(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_key_pairs(
            Filters=[
                {'Name': 'key-name', 'Values': ['ami-builder-*']}
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


def cleanup_instances(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'key-name', 'Values': ['ami-builder-*']},
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


def cleanup_launch_templates(ec2_client, dry_run):
    deleted_count = 0
    try:
        response = ec2_client.describe_launch_templates(
            Filters=[
                {'Name': 'launch-template-name', 'Values': ['ami-builder-*']}
            ]
        )
        launch_templates = response.get('LaunchTemplates', [])
        for lt in launch_templates:
            lt_id = lt['LaunchTemplateId']
            lt_name = lt['LaunchTemplateName']
            try:
                if dry_run:
                    print(f"[DRY RUN] Would delete launch template: {lt_id} ({lt_name})")
                else:
                    ec2_client.delete_launch_template(LaunchTemplateId=lt_id)
                    print(f"Deleted launch template: {lt_id} ({lt_name})")
                deleted_count += 1
            except ClientError as e:
                print(f"Error deleting launch template {lt_id}: {e}")
    except ClientError as e:
        print(f"Error listing launch templates: {e}")
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
    print("EC2 RUNNER IMAGE CLEANUP")
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
        resource_types_set = {'amis', 'snapshots', 'instances', 'security-groups', 'key-pairs', 'launch-templates'}
    else:
        resource_types_set = set(rt.strip() for rt in resource_types.split(','))

    print_header(args, resource_types_set)

    latest_ami_id = get_latest_ami_id(ssm_client, args.ssm_parameter_name)
    latest_snapshot_ids = get_latest_snapshot_ids(ec2_client, latest_ami_id)
    print_protected_resources(latest_ami_id, latest_snapshot_ids)

    total_deleted = 0
    snapshots_to_delete = set()

    if 'amis' in resource_types_set:
        cleanup_snapshots_enabled = 'snapshots' in resource_types_set
        print("-" * 80)
        print("CLEANING UP AMIS")
        print("-" * 80)
        ami_count, snapshots_to_delete = cleanup_amis(
            ec2_client, latest_ami_id, latest_snapshot_ids, args.dry_run, cleanup_snapshots_enabled
        )
        print(f"Amis cleaned: {ami_count}")
        print()
        total_deleted += ami_count

    if 'snapshots' in resource_types_set:
        orphaned_snapshots = find_orphaned_snapshots(ec2_client, latest_snapshot_ids)
        all_snapshots_to_delete = snapshots_to_delete | orphaned_snapshots
        if orphaned_snapshots:
            print(f"Found {len(orphaned_snapshots)} orphaned snapshot(s)")
        total_deleted += run_cleanup('SNAPSHOTS', lambda: cleanup_snapshots(ec2_client, all_snapshots_to_delete, args.dry_run))

    if 'instances' in resource_types_set:
        total_deleted += run_cleanup('INSTANCES', lambda: cleanup_instances(ec2_client, args.dry_run))

    if 'launch-templates' in resource_types_set:
        total_deleted += run_cleanup('LAUNCH TEMPLATES', lambda: cleanup_launch_templates(ec2_client, args.dry_run))

    if 'security-groups' in resource_types_set:
        total_deleted += run_cleanup('SECURITY GROUPS', lambda: cleanup_security_groups(ec2_client, args.dry_run))

    if 'key-pairs' in resource_types_set:
        total_deleted += run_cleanup('KEY PAIRS', lambda: cleanup_key_pairs(ec2_client, args.dry_run))

    print_summary(total_deleted, args.dry_run)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Cleanup old AMIs and snapshots for GitHub EC2 runners'
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
        help='Comma-separated list of resource types to clean (amis,snapshots,instances,security-groups,key-pairs,launch-templates) or "all" (default: all)'
    )

    args = parser.parse_args()
    return handle_ami_cleanup(args)


if __name__ == '__main__':
    sys.exit(main())
