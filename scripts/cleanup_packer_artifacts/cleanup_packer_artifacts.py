#!/usr/bin/env python3
import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def get_latest_ami_id(ssm_client, ssm_parameter_name):
    try:
        response = ssm_client.get_parameter(Name=ssm_parameter_name)
        return response['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            print(f"SSM Parameter {ssm_parameter_name} not found")
            return None
        print(f"Error retrieving latest AMI from SSM: {e}")
        return None


def get_latest_snapshot_ids(ec2_client, latest_ami_id):
    latest_snapshot_ids = set()

    if latest_ami_id:
        try:
            response = ec2_client.describe_images(ImageIds=[latest_ami_id])
            images = response.get('Images', [])
            if images:
                for block_device in images[0].get('BlockDeviceMappings', []):
                    if 'Ebs' in block_device:
                        snapshot_id = block_device['Ebs'].get('SnapshotId')
                        if snapshot_id:
                            latest_snapshot_ids.add(snapshot_id)
        except ClientError as e:
            print(f"Error retrieving snapshots for latest AMI: {e}")

    return latest_snapshot_ids


def cleanup_amis(ec2_client, latest_ami_id, dry_run):
    try:
        response = ec2_client.describe_images(
            Owners=['self'],
            Filters=[
                {'Name': 'name', 'Values': ['github-ec2-runner-*']},
                {'Name': 'state', 'Values': ['available', 'pending', 'failed']}
            ]
        )

        images = response.get('Images', [])
        deleted_count = 0

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

        return deleted_count
    except ClientError as e:
        print(f"Error listing AMIs: {e}")
        return 0


def cleanup_snapshots(ec2_client, latest_snapshot_ids, dry_run):
    try:
        response = ec2_client.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'description', 'Values': ['*github-ec2-runner-*']},
            ]
        )

        snapshots = response.get('Snapshots', [])
        deleted_count = 0

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

        return deleted_count
    except ClientError as e:
        print(f"Error listing snapshots: {e}")
        return 0


def cleanup_security_groups(ec2_client, dry_run):
    try:
        response = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': ['Packer*']},
            ]
        )

        security_groups = response.get('SecurityGroups', [])
        deleted_count = 0

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

        return deleted_count
    except ClientError as e:
        print(f"Error listing security groups: {e}")
        return 0


def cleanup_instances(ec2_client, dry_run):
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

        deleted_count = 0

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

        return deleted_count
    except ClientError as e:
        print(f"Error listing instances: {e}")
        return 0


def cleanup_key_pairs(ec2_client, dry_run):
    try:
        response = ec2_client.describe_key_pairs(
            Filters=[
                {'Name': 'key-name', 'Values': ['packer_*']}
            ]
        )

        key_pairs = response.get('KeyPairs', [])
        deleted_count = 0

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

        return deleted_count
    except ClientError as e:
        print(f"Error listing key pairs: {e}")
        return 0


def cleanup_volumes(ec2_client, dry_run):
    try:
        response = ec2_client.describe_volumes(
            Filters=[
                {'Name': 'status', 'Values': ['available']},
                {'Name': 'tag:Name', 'Values': ['Packer*']}
            ]
        )

        volumes = response.get('Volumes', [])
        deleted_count = 0

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

        return deleted_count
    except ClientError as e:
        print(f"Error listing volumes: {e}")
        return 0


def cleanup_ecr_old_images(ecr_client, repository_name, dry_run):
    try:
        response = ecr_client.describe_images(
            repositoryName=repository_name
        )

        image_details = response.get('imageDetails', [])
        sorted_images = sorted(image_details, key=lambda x: x.get('imagePushedAt'), reverse=True)
        images_to_delete = sorted_images[1:]

        deleted_count = 0

        if not images_to_delete:
            print("No old images to clean up (keeping latest image)")
            return deleted_count

        image_ids = [{'imageDigest': img['imageDigest']} for img in images_to_delete]

        if dry_run:
            print(f"[DRY RUN] Would delete {len(image_ids)} old images (keeping latest)")
            deleted_count = len(image_ids)
        else:
            batch_response = ecr_client.batch_delete_image(
                repositoryName=repository_name,
                imageIds=image_ids
            )
            deleted_count = len(batch_response.get('imageIds', []))
            print(f"Deleted {deleted_count} old images (kept latest)")

        return deleted_count
    except ClientError as e:
        print(f"Error cleaning up old images: {e}")
        return 0


def cleanup_docker_build_resources(ec2_client, dry_run):
    total_deleted = 0

    print("-" * 80)
    print("CLEANING UP DOCKER BUILD INSTANCES")
    print("-" * 80)
    count = cleanup_instances(ec2_client, dry_run)
    total_deleted += count
    print(f"Instances cleaned: {count}")
    print()

    print("-" * 80)
    print("CLEANING UP DOCKER BUILD VOLUMES")
    print("-" * 80)
    count = cleanup_volumes(ec2_client, dry_run)
    total_deleted += count
    print(f"Volumes cleaned: {count}")
    print()

    print("-" * 80)
    print("CLEANING UP DOCKER BUILD SECURITY GROUPS")
    print("-" * 80)
    count = cleanup_security_groups(ec2_client, dry_run)
    total_deleted += count
    print(f"Security groups cleaned: {count}")
    print()

    print("-" * 80)
    print("CLEANING UP DOCKER BUILD KEY PAIRS")
    print("-" * 80)
    count = cleanup_key_pairs(ec2_client, dry_run)
    total_deleted += count
    print(f"Key pairs cleaned: {count}")
    print()

    return total_deleted


def handle_ami_cleanup(args):
    ec2_client = boto3.client('ec2', region_name=args.region)
    ssm_client = boto3.client('ssm', region_name=args.region)

    resource_types = args.resource_types.lower()
    if resource_types == 'all':
        resource_types_set = {'amis', 'snapshots', 'security-groups', 'instances', 'key-pairs', 'volumes'}
    else:
        resource_types_set = set(rt.strip() for rt in resource_types.split(','))

    print("=" * 80)
    print("PACKER ARTIFACTS CLEANUP")
    print("=" * 80)
    print(f"Region: {args.region}")
    print(f"SSM Parameter: {args.ssm_parameter_name}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Resource Types: {', '.join(sorted(resource_types_set))}")
    print()

    latest_ami_id = get_latest_ami_id(ssm_client, args.ssm_parameter_name)
    if latest_ami_id:
        print(f"Protected latest AMI: {latest_ami_id}")
    else:
        print("No latest AMI found in SSM Parameter Store")
    print()

    latest_snapshot_ids = get_latest_snapshot_ids(ec2_client, latest_ami_id)
    if latest_snapshot_ids:
        print(f"Protected latest snapshots: {', '.join(sorted(latest_snapshot_ids))}")
    else:
        print("No latest snapshots found")
    print()

    total_deleted = 0

    if 'instances' in resource_types_set:
        print("-" * 80)
        print("CLEANING UP INSTANCES")
        print("-" * 80)
        count = cleanup_instances(ec2_client, args.dry_run)
        total_deleted += count
        print(f"Instances cleaned: {count}")
        print()

    if 'volumes' in resource_types_set:
        print("-" * 80)
        print("CLEANING UP VOLUMES")
        print("-" * 80)
        count = cleanup_volumes(ec2_client, args.dry_run)
        total_deleted += count
        print(f"Volumes cleaned: {count}")
        print()

    if 'amis' in resource_types_set:
        print("-" * 80)
        print("CLEANING UP AMIS")
        print("-" * 80)
        count = cleanup_amis(ec2_client, latest_ami_id, args.dry_run)
        total_deleted += count
        print(f"AMIs cleaned: {count}")
        print()

    if 'snapshots' in resource_types_set:
        print("-" * 80)
        print("CLEANING UP SNAPSHOTS")
        print("-" * 80)
        count = cleanup_snapshots(ec2_client, latest_snapshot_ids, args.dry_run)
        total_deleted += count
        print(f"Snapshots cleaned: {count}")
        print()

    if 'security-groups' in resource_types_set:
        print("-" * 80)
        print("CLEANING UP SECURITY GROUPS")
        print("-" * 80)
        count = cleanup_security_groups(ec2_client, args.dry_run)
        total_deleted += count
        print(f"Security groups cleaned: {count}")
        print()

    if 'key-pairs' in resource_types_set:
        print("-" * 80)
        print("CLEANING UP KEY PAIRS")
        print("-" * 80)
        count = cleanup_key_pairs(ec2_client, args.dry_run)
        total_deleted += count
        print(f"Key pairs cleaned: {count}")
        print()

    print("=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Total resources cleaned: {total_deleted}")
    if args.dry_run:
        print("\n[DRY RUN MODE - No resources were actually deleted]")
    print()

    return 0


def handle_docker_cleanup(args):
    ecr_client = boto3.client('ecr', region_name=args.region)
    ec2_client = boto3.client('ec2', region_name=args.region)

    print("=" * 80)
    print("DOCKER RUNNER CLEANUP")
    print("=" * 80)
    print(f"Region: {args.region}")
    print(f"Repository: {args.repository}")
    print(f"Dry Run: {args.dry_run}")
    print()

    total_deleted = 0

    print("-" * 80)
    print("CLEANING UP OLD ECR IMAGES")
    print("-" * 80)
    count = cleanup_ecr_old_images(ecr_client, args.repository, args.dry_run)
    total_deleted += count
    print()

    count = cleanup_docker_build_resources(ec2_client, args.dry_run)
    total_deleted += count

    print("=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Total resources cleaned: {total_deleted}")
    if args.dry_run:
        print("\n[DRY RUN MODE - No resources were actually deleted]")
    print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Cleanup AWS resources for GitHub runners'
    )
    subparsers = parser.add_subparsers(dest='command', help='Runner type to clean up')

    ec2_parser = subparsers.add_parser('ec2', help='Clean up EC2 runner artifacts (AMIs and Packer resources)')
    ec2_parser.add_argument(
        '--region',
        required=True,
        help='AWS region to clean up'
    )
    ec2_parser.add_argument(
        '--ssm-parameter-name',
        required=True,
        help='SSM parameter name containing latest AMI ID'
    )
    ec2_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    ec2_parser.add_argument(
        '--resource-types',
        default='all',
        help='Comma-separated list of resource types to clean (amis,snapshots,security-groups,instances,key-pairs,volumes) or "all" (default: all)'
    )

    docker_parser = subparsers.add_parser('docker', help='Clean up Docker runner images and build resources')
    docker_parser.add_argument(
        '--region',
        required=True,
        help='AWS region of ECR repository'
    )
    docker_parser.add_argument(
        '--repository',
        required=True,
        help='ECR repository name'
    )
    docker_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'ec2':
        return handle_ami_cleanup(args)
    if args.command == 'docker':
        return handle_docker_cleanup(args)
    return 1


if __name__ == '__main__':
    sys.exit(main())
