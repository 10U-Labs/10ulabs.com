#!/usr/bin/env python3
"""Script to clean up old AMIs, snapshots, and launch templates."""
import argparse
from dataclasses import dataclass
import json
import re
import sys

import boto3
from botocore.exceptions import ClientError


@dataclass
class AmiCleanupParams:
    """Parameters for AMI cleanup operations."""

    latest_ami_id: str
    latest_snapshot_ids: set
    dry_run: bool
    cleanup_snapshots_enabled: bool
    tags: dict
    exclude_tags: dict
    ami_name_prefix: str = ""


def has_excluded_tags(resource_tags, exclude_tags):
    """Check if a resource has any excluded tags."""
    if not exclude_tags:
        return False
    resource_tag_dict = {tag['Key']: tag['Value'] for tag in (resource_tags or [])}
    for key, value in exclude_tags.items():
        if resource_tag_dict.get(key) == value:
            return True
    return False


def get_latest_ami_id(ec2_client, purpose_tag, purpose_value, stable_tag, stable_value):
    """Get the latest stable AMI ID by querying EC2 directly."""
    result = None
    try:
        response = ec2_client.describe_images(
            Owners=['self'],
            Filters=[
                {'Name': f'tag:{purpose_tag}', 'Values': [purpose_value]},
                {'Name': f'tag:{stable_tag}', 'Values': [stable_value]},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        images = response.get('Images', [])
        if images:
            sorted_images = sorted(images, key=lambda x: x['CreationDate'], reverse=True)
            result = sorted_images[0]['ImageId']
            print(f"Found latest stable AMI: {result}")
        else:
            print("No stable AMI found matching tag filters")
    except ClientError as e:
        print(f"Error querying EC2 for latest AMI: {e}")
    return result


def get_latest_snapshot_ids(ec2_client, latest_ami_id):
    """Get snapshot IDs associated with the latest AMI."""
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
    """Get snapshot IDs from an AMI's block device mappings."""
    snapshot_ids = set()
    for block_device in image.get('BlockDeviceMappings', []):
        ebs = block_device.get('Ebs', {})
        snapshot_id = ebs.get('SnapshotId')
        if snapshot_id:
            snapshot_ids.add(snapshot_id)
    return snapshot_ids


def _collect_images_by_filter(ec2_client, filters, error_context="AMIs"):
    """Collect AMI images matching the specified filters."""
    images_by_id = {}
    all_filters = filters + [{'Name': 'state', 'Values': ['available', 'pending', 'failed']}]
    try:
        response = ec2_client.describe_images(Owners=['self'], Filters=all_filters)
        for image in response.get('Images', []):
            images_by_id[image['ImageId']] = image
    except ClientError as e:
        print(f"Error listing {error_context}: {e}")
    return images_by_id


def find_amis_by_tags(ec2_client, tags):
    """Find AMIs matching the specified tags."""
    images_by_id = {}
    for tag_key, tag_value in tags.items():
        filters = [{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
        images_by_id.update(_collect_images_by_filter(ec2_client, filters))
    return images_by_id


def find_amis_by_name_prefix(ec2_client, ami_name_prefix):
    """Find AMIs matching the specified name prefix."""
    if not ami_name_prefix:
        return {}
    filters = [{'Name': 'name', 'Values': [f'{ami_name_prefix}*']}]
    return _collect_images_by_filter(ec2_client, filters, "AMIs by name prefix")


def cleanup_amis(ec2_client, params: AmiCleanupParams):
    """Clean up old AMIs matching the specified tags or name prefix."""
    deleted_count = 0
    snapshots_to_delete = set()
    images_by_id = find_amis_by_tags(ec2_client, params.tags)
    images_by_id.update(find_amis_by_name_prefix(ec2_client, params.ami_name_prefix))
    for image in images_by_id.values():
        image_id = image['ImageId']
        if image_id == params.latest_ami_id:
            print(f"Skipping latest AMI: {image_id}")
            continue
        if has_excluded_tags(image.get('Tags', []), params.exclude_tags):
            print(f"Skipping protected AMI: {image_id} ({image.get('Name', 'N/A')})")
            continue
        ami_snapshot_ids = get_snapshot_ids_for_ami(image)
        if params.cleanup_snapshots_enabled:
            snapshots_to_delete.update(ami_snapshot_ids - params.latest_snapshot_ids)
        try:
            if params.dry_run:
                print(f"[DRY RUN] Would deregister AMI: {image_id} ({image.get('Name', 'N/A')})")
            else:
                ec2_client.deregister_image(ImageId=image_id)
                print(f"Deregistered AMI: {image_id} ({image.get('Name', 'N/A')})")
            deleted_count += 1
        except ClientError as e:
            print(f"Error deregistering AMI {image_id}: {e}")
    return deleted_count, snapshots_to_delete


def cleanup_snapshots(ec2_client, snapshot_ids_to_delete, dry_run):
    """Delete snapshots from the provided set."""
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
    """Extract AMI ID from a snapshot description."""
    result = None
    match = re.search(r'for (ami-[a-f0-9]+)', description)
    if match:
        result = match.group(1)
    return result


def get_existing_ami_ids(ec2_client):
    """Get all existing AMI IDs owned by self."""
    existing_ami_ids = set()
    try:
        response = ec2_client.describe_images(Owners=['self'])
        for image in response.get('Images', []):
            existing_ami_ids.add(image['ImageId'])
    except ClientError as e:
        print(f"Error listing AMIs: {e}")
    return existing_ami_ids


def find_orphaned_snapshots(ec2_client, latest_snapshot_ids):
    """Find snapshots that are not associated with any existing AMI."""
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


def cleanup_security_groups(ec2_client, dry_run, tags, exclude_tags):
    """Clean up security groups matching the specified tags."""
    deleted_count = 0
    sgs_by_id = {}
    for tag_key, tag_value in tags.items():
        try:
            response = ec2_client.describe_security_groups(
                Filters=[
                    {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
                ]
            )
            for sg in response.get('SecurityGroups', []):
                sgs_by_id[sg['GroupId']] = sg
        except ClientError as e:
            print(f"Error listing security groups: {e}")
    for sg in sgs_by_id.values():
        sg_id = sg['GroupId']
        sg_name = sg['GroupName']
        if has_excluded_tags(sg.get('Tags', []), exclude_tags):
            print(f"Skipping protected security group: {sg_id} ({sg_name})")
            continue
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
    return deleted_count


def cleanup_key_pairs(ec2_client, dry_run, tags, exclude_tags):
    """Clean up key pairs matching the specified tags."""
    deleted_count = 0
    kps_by_name = {}
    for tag_key, tag_value in tags.items():
        try:
            response = ec2_client.describe_key_pairs(
                Filters=[
                    {'Name': f'tag:{tag_key}', 'Values': [tag_value]}
                ]
            )
            for key_pair in response.get('KeyPairs', []):
                kps_by_name[key_pair['KeyName']] = key_pair
        except ClientError as e:
            print(f"Error listing key pairs: {e}")
    for key_pair in kps_by_name.values():
        key_name = key_pair['KeyName']
        if has_excluded_tags(key_pair.get('Tags', []), exclude_tags):
            print(f"Skipping protected key pair: {key_name}")
            continue
        try:
            if dry_run:
                print(f"[DRY RUN] Would delete key pair: {key_name}")
            else:
                ec2_client.delete_key_pair(KeyName=key_name)
                print(f"Deleted key pair: {key_name}")
            deleted_count += 1
        except ClientError as e:
            print(f"Error deleting key pair {key_name}: {e}")
    return deleted_count


def cleanup_instances(ec2_client, dry_run, tags, exclude_tags):
    """Terminate instances matching the specified tags."""
    deleted_count = 0
    instances_by_id = {}
    for tag_key, tag_value in tags.items():
        try:
            response = ec2_client.describe_instances(
                Filters=[
                    {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running', 'stopped', 'stopping', 'pending'],
                    },
                ]
            )
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances_by_id[instance['InstanceId']] = instance
        except ClientError as e:
            print(f"Error listing instances: {e}")
    for instance_id, instance in instances_by_id.items():
        if has_excluded_tags(instance.get('Tags', []), exclude_tags):
            print(f"Skipping protected instance: {instance_id}")
            continue
        try:
            if dry_run:
                print(f"[DRY RUN] Would terminate instance: {instance_id}")
            else:
                ec2_client.terminate_instances(InstanceIds=[instance_id])
                print(f"Terminated instance: {instance_id}")
            deleted_count += 1
        except ClientError as e:
            print(f"Error terminating instance {instance_id}: {e}")
    return deleted_count


def cleanup_launch_templates(ec2_client, dry_run, tags, exclude_tags):
    """Clean up launch templates matching the specified tags."""
    deleted_count = 0
    lts_by_id = {}
    for tag_key, tag_value in tags.items():
        try:
            response = ec2_client.describe_launch_templates(
                Filters=[
                    {'Name': f'tag:{tag_key}', 'Values': [tag_value]}
                ]
            )
            for lt in response.get('LaunchTemplates', []):
                lts_by_id[lt['LaunchTemplateId']] = lt
        except ClientError as e:
            print(f"Error listing launch templates: {e}")
    for lt in lts_by_id.values():
        lt_id = lt['LaunchTemplateId']
        lt_name = lt['LaunchTemplateName']
        if has_excluded_tags(lt.get('Tags', []), exclude_tags):
            print(f"Skipping protected launch template: {lt_id} ({lt_name})")
            continue
        try:
            if dry_run:
                print(f"[DRY RUN] Would delete launch template: {lt_id} ({lt_name})")
            else:
                ec2_client.delete_launch_template(LaunchTemplateId=lt_id)
                print(f"Deleted launch template: {lt_id} ({lt_name})")
            deleted_count += 1
        except ClientError as e:
            print(f"Error deleting launch template {lt_id}: {e}")
    return deleted_count


def run_cleanup(label, cleanup_fn):
    """Run a cleanup function and print the results."""
    print("-" * 80)
    print(f"CLEANING UP {label}")
    print("-" * 80)
    count = cleanup_fn()
    print(f"{label.title()} cleaned: {count}")
    print()
    return count


def load_config(config_path):
    """Load configuration from a JSON file."""
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def print_header(args, resource_types_set, tags, exclude_tags, ami_name_prefix):
    """Print the cleanup header information."""
    print("=" * 80)
    print("EC2 RUNNER IMAGE CLEANUP")
    print("=" * 80)
    print(f"Region: {args.region}")
    print(f"Purpose Tag: {args.purpose_tag}={args.purpose_value}")
    print(f"Stable Tag: {args.stable_tag}")
    if tags:
        print(f"Tag Filters: {', '.join(f'{k}={v}' for k, v in tags.items())}")
    if ami_name_prefix:
        print(f"AMI Name Prefix: {ami_name_prefix}*")
    if exclude_tags:
        print(f"Excluded Tags: {', '.join(f'{k}={v}' for k, v in exclude_tags.items())}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Resource Types: {', '.join(sorted(resource_types_set))}")
    print()


def print_protected_resources(latest_ami_id, latest_snapshot_ids):
    """Print information about protected resources."""
    if latest_ami_id:
        print(f"Protected latest AMI: {latest_ami_id}")
    else:
        print("No stable AMI found matching tag filters")
    print()
    if latest_snapshot_ids:
        print(f"Protected latest snapshots: {', '.join(sorted(latest_snapshot_ids))}")
    else:
        print("No latest snapshots found")
    print()


def print_summary(total_deleted, dry_run):
    """Print the cleanup summary."""
    print("=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Total resources cleaned: {total_deleted}")
    if dry_run:
        print("\n[DRY RUN MODE - No resources were actually deleted]")
    print()


def parse_tags(tag_list):
    """Parse KEY=VALUE tag arguments into a dictionary."""
    tags = {}
    for item in tag_list or []:
        if '=' in item:
            key, value = item.split('=', 1)
            tags[key] = value
    return tags


def get_resource_types(args):
    """Parse resource types from arguments."""
    if args.resource_types.lower() == 'all':
        return {
            'amis', 'snapshots', 'instances', 'security-groups',
            'key-pairs', 'launch-templates',
        }
    return set(rt.strip() for rt in args.resource_types.lower().split(','))


def handle_ami_cleanup(args):
    """Handle the main cleanup process based on command line arguments."""
    ec2_client = boto3.client('ec2', region_name=args.region)

    file_config = load_config(args.config)
    tags = {**file_config.get('tags', {}), **parse_tags(args.tag)}
    ami_name_prefix = file_config.get('ami_name_prefix', '')
    if not tags and not ami_name_prefix:
        print("Error: No tags or ami_name_prefix found in config file")
        return 1

    exclude_tags = parse_tags(args.exclude_tag)
    resource_types_set = get_resource_types(args)

    print_header(args, resource_types_set, tags, exclude_tags, ami_name_prefix)

    latest_ami_id = get_latest_ami_id(
        ec2_client, args.purpose_tag, args.purpose_value,
        args.stable_tag, args.stable_value
    )
    latest_snapshot_ids = get_latest_snapshot_ids(ec2_client, latest_ami_id)
    print_protected_resources(latest_ami_id, latest_snapshot_ids)

    total_deleted = 0
    snapshots_to_delete = set()

    if 'amis' in resource_types_set:
        print("-" * 80)
        print("CLEANING UP AMIS")
        print("-" * 80)
        ami_result, snapshots_to_delete = cleanup_amis(ec2_client, AmiCleanupParams(
            latest_ami_id=latest_ami_id,
            latest_snapshot_ids=latest_snapshot_ids,
            dry_run=args.dry_run,
            cleanup_snapshots_enabled='snapshots' in resource_types_set,
            tags=tags,
            exclude_tags=exclude_tags,
            ami_name_prefix=ami_name_prefix
        ))
        print(f"Amis cleaned: {ami_result}")
        print()
        total_deleted += ami_result

    if 'snapshots' in resource_types_set:
        orphaned_snapshots = find_orphaned_snapshots(ec2_client, latest_snapshot_ids)
        all_snapshots_to_delete = snapshots_to_delete | orphaned_snapshots
        if orphaned_snapshots:
            print(f"Found {len(orphaned_snapshots)} orphaned snapshot(s)")
        total_deleted += run_cleanup(
            'SNAPSHOTS',
            lambda: cleanup_snapshots(ec2_client, all_snapshots_to_delete, args.dry_run)
        )

    if 'instances' in resource_types_set:
        total_deleted += run_cleanup(
            'INSTANCES',
            lambda: cleanup_instances(ec2_client, args.dry_run, tags, exclude_tags)
        )

    if 'launch-templates' in resource_types_set:
        total_deleted += run_cleanup(
            'LAUNCH TEMPLATES',
            lambda: cleanup_launch_templates(ec2_client, args.dry_run, tags, exclude_tags)
        )

    if 'security-groups' in resource_types_set:
        total_deleted += run_cleanup(
            'SECURITY GROUPS',
            lambda: cleanup_security_groups(ec2_client, args.dry_run, tags, exclude_tags)
        )

    if 'key-pairs' in resource_types_set:
        total_deleted += run_cleanup(
            'KEY PAIRS',
            lambda: cleanup_key_pairs(ec2_client, args.dry_run, tags, exclude_tags)
        )

    print_summary(total_deleted, args.dry_run)
    return 0


def main():
    """Parse command line arguments and run the cleanup."""
    parser = argparse.ArgumentParser(
        description='Cleanup old AMIs and snapshots for GitHub EC2 runners'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to config file containing tags to filter resources'
    )
    parser.add_argument(
        '--region',
        required=True,
        help='AWS region to clean up'
    )
    parser.add_argument(
        '--purpose-tag',
        required=True,
        help='Tag key identifying AMI purpose (e.g., Purpose)'
    )
    parser.add_argument(
        '--purpose-value',
        required=True,
        help='Tag value identifying AMI purpose (e.g., GitHub self-hosted EC2 runner)'
    )
    parser.add_argument(
        '--stable-tag',
        required=True,
        help='Tag key identifying stable AMIs (e.g., Stable)'
    )
    parser.add_argument(
        '--stable-value',
        required=True,
        help='Tag value identifying stable AMIs (e.g., true)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--resource-types',
        default='all',
        help='Resource types to clean: amis,snapshots,instances,etc. (default: all)'
    )
    parser.add_argument(
        '--tag',
        action='append',
        metavar='KEY=VALUE',
        help='Additional tag filter (can be repeated). Matching resources deleted.'
    )
    parser.add_argument(
        '--exclude-tag',
        action='append',
        metavar='KEY=VALUE',
        help='Exclude resources with tag (can be repeated). Excluded resources skipped.'
    )

    args = parser.parse_args()
    return handle_ami_cleanup(args)


if __name__ == '__main__':
    sys.exit(main())
