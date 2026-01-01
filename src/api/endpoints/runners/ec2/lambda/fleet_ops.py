"""EC2 Fleet operations for launching GitHub runners."""
import base64
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

from botocore.exceptions import ClientError

from aws_clients import get_ec2_client
from github_runner_api import (
    build_runner_labels,
    cleanup_offline_runners,
    get_existing_runner_for_workflow,
    get_github_token,
    get_runner_registration_token,
)
from infra_validation import ensure_dependencies_valid, get_api_key
from runner_labels import (
    LabelParseError,
    LabelValidationError,
    get_instance_type,
    is_spot,
    parse_labels,
    validate_labels,
)

logger = logging.getLogger()


def create_ec2_user_data(
        registration_token: str, job_labels: List[str],
        github_repo: str, runner_name: str) -> str:
    """Generate EC2 user data script for GitHub runner configuration."""
    aws_region = os.environ['AWS_REGION']
    runner_labels = ','.join(job_labels)
    return f"""#!/bin/bash
set -e

INSTANCE_STORE=$(lsblk -dn -o NAME,TYPE | awk '$2=="disk" {{print "/dev/"$1}}' | while read dev; do
    if [ -z "$(lsblk -n "$dev" -o MOUNTPOINT 2>/dev/null | tr -d ' ')" ]; then
        echo "$dev"
        break
    fi
done)

mkfs.ext4 -F "$INSTANCE_STORE"
mount "$INSTANCE_STORE" /mnt
cp -a /home/github-runner/. /mnt/
umount /mnt
mount "$INSTANCE_STORE" /home/github-runner
chown -R github-runner:github-runner /home/github-runner

# Start CloudWatch agent for memory metrics
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

cd /home/github-runner/actions-runner

sudo -u github-runner ./config.sh \
    --url "https://github.com/{github_repo}" \
    --token "{registration_token}" \
    --name "{runner_name}" \
    --labels "{runner_labels}" \
    --unattended \
    --ephemeral

sudo -u github-runner ./run.sh

INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
aws ec2 terminate-instances \
    --instance-ids "$INSTANCE_ID" \
    --region {aws_region} \
    || shutdown -h now
"""


def get_latest_ami() -> str:
    """Get the latest available AMI for EC2 runners."""
    ami_purpose_tag = os.environ['EC2_AMI_PURPOSE_TAG']
    ami_purpose_value = os.environ['EC2_AMI_PURPOSE_VALUE']
    ami_stable_tag = os.environ['EC2_AMI_STABLE_TAG']
    try:
        response = get_ec2_client().describe_images(
            Owners=['self'],
            Filters=[
                {'Name': f'tag:{ami_purpose_tag}', 'Values': [ami_purpose_value]},
                {'Name': f'tag:{ami_stable_tag}', 'Values': ['true']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )

        if not response['Images']:
            logger.warning("No available AMI found")
            return ''

        images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
        latest_ami_id = images[0]['ImageId']
        logger.info("Found latest AMI: %s", latest_ami_id)
        return latest_ami_id
    except ClientError as e:
        logger.error("Error getting latest AMI: %s", e)
        return ''


def trigger_ami_creation() -> Dict[str, Any]:
    """Trigger AMI creation via the image-for-ec2-runners endpoint."""
    api_fqdn = os.environ['API_FQDN']
    ami_creation_url = f"https://{api_fqdn}/v1/runners/ec2/images"

    try:
        api_key = get_api_key()
        req = urllib.request.Request(
            ami_creation_url,
            data=json.dumps({}).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'x-api-key': api_key},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            logger.info("AMI creation triggered successfully: %s", result)
            return {'success': True, 'result': result}
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, ClientError) as e:
        logger.error("Failed to trigger AMI creation: %s", e)
        return {'success': False, 'error': str(e)}


def get_ec2_config() -> Dict[str, Any]:
    """Get EC2 configuration from environment variables."""
    return {
        'subnet_ids': os.environ['SUBNETS'].split(','),
        'security_group_id': os.environ['SECURITY_GROUPS'],
        'instance_types': os.environ['EC2_INSTANCE_TYPES'].split(','),
        'iam_instance_profile': os.environ['EC2_IAM_INSTANCE_PROFILE']
    }


def _get_instance_type_from_labels(job_labels: List[str]) -> str | None:
    """Determine the EC2 instance type from job labels."""
    try:
        parsed = parse_labels(job_labels)
        validate_labels(parsed)
        return get_instance_type(parsed)
    except (LabelParseError, LabelValidationError) as e:
        logger.warning("Could not parse labels for instance type: %s", e)
        return None


def _is_spot_from_labels(job_labels: List[str]) -> bool:
    """Determine if spot pricing should be used from job labels."""
    try:
        parsed = parse_labels(job_labels)
        validate_labels(parsed)
        return is_spot(parsed)
    except (LabelParseError, LabelValidationError) as e:
        logger.warning("Could not parse labels for pricing, defaulting to spot: %s", e)
        return True


def wait_for_instance_describable(instance_id: str, max_attempts: int = 3) -> Dict[str, Any]:
    """Wait for an EC2 instance to become describable after launch."""
    ec2 = get_ec2_client()
    attempt = 0
    while attempt < max_attempts:
        try:
            response = ec2.describe_instances(InstanceIds=[instance_id])
            if response['Reservations'] and response['Reservations'][0]['Instances']:
                return response['Reservations'][0]['Instances'][0]
        except ClientError as e:
            if e.response['Error']['Code'] != 'InvalidInstanceID.NotFound':
                raise
        wait_time = 2 ** (attempt + 3)
        time.sleep(wait_time)
        attempt = attempt + 1
    msg = f'Instance {instance_id} not found after {max_attempts} attempts'
    raise ClientError(
        {'Error': {'Code': 'InvalidInstanceID.NotFound', 'Message': msg}},
        'DescribeInstances'
    )


def create_fleet_launch_template(template_config: Dict[str, Any]) -> str:
    """Create a launch template for EC2 Fleet."""
    ec2 = get_ec2_client()
    template_name = f"github-runner-fleet-{template_config['job_id']}"
    run_id = template_config.get('run_id')
    runner_type = template_config.get('runner_type', 'ec2')
    try:
        response = ec2.create_launch_template(
            LaunchTemplateName=template_name,
            LaunchTemplateData={
                'ImageId': template_config['ami_id'],
                'SecurityGroupIds': [template_config['security_group_id']],
                'IamInstanceProfile': {'Name': template_config['iam_instance_profile']},
                'UserData': template_config['user_data_base64'],
                'BlockDeviceMappings': [{
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': 64,
                        'VolumeType': 'gp3',
                        'DeleteOnTermination': True
                    }
                }],
                'MetadataOptions': {
                    'HttpTokens': 'required',
                    'HttpEndpoint': 'enabled'
                },
                'TagSpecifications': [{
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f"github-runner-ec2-{template_config['job_id']}"},
                        {'Key': 'Type', 'Value': 'workflow-runner'},
                        {'Key': 'ManagedBy', 'Value': os.environ['EC2_MANAGED_BY_TAG']},
                        {'Key': 'GitHubJobId', 'Value': str(template_config['job_id'])},
                        {'Key': 'JobLabels', 'Value': ','.join(template_config['job_labels'])},
                        {'Key': 'GitHubRepo', 'Value': template_config['github_repo']},
                        {'Key': 'RunId', 'Value': str(run_id) if run_id else ''},
                        {'Key': 'RunnerType', 'Value': runner_type}
                    ]
                }]
            }
        )
        return response['LaunchTemplate']['LaunchTemplateId']
    except ClientError as e:
        logger.error("Failed to create launch template: %s", e)
        raise


def delete_launch_template(template_id: str):
    """Delete a launch template after fleet creation."""
    try:
        get_ec2_client().delete_launch_template(LaunchTemplateId=template_id)
    except ClientError as e:
        logger.warning("Failed to delete launch template %s: %s", template_id, e)


def _check_existing_runner(cfg: Dict[str, Any]) -> Dict[str, Any] | None:
    """Check for and return existing runner if available."""
    existing = get_existing_runner_for_workflow(
        cfg['github_token'], cfg['github_repo'], cfg['run_id'], cfg['job_labels'])
    if existing:
        logger.info("Reusing runner %s for run %s", existing.get('name'), cfg['run_id'])
        return {
            'success': True,
            'job_id': cfg['job_id'],
            'runner_type': cfg['runner_type'],
            'run_id': cfg['run_id'],
            'runner_name': existing.get('name'),
            'reused': True
        }
    return None


def _handle_missing_ami() -> Dict[str, Any]:
    """Handle case where no AMI is available by triggering creation."""
    logger.warning("No AMI available - triggering AMI creation")
    ami_trigger = trigger_ami_creation()
    if ami_trigger['success']:
        return {
            'success': False,
            'ami_creation_triggered': True,
            'error': 'No AMI available - AMI creation has been triggered. Please retry.'
        }
    return {
        'success': False,
        'ami_creation_triggered': False,
        'error': f"No AMI available and failed to trigger creation: {ami_trigger.get('error')}"
    }


def launch_ec2_runner(
        job_id: int, job_labels: List[str], github_repo: str,
        run_id: int | None = None, runner_type: str = 'ec2') -> Dict[str, Any]:
    """Launch an EC2 instance as a GitHub Actions self-hosted runner."""
    try:
        ensure_dependencies_valid()
    except RuntimeError as exc:
        logger.error("Dependency validation failed: %s", exc)
        return {'success': False, 'job_id': job_id, 'error': str(exc)}

    github_token = get_github_token()
    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        return {'success': False, 'job_id': job_id, 'error': 'GITHUB_TOKEN not configured'}

    if run_id:
        reused = _check_existing_runner({
            'github_token': github_token, 'github_repo': github_repo,
            'run_id': run_id, 'job_id': job_id,
            'job_labels': job_labels, 'runner_type': runner_type
        })
        if reused:
            return reused

    ami_id = get_latest_ami()
    if not ami_id:
        result = _handle_missing_ami()
        result['job_id'] = job_id
        return result

    cleanup_offline_runners(github_token, github_repo, run_id)

    registration_token = get_runner_registration_token(github_token, github_repo)
    if not registration_token:
        logger.error("Failed to get runner registration token")
        return {
            'success': False, 'job_id': job_id,
            'error': 'Failed to get runner registration token'
        }

    return _try_launch_ec2_fleet({
        'job_id': job_id,
        'job_labels': build_runner_labels(job_labels, run_id),
        'github_repo': github_repo,
        'ami_id': ami_id,
        'registration_token': registration_token,
        'run_id': run_id,
        'runner_type': runner_type
    })


def _build_ec2_template_config(cfg: Dict[str, Any], ec2_config: Dict[str, Any]) -> Dict[str, Any]:
    """Build the configuration dictionary for an EC2 launch template."""
    run_id = cfg['run_id']
    job_id = cfg['job_id']
    runner_name = f"ec2-runner-{run_id}" if run_id else f"ec2-runner-{job_id}"
    user_data = create_ec2_user_data(
        cfg['registration_token'], cfg['job_labels'], cfg['github_repo'], runner_name)
    user_data_b64 = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')
    return {
        'ami_id': cfg['ami_id'],
        'security_group_id': ec2_config['security_group_id'],
        'iam_instance_profile': ec2_config['iam_instance_profile'],
        'user_data_base64': user_data_b64,
        'job_id': job_id,
        'job_labels': cfg['job_labels'],
        'github_repo': cfg['github_repo'],
        'run_id': run_id,
        'runner_type': cfg['runner_type'],
        'runner_name': runner_name
    }


def _handle_ec2_fleet_success(
        cfg: Dict[str, Any], instance: Dict[str, Any], instance_id: str) -> Dict[str, Any]:
    """Handle successful EC2 fleet instance launch."""
    run_id = cfg['run_id']
    job_id = cfg['job_id']
    runner_name = cfg.get('runner_name')
    if not runner_name:
        runner_name = f"ec2-runner-{run_id}" if run_id else f"ec2-runner-{job_id}"
    az = instance['Placement']['AvailabilityZone']
    logger.info(
        "Launched EC2 runner for job %s: %s (%s in %s)",
        job_id, instance_id, instance['InstanceType'], az
    )
    return {
        'success': True,
        'instance_id': instance_id,
        'instance_type': instance['InstanceType'],
        'availability_zone': az,
        'job_id': job_id,
        'runner_type': cfg['runner_type'],
        'run_id': run_id,
        'runner_name': runner_name
    }


def _get_fleet_instance_config(job_labels: List[str], ec2_config: Dict[str, Any]) -> tuple:
    """Get instance types and capacity type based on labels."""
    label_type = _get_instance_type_from_labels(job_labels)
    if label_type:
        instance_types = [label_type]
        logger.info("Using instance type from labels: %s", label_type)
    else:
        instance_types = ec2_config['instance_types']
        logger.info("Using instance types from config: %s", instance_types)
    use_spot = _is_spot_from_labels(job_labels)
    capacity_type = 'spot' if use_spot else 'on-demand'
    logger.info("Using capacity type: %s", capacity_type)
    return instance_types, use_spot, capacity_type


def _create_fleet_request(
        template_id: str, capacity_type: str, use_spot: bool,
        instance_types: List[str], subnet_ids: List[str]
) -> Dict[str, Any]:
    """Create and execute EC2 Fleet request."""
    target_spec = {'TotalTargetCapacity': 1, 'DefaultTargetCapacityType': capacity_type}
    template_spec = {'LaunchTemplateId': template_id, 'Version': '$Latest'}
    overrides = [
        {'InstanceType': itype, 'SubnetId': subnet}
        for subnet in subnet_ids for itype in instance_types
    ]
    config = [{
        'LaunchTemplateSpecification': template_spec,
        'Overrides': overrides
    }]
    if use_spot:
        return get_ec2_client().create_fleet(
            Type='instant', TargetCapacitySpecification=target_spec,
            SpotOptions={'AllocationStrategy': 'price-capacity-optimized'},
            LaunchTemplateConfigs=config)
    return get_ec2_client().create_fleet(
        Type='instant', TargetCapacitySpecification=target_spec,
        OnDemandOptions={'AllocationStrategy': 'lowest-price'},
        LaunchTemplateConfigs=config)


def _try_launch_ec2_fleet(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt to launch an EC2 runner using the EC2 Fleet API."""
    ec2_config = get_ec2_config()
    template_config = _build_ec2_template_config(cfg, ec2_config)
    result: Dict[str, Any] = {'success': False, 'job_id': cfg['job_id']}
    launch_template_id = None
    job_labels = cfg.get('job_labels', [])
    instance_types, use_spot, capacity_type = _get_fleet_instance_config(job_labels, ec2_config)

    try:
        launch_template_id = create_fleet_launch_template(template_config)
        fleet_response = _create_fleet_request(
            launch_template_id, capacity_type, use_spot,
            instance_types, ec2_config['subnet_ids'])
        if fleet_response.get('Instances'):
            instance_ids = fleet_response['Instances'][0].get('InstanceIds', [])
            if instance_ids:
                instance = wait_for_instance_describable(instance_ids[0])
                return _handle_ec2_fleet_success(cfg, instance, instance_ids[0])
        errors = fleet_response.get('Errors', [])
        result['error'] = '; '.join(
            e.get('ErrorMessage', str(e)) for e in errors) if errors else 'No instances launched'
        logger.error("Failed to launch EC2 runner for job %s: %s", cfg['job_id'], result['error'])
    except ClientError as e:
        logger.error("Error launching EC2 runner for job %s: %s", cfg['job_id'], e)
        result['error'] = str(e)
    finally:
        if launch_template_id:
            delete_launch_template(launch_template_id)
    return result


def get_ec2_runner_status() -> Dict[str, Any]:
    """Get the status of all running EC2 workflow runners."""
    try:
        ec2 = get_ec2_client()
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Type', 'Values': ['workflow-runner']},
                {'Name': 'tag:ManagedBy', 'Values': [os.environ['EC2_MANAGED_BY_TAG']]},
                {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
            ]
        )

        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                instances.append({
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'availability_zone': instance['Placement']['AvailabilityZone'],
                    'launch_time': instance['LaunchTime'].isoformat(),
                    'public_ip': instance.get('PublicIpAddress'),
                    'job_id': instance_tags.get('GitHubJobId'),
                    'job_labels': instance_tags.get('JobLabels'),
                    'github_repo': instance_tags.get('GitHubRepo')
                })

        result = {
            'success': True,
            'running_instances': len(instances),
            'instances': instances
        }
        logger.info("EC2 runner status: %d running instances", len(instances))
        return result
    except ClientError as e:
        logger.error("Error getting EC2 runner status: %s", e)
        return {
            'success': False,
            'error': str(e)
        }
