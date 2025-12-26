"""Lambda handler for EC2 runner API endpoint."""
import base64
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

from runner_labels import (
    parse_labels,
    validate_labels,
    get_instance_type,
    is_spot,
    LabelParseError,
    LabelValidationError,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients: Dict[str, Any] = {}
_github_token_cache: Dict[str, str] = {'value': ''}
_api_key_cache: Dict[str, str] = {'value': ''}
_test_mode = {'enabled': False}
_dependencies_validated: Dict[str, Any] = {'checked': False, 'valid': False, 'errors': []}


def is_test_mode() -> bool:
    """Check if test mode is enabled."""
    return _test_mode['enabled']


def set_test_mode(enabled: bool):
    """Enable or disable test mode."""
    _test_mode['enabled'] = enabled


def get_header_case_insensitive(headers: dict, header_name: str) -> str:
    """Get a header value by name, case-insensitively."""
    if not headers:
        return ''
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value or ''
    return ''


def get_ec2_client():
    """Get or create a cached EC2 client."""
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def get_ssm_client():
    """Get or create a cached SSM client."""
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_dynamodb_client():
    """Get or create a cached DynamoDB client."""
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def set_client(name: str, client: Any):
    """Set a client in the cache for testing purposes."""
    _clients[name] = client


def get_api_key() -> str:
    """Get the API key from SSM Parameter Store, with caching."""
    api_key = _api_key_cache['value']
    if api_key:
        return api_key
    parameter_name = os.environ['API_KEY_PARAMETER_NAME']
    ssm = get_ssm_client()
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    api_key = response['Parameter']['Value']
    _api_key_cache['value'] = api_key
    return api_key


def validate_security_groups(security_group_ids: List[str]) -> Dict[str, Any]:
    """Validate that security groups exist in AWS."""
    if not security_group_ids:
        return {'valid': True, 'missing': []}
    try:
        response = get_ec2_client().describe_security_groups(GroupIds=security_group_ids)
        found_ids = {sg['GroupId'] for sg in response.get('SecurityGroups', [])}
        missing = [sg_id for sg_id in security_group_ids if sg_id not in found_ids]
        return {'valid': len(missing) == 0, 'missing': missing}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidGroup.NotFound':
            return {'valid': False, 'missing': security_group_ids, 'error': str(e)}
        return {'valid': False, 'missing': [], 'error': str(e)}


def validate_subnets(subnet_ids: List[str]) -> Dict[str, Any]:
    """Validate that subnets exist in AWS."""
    if not subnet_ids:
        return {'valid': True, 'missing': []}
    try:
        response = get_ec2_client().describe_subnets(SubnetIds=subnet_ids)
        found_ids = {subnet['SubnetId'] for subnet in response.get('Subnets', [])}
        missing = [subnet_id for subnet_id in subnet_ids if subnet_id not in found_ids]
        return {'valid': len(missing) == 0, 'missing': missing}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidSubnetID.NotFound':
            return {'valid': False, 'missing': subnet_ids, 'error': str(e)}
        return {'valid': False, 'missing': [], 'error': str(e)}


def validate_vpc(vpc_id: str | None) -> Dict[str, Any]:
    """Validate that a VPC exists in AWS."""
    if not vpc_id:
        return {'valid': False, 'error': 'VPC ID not configured'}
    try:
        response = get_ec2_client().describe_vpcs(VpcIds=[vpc_id])
        found = len(response.get('Vpcs', [])) > 0
        return {'valid': found, 'error': None if found else f'VPC {vpc_id} not found'}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidVpcID.NotFound':
            return {'valid': False, 'error': f'VPC {vpc_id} not found'}
        return {'valid': False, 'error': str(e)}


def validate_all_dependencies() -> Dict[str, Any]:
    """Validate all infrastructure dependencies (SGs, subnets, VPC)."""
    errors = []
    security_groups_env = os.environ.get('SECURITY_GROUPS')
    security_group_ids = security_groups_env.split(',') if security_groups_env else []
    security_group_ids = [sg.strip() for sg in security_group_ids if sg.strip()]
    sg_result = validate_security_groups(security_group_ids)
    if not sg_result['valid']:
        errors.append({'type': 'security_group', 'details': sg_result})

    subnets_env = os.environ.get('SUBNETS')
    subnet_ids = subnets_env.split(',') if subnets_env else []
    subnet_ids = [s.strip() for s in subnet_ids if s.strip()]
    subnet_result = validate_subnets(subnet_ids)
    if not subnet_result['valid']:
        errors.append({'type': 'subnet', 'details': subnet_result})

    vpc_id = os.environ.get('VPC_ID')
    vpc_result = validate_vpc(vpc_id)
    if not vpc_result['valid']:
        errors.append({'type': 'vpc', 'details': vpc_result})

    all_valid = len(errors) == 0
    return {
        'valid': all_valid,
        'errors': errors,
        'checked_resources': {
            'security_groups': security_group_ids,
            'subnets': subnet_ids,
            'vpc': vpc_id
        }
    }


def ensure_dependencies_valid():
    """Ensure infrastructure dependencies are valid, raising if not."""
    if _dependencies_validated['checked']:
        if not _dependencies_validated['valid']:
            errors = _dependencies_validated['errors']
            raise RuntimeError(f"Infrastructure dependencies are invalid: {errors}")
        return

    result = validate_all_dependencies()
    _dependencies_validated['checked'] = True
    _dependencies_validated['valid'] = result['valid']
    _dependencies_validated['errors'] = result['errors']

    if not result['valid']:
        logger.error("Infrastructure dependency validation failed: %s", result['errors'])
        raise RuntimeError(f"Infrastructure dependencies are invalid: {result['errors']}")

    logger.info("Infrastructure dependencies validated successfully")


def reset_dependency_validation():
    """Reset the dependency validation cache."""
    _dependencies_validated['checked'] = False
    _dependencies_validated['valid'] = False
    _dependencies_validated['errors'] = []


def get_dependencies_status():
    """Get the current dependency validation status."""
    return {
        'checked': _dependencies_validated['checked'],
        'valid': _dependencies_validated['valid'],
        'errors': list(_dependencies_validated['errors'])
    }


def set_dependencies_status(checked, valid, errors):
    """Set the dependency validation status for testing."""
    _dependencies_validated['checked'] = checked
    _dependencies_validated['valid'] = valid
    _dependencies_validated['errors'] = errors


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a JSON HTTP response with standard headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
        },
        'body': json.dumps(body)
    }


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a success HTTP response."""
    status_code = 200 if data.get('success', True) else 500
    return json_response(status_code, data)


def error_response(status_code: int, error: str, details: str | None = None) -> Dict[str, Any]:
    """Create an error HTTP response."""
    body: Dict[str, Any] = {'success': False, 'error': error}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the request body from an API Gateway event."""
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def is_capacity_error(result: Dict[str, Any]) -> bool:
    """Check if a result indicates an EC2 capacity error."""
    error = result.get('error', [])
    if isinstance(error, str):
        return 'capacity' in error.lower() or 'availability zone' in error.lower()
    if isinstance(error, list):
        return any('Capacity' in str(e.get('reason', '')) for e in error if isinstance(e, dict))
    return False


def get_github_token() -> str:
    """Get the GitHub token from SSM Parameter Store, with caching."""
    if _github_token_cache['value']:
        return _github_token_cache['value']

    parameter_name = os.environ['GITHUB_TOKEN_SECRET_NAME']
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        token = response['Parameter']['Value']
        _github_token_cache['value'] = token
        return token
    except (ClientError, ValueError, KeyError) as e:
        logger.error("Failed to retrieve GitHub token: %s", e)
        return ''


def get_runner_registration_token(github_token: str, github_repo: str) -> str:
    """Get a new runner registration token from the GitHub API."""
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    req = urllib.request.Request(
        f'https://api.github.com/repos/{github_repo}/actions/runners/registration-token',
        method='POST',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data.get('token', '')
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        logger.error("Failed to get runner registration token: %s", e)
        return ''


def list_repo_runners(github_token: str, github_repo: str) -> List[Dict[str, Any]]:
    """List all runners registered for a GitHub repository."""
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    runners: List[Dict[str, Any]] = []
    page = 1
    while True:
        req = urllib.request.Request(
            f'https://api.github.com/repos/{github_repo}/actions/runners?per_page=100&page={page}',
            headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                page_runners = data.get('runners', [])
                runners.extend(page_runners)
                if len(page_runners) < 100:
                    break
                page += 1
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
            logger.error("Failed to list runners: %s", e)
            break
    return runners


def delete_runner(github_token: str, github_repo: str, runner_id: int) -> bool:
    """Delete a runner from a GitHub repository."""
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    req = urllib.request.Request(
        f'https://api.github.com/repos/{github_repo}/actions/runners/{runner_id}',
        method='DELETE',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            success = response.status == 204
            if success:
                logger.info("Deleted runner %s", runner_id)
            return success
    except urllib.error.HTTPError as e:
        if e.code == 204:
            logger.info("Deleted runner %s", runner_id)
            return True
        logger.error("Failed to delete runner %s: %s", runner_id, e)
        return False
    except (urllib.error.URLError, ValueError) as e:
        logger.error("Failed to delete runner %s: %s", runner_id, e)
        return False


def cleanup_offline_runners(
        github_token: str, github_repo: str, run_id: int | None) -> Dict[str, Any]:
    """Clean up offline runners for a specific workflow run."""
    runners = list_repo_runners(github_token, github_repo)
    run_id_label = f'runner-{run_id}' if run_id else None
    offline_runners = []
    for runner in runners:
        if runner.get('status') != 'offline':
            continue
        if not run_id_label:
            continue
        runner_labels = {label.get('name') for label in runner.get('labels', [])}
        if run_id_label not in runner_labels:
            continue
        offline_runners.append(runner)
    deleted_count = 0
    failed_count = 0
    for runner in offline_runners:
        runner_id = runner.get('id')
        runner_name = runner.get('name')
        if runner_id is None:
            continue
        logger.info("Removing offline runner: %s (id=%s)", runner_name, runner_id)
        if delete_runner(github_token, github_repo, int(runner_id)):
            deleted_count += 1
        else:
            failed_count += 1
    result = {
        'found': len(offline_runners),
        'deleted': deleted_count,
        'failed': failed_count
    }
    if deleted_count > 0:
        logger.info("Cleaned up %d offline runners for run_id %s", deleted_count, run_id)
    return result


def get_existing_runner_for_workflow(
        github_token: str, github_repo: str,
        run_id: int, job_labels: list) -> Dict[str, Any] | None:
    """Find an existing runner that can handle a workflow job."""
    result = None
    runners = list_repo_runners(github_token, github_repo)
    runner_label = f'runner-{run_id}'
    required_labels = set(job_labels)
    for runner in runners:
        runner_labels = {label.get('name') for label in runner.get('labels', [])}
        has_run_id_label = runner_label in runner_labels
        has_required_labels = required_labels.issubset(runner_labels)
        is_available = runner.get('status') in ('online', 'busy')
        if has_run_id_label and has_required_labels and is_available:
            result = runner
    return result


def build_runner_labels(job_labels: List[str], run_id: int | None) -> List[str]:
    """Build the complete list of labels for a GitHub runner."""
    base_labels = ['self-hosted', 'linux', 'x64']
    for label in job_labels:
        if label not in base_labels:
            base_labels.append(label)
    if run_id:
        base_labels.append(f'runner-{run_id}')
    return base_labels


def store_workflow_runner(
        run_id: int, runner_type: str, resource_id: str,
        runner_name: str, github_repo: str) -> bool:
    """Store workflow runner information in DynamoDB."""
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if not table_name:
        logger.warning("WORKFLOW_RUNNERS_TABLE not set, skipping runner storage")
        return False
    if not run_id:
        logger.warning("run_id not provided, skipping runner storage")
        return False
    try:
        ttl = int(time.time()) + 86400
        get_dynamodb_client().put_item(
            TableName=table_name,
            Item={
                'run_id': {'S': str(run_id)},
                'runner_type': {'S': runner_type},
                'resource_id': {'S': resource_id},
                'runner_name': {'S': runner_name},
                'github_repo': {'S': github_repo},
                'ttl': {'N': str(ttl)},
                'created_at': {'N': str(int(time.time()))}
            }
        )
        logger.info(
            "Stored workflow runner: run_id=%s, type=%s, resource=%s",
            run_id, runner_type, resource_id)
        return True
    except ClientError as e:
        logger.error("Failed to store workflow runner: %s", e)
        return False


def create_ec2_user_data(
        registration_token: str, job_labels: List[str],
        github_repo: str, runner_name: str) -> str:
    """Generate EC2 user data script for GitHub runner configuration.

    Uses --ephemeral so runner auto-deregisters after one job, then instance
    self-terminates via aws ec2 terminate-instances.
    """
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
    api_domain = os.environ['API_DOMAIN']
    ami_creation_url = f"https://{api_domain}/v1/runners/ec2/images"

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
    if run_id:
        store_workflow_runner(
            run_id, cfg['runner_type'], instance_id, runner_name, cfg['github_repo'])
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


def handle_ec2_runner_get(_event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET requests for EC2 runner status."""
    result = get_ec2_runner_status()
    response = success_response(result)
    return response


def handle_ec2_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST requests to launch a new EC2 runner."""
    try:
        body = parse_body(event)
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')
        run_id = body.get('run_id')
        runner_type = body.get('runner_type', 'ec2')

        if not job_id:
            response = error_response(400, 'Missing required field: job_id')
        elif not github_repo:
            response = error_response(400, 'Missing required field: github_repo')
        elif is_test_mode():
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/runners/ec2'])
        else:
            result = launch_ec2_runner(job_id, job_labels, github_repo, run_id, runner_type)
            response_body = result.copy()
            capacity_error = not result.get('success') and is_capacity_error(result)
            status_code = 503 if capacity_error else (200 if result.get('success') else 500)
            response = json_response(status_code, response_body)
    except (ValueError, KeyError) as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


ROUTE_MAP = {
    ('/v1/runners/ec2', 'POST'): handle_ec2_runner_post,
    ('/v1/runners/ec2', 'GET'): handle_ec2_runner_get
}


TEST_MODE_MOCK_PATHS = {
    '/v1/runners/ec2': {'success': True, 'instance_id': 'i-test-mode-mock', 'test_mode': True}
}


def lambda_handler(event, _context):
    """AWS Lambda handler for EC2 runner API requests."""
    logger.info("Received API request: %s", json.dumps(event))

    headers = event.get('headers', {})
    test_mode_header = get_header_case_insensitive(headers, 'x-test-mode')
    set_test_mode(test_mode_header == 'true')

    if is_test_mode():
        logger.info("Test mode enabled - will return mock responses for POST requests")

    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
            },
            'body': ''
        }

    path = event.get('path', '')
    handler = ROUTE_MAP.get((path, method))
    return handler(event) if handler else error_response(404, 'Not found')
