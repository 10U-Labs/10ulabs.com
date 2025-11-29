import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {}
_github_token_cache = {'value': None}
_api_key_cache = {'value': None}
_test_mode = {'enabled': False}
_dependencies_validated = {'checked': False, 'valid': False, 'errors': []}


def is_test_mode() -> bool:
    return _test_mode['enabled']


def set_test_mode(enabled: bool):
    _test_mode['enabled'] = enabled


def get_header_case_insensitive(headers: dict, header_name: str) -> str:
    if not headers:
        return ''
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value or ''
    return ''


def get_ec2_client():
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def get_ecs_client():
    if 'ecs' not in _clients:
        _clients['ecs'] = boto3.client('ecs')
    return _clients['ecs']


def get_ecr_client():
    if 'ecr' not in _clients:
        _clients['ecr'] = boto3.client('ecr')
    return _clients['ecr']


def get_ssm_client():
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_api_key() -> str:
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
    if _dependencies_validated['checked']:
        if not _dependencies_validated['valid']:
            raise RuntimeError(f"Infrastructure dependencies are invalid: {_dependencies_validated['errors']}")
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
    _dependencies_validated['checked'] = False
    _dependencies_validated['valid'] = False
    _dependencies_validated['errors'] = []


def get_dependencies_status():
    return {
        'checked': _dependencies_validated['checked'],
        'valid': _dependencies_validated['valid'],
        'errors': list(_dependencies_validated['errors'])
    }


def set_dependencies_status(checked, valid, errors):
    _dependencies_validated['checked'] = checked
    _dependencies_validated['valid'] = valid
    _dependencies_validated['errors'] = errors


def set_client(name, client):
    _clients[name] = client


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
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
    status_code = 200 if data.get('success', True) else 500
    return json_response(status_code, data)


def error_response(status_code: int, error: str, details: str | None = None) -> Dict[str, Any]:
    body = {'success': False, 'error': error}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def is_capacity_error(result: Dict[str, Any]) -> bool:
    error = result.get('error', [])
    if isinstance(error, str):
        return 'capacity' in error.lower() or 'availability zone' in error.lower()
    if isinstance(error, list):
        return any('Capacity' in str(e.get('reason', '')) for e in error if isinstance(e, dict))
    return False


def trigger_github_workflow(workflow_file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    github_repo = os.environ['GITHUB_REPO']
    github_token = os.environ.get('GITHUB_TOKEN')

    if not github_token:
        logger.error("GITHUB_TOKEN not set")
        result = {'success': False, 'error': 'GITHUB_TOKEN not configured'}
    else:
        workflow_url = f'https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/dispatches'

        try:
            req = urllib.request.Request(
                workflow_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Accept': 'application/vnd.github+json',
                    'Authorization': f'Bearer {github_token}',
                    'X-GitHub-Api-Version': '2022-11-28',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 204:
                    logger.info("GitHub Actions workflow triggered successfully")
                    result = {'success': True, 'message': f'{workflow_file} workflow triggered via GitHub Actions'}
                else:
                    logger.warning("Unexpected response status: %s", response.status)
                    result = {'success': False, 'error': f'Unexpected response status: {response.status}'}
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            logger.error("Failed to trigger GitHub Actions workflow: %s", e)
            result = {'success': False, 'error': str(e)}

    return result


def handle_post_request(event: Dict[str, Any], handler_func) -> Dict[str, Any]:
    try:
        path = event.get('path', '')
        if is_test_mode() and path in TEST_MODE_MOCK_PATHS:
            response = success_response(TEST_MODE_MOCK_PATHS[path])
        else:
            body = parse_body(event)
            result = handler_func(body)
            response = success_response(result)
    except (ValueError, KeyError) as e:
        logger.error("Error handling POST request: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def get_latest_ecr_image() -> Dict[str, Any]:
    ecr_repo = os.environ['ECR_REPOSITORY']
    try:
        response = get_ecr_client().describe_images(
            repositoryName=ecr_repo,
            filter={'tagStatus': 'TAGGED'}
        )

        stable_images = []
        for image in response['imageDetails']:
            image_tags = image.get('imageTags', [])
            if 'stable' in image_tags:
                stable_images.append({
                    'digest': image['imageDigest'],
                    'tags': image_tags,
                    'pushed_at': image['imagePushedAt'],
                    'size_bytes': image['imageSizeInBytes']
                })

        if not stable_images:
            return {
                'success': False,
                'error': 'No stable image found'
            }

        latest_image = sorted(stable_images, key=lambda x: x['pushed_at'], reverse=True)[0]

        result = {
            'success': True,
            'digest': latest_image['digest'],
            'tags': latest_image['tags'],
            'pushed_at': latest_image['pushed_at'].isoformat(),
            'size_bytes': latest_image['size_bytes'],
            'repository': ecr_repo
        }
        logger.info("Latest stable image: %s", result['digest'])
        return result
    except ClientError as e:
        logger.error("Error getting latest image: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def get_github_token() -> str:
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


def trigger_image_creation() -> Dict[str, Any]:
    api_endpoint = os.environ['IMAGE_API_ENDPOINT']
    image_endpoint = f'{api_endpoint}/v1/image-for-docker-runner'

    try:
        req = urllib.request.Request(
            image_endpoint,
            data=json.dumps({}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            logger.info("Image creation triggered: %s", response_data)
            result = response_data
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        logger.error("Failed to trigger image creation: %s", e)
        result = {'success': False, 'error': str(e)}
    return result


def launch_fargate_runner(job_id: int, job_labels: list, github_repo: str, run_id: int | None = None, runner_type: str = 'fargate') -> Dict[str, Any]:
    result: Dict[str, Any] = {'success': False, 'job_id': job_id}

    try:
        ensure_dependencies_valid()
    except RuntimeError as e:
        logger.error("Dependency validation failed: %s", e)
        result['error'] = str(e)
        return result

    github_token = get_github_token()
    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        result['error'] = 'GITHUB_TOKEN not configured'
        return result

    cleanup_offline_runners(github_token, github_repo, job_labels)

    registration_token = get_runner_registration_token(github_token, github_repo)
    if not registration_token:
        logger.error("Failed to get runner registration token")
        result['error'] = 'Failed to get runner registration token'
        return result

    runner_labels = build_runner_labels(job_labels, run_id)
    runner_config = {
        'job_id': job_id, 'job_labels': runner_labels, 'github_repo': github_repo,
        'registration_token': registration_token, 'run_id': run_id, 'runner_type': runner_type
    }
    return _try_launch_fargate_task(runner_config)


def _launch_fargate_task_in_subnet(cfg: Dict[str, Any], subnet: str) -> Dict[str, Any]:
    runner_name = f"fargate-runner-{cfg['job_id']}"
    response = get_ecs_client().run_task(
        cluster=os.environ['ECS_CLUSTER'],
        taskDefinition=os.environ['TASK_DEFINITION'],
        enableECSManagedTags=True,
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [subnet],
                'securityGroups': os.environ['SECURITY_GROUPS'].split(','),
                'assignPublicIp': 'ENABLED'
            }
        },
        capacityProviderStrategy=[{'capacityProvider': 'FARGATE_SPOT', 'weight': 100, 'base': 0}],
        overrides={
            'containerOverrides': [{
                'name': os.environ['CONTAINER_NAME'],
                'command': [
                    '--repo', cfg['github_repo'], '--name', runner_name,
                    '--labels', ','.join(cfg['job_labels']), '--token', cfg['registration_token']
                ]
            }]
        },
        tags=[
            {'key': 'Type', 'value': 'workflow-runner'},
            {'key': 'ManagedBy', 'value': 'docker-runner-api'},
            {'key': 'GitHubJobId', 'value': str(cfg['job_id'])},
            {'key': 'JobLabels', 'value': ' '.join(cfg['job_labels'])},
            {'key': 'GitHubRepo', 'value': cfg['github_repo']},
            {'key': 'RunId', 'value': str(cfg['run_id']) if cfg['run_id'] else ''},
            {'key': 'RunnerType', 'value': cfg['runner_type']}
        ]
    )
    return {'response': response, 'runner_name': runner_name}


def _try_launch_fargate_task(cfg: Dict[str, Any]) -> Dict[str, Any]:
    last_error: Any = None
    result: Dict[str, Any] = {'success': False, 'job_id': cfg['job_id']}
    for subnet in os.environ['SUBNETS'].split(','):
        try:
            launch = _launch_fargate_task_in_subnet(cfg, subnet)
            response, runner_name = launch['response'], launch['runner_name']
            if response['tasks']:
                task_arn = response['tasks'][0]['taskArn']
                logger.info("Launched Fargate runner for job %s: %s", cfg['job_id'], task_arn)
                if cfg['run_id']:
                    store_workflow_runner(cfg['run_id'], cfg['runner_type'], task_arn, runner_name, cfg['github_repo'])
                result = {
                    'success': True, 'task_arn': task_arn, 'job_id': cfg['job_id'],
                    'runner_type': cfg['runner_type'], 'run_id': cfg['run_id'], 'runner_name': runner_name
                }
                return result
            failures = response.get('failures', [])
            if any('Capacity' in str(f.get('reason', '')) for f in failures):
                logger.warning("No Fargate Spot capacity in subnet %s, trying next AZ...", subnet)
                last_error = failures
                continue
            logger.error("Failed to launch Fargate runner for job %s: %s", cfg['job_id'], failures)
            result['error'] = failures
            return result
        except ClientError as e:
            logger.error("Error launching Fargate runner for job %s: %s", cfg['job_id'], e)
            result['error'] = str(e)
            return result
    logger.error("Failed to launch Fargate runner for job %s: no capacity in any AZ", cfg['job_id'])
    result['error'] = last_error if last_error else 'No capacity in any availability zone'
    return result


def get_runner_registration_token(github_token: str, github_repo: str) -> str:
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


def cleanup_offline_runners(github_token: str, github_repo: str, job_labels: List[str]) -> Dict[str, Any]:
    runners = list_repo_runners(github_token, github_repo)
    job_labels_set = set(job_labels)
    offline_runners = []
    for runner in runners:
        if runner.get('status') != 'offline':
            continue
        runner_labels = {label.get('name') for label in runner.get('labels', [])}
        if not job_labels_set.intersection(runner_labels):
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
        logger.info("Cleaned up %d offline runners matching labels %s", deleted_count, job_labels)
    return result


def create_ec2_user_data(registration_token: str, job_labels: List[str], github_repo: str) -> str:
    aws_region = os.environ['AWS_REGION']
    runner_labels = ','.join(job_labels)
    return f"""#!/bin/bash
set -e

INSTANCE_STORE=$(lsblk -dn -o NAME,TYPE | awk '$2=="disk" {{print "/dev/"$1}}' | while read dev; do
    if [ -z "$(lsblk -n "$dev" -o CHILDREN 2>/dev/null | tr -d ' ')" ]; then
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

cd /home/github-runner/actions-runner

sudo -u github-runner ./config.sh \
    --url "https://github.com/{github_repo}" \
    --token "{registration_token}" \
    --name "ec2-spot-$(hostname)" \
    --labels "{runner_labels}" \
    --unattended

sudo -u github-runner ./run.sh

INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
aws ec2 terminate-instances \
    --instance-ids "$INSTANCE_ID" \
    --region {aws_region} \
    || shutdown -h now
"""


def get_latest_ami() -> str:
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
    api_domain = os.environ['API_DOMAIN']
    ami_creation_url = f"https://{api_domain}/v1/image-for-ec2-runners"

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
    return {
        'subnet_ids': os.environ['SUBNETS'].split(','),
        'security_group_id': os.environ['SECURITY_GROUPS'],
        'instance_types': os.environ['EC2_INSTANCE_TYPES'].split(','),
        'iam_instance_profile': os.environ['EC2_IAM_INSTANCE_PROFILE'],
        'max_price': os.environ['EC2_MAX_PRICE']
    }


def wait_for_instance_describable(instance_id: str, max_attempts: int = 3) -> Dict[str, Any]:
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
    raise ClientError(
        {'Error': {'Code': 'InvalidInstanceID.NotFound', 'Message': f'Instance {instance_id} not found after {max_attempts} attempts'}},
        'DescribeInstances'
    )


def create_fleet_launch_template(template_config: Dict[str, Any]) -> str:
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
    try:
        get_ec2_client().delete_launch_template(LaunchTemplateId=template_id)
    except ClientError as e:
        logger.warning("Failed to delete launch template %s: %s", template_id, e)


def launch_ec2_spot_runner(
    job_id: int, job_labels: List[str], github_repo: str, run_id: int | None = None, runner_type: str = 'ec2'
) -> Dict[str, Any]:
    result: Dict[str, Any] = {'success': False, 'job_id': job_id}

    try:
        ensure_dependencies_valid()
    except RuntimeError as e:
        logger.error("Dependency validation failed: %s", e)
        result['error'] = str(e)
        return result

    ami_id = get_latest_ami()
    if not ami_id:
        logger.warning("No AMI available - triggering AMI creation")
        ami_trigger = trigger_ami_creation()
        result['ami_creation_triggered'] = ami_trigger['success']
        if ami_trigger['success']:
            result['error'] = 'No AMI available - AMI creation has been triggered. Please retry in a few minutes.'
        else:
            result['error'] = f"No AMI available and failed to trigger creation: {ami_trigger.get('error')}"
        return result

    github_token = get_github_token()
    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        result['error'] = 'GITHUB_TOKEN not configured'
        return result

    cleanup_offline_runners(github_token, github_repo, job_labels)

    registration_token = get_runner_registration_token(github_token, github_repo)
    if not registration_token:
        logger.error("Failed to get runner registration token")
        result['error'] = 'Failed to get runner registration token'
        return result

    runner_labels = build_runner_labels(job_labels, run_id)
    runner_config = {
        'job_id': job_id, 'job_labels': runner_labels, 'github_repo': github_repo,
        'ami_id': ami_id, 'registration_token': registration_token, 'run_id': run_id, 'runner_type': runner_type
    }
    return _try_launch_ec2_fleet(runner_config)


def _build_ec2_template_config(cfg: Dict[str, Any], ec2_config: Dict[str, Any]) -> Dict[str, Any]:
    user_data = create_ec2_user_data(cfg['registration_token'], cfg['job_labels'], cfg['github_repo'])
    return {
        'ami_id': cfg['ami_id'],
        'security_group_id': ec2_config['security_group_id'],
        'iam_instance_profile': ec2_config['iam_instance_profile'],
        'user_data_base64': base64.b64encode(user_data.encode('utf-8')).decode('utf-8'),
        'job_id': cfg['job_id'], 'job_labels': cfg['job_labels'], 'github_repo': cfg['github_repo'],
        'run_id': cfg['run_id'], 'runner_type': cfg['runner_type']
    }


def _handle_ec2_fleet_success(cfg: Dict[str, Any], instance: Dict[str, Any], instance_id: str) -> Dict[str, Any]:
    runner_name = f"ec2-spot-runner-{cfg['job_id']}"
    logger.info(
        "Launched EC2 spot runner for job %s: %s (%s in %s)",
        cfg['job_id'], instance_id, instance['InstanceType'], instance['Placement']['AvailabilityZone']
    )
    if cfg['run_id']:
        store_workflow_runner(cfg['run_id'], cfg['runner_type'], instance_id, runner_name, cfg['github_repo'])
    return {
        'success': True, 'instance_id': instance_id, 'instance_type': instance['InstanceType'],
        'availability_zone': instance['Placement']['AvailabilityZone'], 'job_id': cfg['job_id'],
        'runner_type': cfg['runner_type'], 'run_id': cfg['run_id'], 'runner_name': runner_name
    }


def _try_launch_ec2_fleet(cfg: Dict[str, Any]) -> Dict[str, Any]:
    ec2_config = get_ec2_config()
    template_config = _build_ec2_template_config(cfg, ec2_config)
    result: Dict[str, Any] = {'success': False, 'job_id': cfg['job_id']}
    launch_template_id = None
    try:
        launch_template_id = create_fleet_launch_template(template_config)
        fleet_response = get_ec2_client().create_fleet(
            Type='instant',
            TargetCapacitySpecification={'TotalTargetCapacity': 1, 'DefaultTargetCapacityType': 'spot'},
            SpotOptions={'AllocationStrategy': 'capacity-optimized', 'InstanceInterruptionBehavior': 'terminate'},
            LaunchTemplateConfigs=[{
                'LaunchTemplateSpecification': {'LaunchTemplateId': launch_template_id, 'Version': '$Latest'},
                'Overrides': [
                    {'InstanceType': itype, 'SubnetId': subnet, 'MaxPrice': ec2_config['max_price']}
                    for subnet in ec2_config['subnet_ids'] for itype in ec2_config['instance_types']
                ]
            }]
        )
        if fleet_response.get('Instances'):
            instance_ids = fleet_response['Instances'][0].get('InstanceIds', [])
            if instance_ids:
                instance = wait_for_instance_describable(instance_ids[0])
                result = _handle_ec2_fleet_success(cfg, instance, instance_ids[0])
                return result
        errors = fleet_response.get('Errors', [])
        result['error'] = '; '.join([e.get('ErrorMessage', str(e)) for e in errors]) if errors else 'No instances launched'
        logger.error("Failed to launch EC2 runner for job %s: %s", cfg['job_id'], result['error'])
    except ClientError as e:
        logger.error("Error launching EC2 runner for job %s: %s", cfg['job_id'], e)
        result['error'] = str(e)
    finally:
        if launch_template_id:
            delete_launch_template(launch_template_id)
    return result


def launch_packer_builder(_config: Dict[str, Any]) -> Dict[str, Any]:
    subnet_ids = os.environ['SUBNETS'].split(',')
    vpc_id = os.environ['VPC_ID']
    region = os.environ['AWS_REGION']

    payload = {
        'ref': 'main',
        'inputs': {
            'vpc_id': vpc_id,
            'subnet_id': subnet_ids[0],
            'region': region
        }
    }

    result = trigger_github_workflow('image_for_ec2_runners_post.yml', payload)
    return result


def list_amis() -> Dict[str, Any]:
    ami_purpose_tag = os.environ['EC2_AMI_PURPOSE_TAG']
    ami_purpose_value = os.environ['EC2_AMI_PURPOSE_VALUE']
    try:
        response = get_ec2_client().describe_images(
            Owners=['self'],
            Filters=[
                {'Name': f'tag:{ami_purpose_tag}', 'Values': [ami_purpose_value]}
            ]
        )

        amis = []
        for image in response['Images']:
            amis.append({
                'ami_id': image['ImageId'],
                'name': image['Name'],
                'state': image['State'],
                'creation_date': image['CreationDate'],
                'architecture': image['Architecture'],
                'tags': {tag['Key']: tag['Value'] for tag in image.get('Tags', [])}
            })

        amis.sort(key=lambda x: str(x['creation_date']), reverse=True)
        logger.info("Listed %s AMIs", len(amis))
        return {'success': True, 'amis': amis, 'count': len(amis)}
    except ClientError as e:
        logger.error("Error listing AMIs: %s", e)
        return {'success': False, 'error': str(e)}


def get_latest_ami_details() -> Dict[str, Any]:
    ami_purpose_tag = os.environ['EC2_AMI_PURPOSE_TAG']
    ami_purpose_value = os.environ['EC2_AMI_PURPOSE_VALUE']
    ami_stable_tag = os.environ['EC2_AMI_STABLE_TAG']
    try:
        try:
            param_response = get_ssm_client().get_parameter(Name='/github-runner/ami/latest')
            ami_id = param_response['Parameter']['Value']
            logger.info("Retrieved latest AMI from SSM Parameter Store: %s", ami_id)
        except ClientError as ssm_error:
            if ssm_error.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning("SSM parameter not found, falling back to EC2 query")
                response = get_ec2_client().describe_images(
                    Owners=['self'],
                    Filters=[
                        {'Name': f'tag:{ami_purpose_tag}', 'Values': [ami_purpose_value]},
                        {'Name': f'tag:{ami_stable_tag}', 'Values': ['true']}
                    ]
                )
                if not response['Images']:
                    return {'success': False, 'error': 'No available AMI found'}
                images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
                ami_id = images[0]['ImageId']
                logger.info("Retrieved latest AMI from EC2 query: %s", ami_id)
            else:
                raise

        image_response = get_ec2_client().describe_images(ImageIds=[ami_id])
        if not image_response['Images']:
            return {'success': False, 'error': f'AMI {ami_id} not found'}

        latest_image = image_response['Images'][0]
        result = {
            'success': True,
            'ami_id': latest_image['ImageId'],
            'name': latest_image['Name'],
            'state': latest_image['State'],
            'creation_date': latest_image['CreationDate'],
            'architecture': latest_image['Architecture'],
            'tags': {tag['Key']: tag['Value'] for tag in latest_image.get('Tags', [])}
        }
        logger.info("Latest AMI details: %s", result['ami_id'])
        return result
    except ClientError as e:
        logger.error("Error getting latest AMI: %s", e)
        return {'success': False, 'error': str(e)}


def deregister_ami(ami_id: str) -> Dict[str, Any]:
    try:
        image_response = get_ec2_client().describe_images(ImageIds=[ami_id])
        if not image_response['Images']:
            return {'success': False, 'error': 'AMI not found'}

        snapshot_ids = []
        for mapping in image_response['Images'][0].get('BlockDeviceMappings', []):
            if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                snapshot_ids.append(mapping['Ebs']['SnapshotId'])

        get_ec2_client().deregister_image(ImageId=ami_id)
        logger.info("Deregistered AMI: %s", ami_id)

        for snapshot_id in snapshot_ids:
            try:
                get_ec2_client().delete_snapshot(SnapshotId=snapshot_id)
                logger.info("Deleted snapshot: %s", snapshot_id)
            except ClientError as e:
                logger.warning("Failed to delete snapshot %s: %s", snapshot_id, e)

        return {
            'success': True,
            'ami_id': ami_id,
            'deleted_snapshots': snapshot_ids,
            'message': f'AMI {ami_id} deregistered successfully'
        }
    except ClientError as e:
        logger.error("Error deregistering AMI %s: %s", ami_id, e)
        return {'success': False, 'error': str(e)}


def handle_docker_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')
        run_id = body.get('run_id')
        runner_type = body.get('runner_type', 'fargate')

        if not job_id:
            response = error_response(400, 'Missing required field: job_id')
        elif not github_repo:
            response = error_response(400, 'Missing required field: github_repo')
        elif is_test_mode():
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/docker-runner'])
        else:
            image_check = get_latest_ecr_image()
            if not image_check['success']:
                logger.warning("No stable image found, triggering image creation")
                trigger_result = trigger_image_creation()
                response = json_response(202, {
                    'success': False,
                    'error': 'No stable image available',
                    'message': 'Image build triggered',
                    'trigger_result': trigger_result
                })
            else:
                result = launch_fargate_runner(job_id, job_labels, github_repo, run_id, runner_type)
                response_body = result.copy()
                capacity_error = not result.get('success') and is_capacity_error(result)
                status_code = 503 if capacity_error else (200 if result.get('success') else 500)
                response = json_response(status_code, response_body)
    except (ValueError, KeyError) as e:
        logger.error("Error handling POST request: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def get_docker_runner_status() -> Dict[str, Any]:
    cluster = os.environ['ECS_CLUSTER']
    try:
        ecs = get_ecs_client()
        response = ecs.list_tasks(
            cluster=cluster,
            desiredStatus='RUNNING'
        )

        task_arns = response.get('taskArns', [])

        if not task_arns:
            result = {
                'success': True,
                'running_tasks': 0,
                'tasks': [],
                'cluster': cluster
            }
        else:
            task_details = ecs.describe_tasks(
                cluster=cluster,
                tasks=task_arns
            )

            tasks = []
            for task in task_details.get('tasks', []):
                task_tags = {tag['key']: tag['value'] for tag in task.get('tags', [])}
                tasks.append({
                    'task_arn': task['taskArn'],
                    'task_id': task['taskArn'].split('/')[-1],
                    'status': task['lastStatus'],
                    'desired_status': task['desiredStatus'],
                    'started_at': task.get('startedAt').isoformat() if task.get('startedAt') else None,
                    'cpu': task.get('cpu'),
                    'memory': task.get('memory'),
                    'job_id': task_tags.get('GitHubJobId'),
                    'job_labels': task_tags.get('JobLabels'),
                    'github_repo': task_tags.get('GitHubRepo')
                })

            result = {
                'success': True,
                'running_tasks': len(tasks),
                'tasks': tasks,
                'cluster': cluster
            }

        logger.info("Docker runner status: %d running tasks", len(task_arns))
        return result
    except ClientError as e:
        logger.error("Error getting docker runner status: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def get_ec2_runner_status() -> Dict[str, Any]:
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


def handle_docker_runner_get(_event: Dict[str, Any]) -> Dict[str, Any]:
    result = get_docker_runner_status()
    response = success_response(result)
    return response


def handle_ec2_runner_get(_event: Dict[str, Any]) -> Dict[str, Any]:
    result = get_ec2_runner_status()
    response = success_response(result)
    return response


def handle_ec2_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
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
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/ec2-runner'])
        else:
            result = launch_ec2_spot_runner(job_id, job_labels, github_repo, run_id, runner_type)
            response_body = result.copy()
            capacity_error = not result.get('success') and is_capacity_error(result)
            status_code = 503 if capacity_error else (200 if result.get('success') else 500)
            response = json_response(status_code, response_body)
    except (ValueError, KeyError) as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def handle_ec2_image_get(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get('path', '')
    result = get_latest_ami_details() if path.endswith('/latest') else list_amis()
    response = success_response(result)
    return response


def handle_ec2_image_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    path_params = event.get('pathParameters', {})
    ami_id = path_params.get('ami_id')
    result = deregister_ami(ami_id) if ami_id else {'success': False, 'error': 'Missing required path parameter: ami_id'}
    response = error_response(400, result['error']) if not ami_id else success_response(result)
    return response


def handle_echo_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        response = json_response(200, {'echo': body, 'received_at': event.get('requestContext', {}).get('requestId', 'N/A')})
    except (ValueError, KeyError):
        response = error_response(400, 'Invalid JSON')
    return response


def get_ses_client():
    if 'ses' not in _clients:
        _clients['ses'] = boto3.client('ses')
    return _clients['ses']


def get_dynamodb_client():
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def store_workflow_runner(run_id: int, runner_type: str, resource_id: str, runner_name: str, github_repo: str) -> bool:
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
        logger.info("Stored workflow runner: run_id=%s, type=%s, resource=%s", run_id, runner_type, resource_id)
        return True
    except ClientError as e:
        logger.error("Failed to store workflow runner: %s", e)
        return False


def build_runner_labels(job_labels: List[str], run_id: int | None) -> List[str]:
    base_labels = ['self-hosted', 'linux', 'x64']
    for label in job_labels:
        if label not in base_labels:
            base_labels.append(label)
    if run_id:
        base_labels.append(f'runner-{run_id}')
    return base_labels


def get_recaptcha_secret() -> str:
    parameter_name = os.environ.get('RECAPTCHA_SECRET_PARAMETER_NAME')
    if not parameter_name:
        return ''
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        secret = response['Parameter']['Value']
        return secret
    except (ClientError, ValueError, KeyError) as e:
        logger.error("Failed to retrieve reCAPTCHA secret: %s", e)
        return ''


def verify_recaptcha(token: str, secret: str) -> bool:
    if not token or not secret:
        return False
    try:
        data = urllib.parse.urlencode({
            'secret': secret,
            'response': token
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://www.google.com/recaptcha/api/siteverify',
            data=data,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            success = result.get('success', False)
            score = result.get('score', 0)
            is_valid = success and score >= 0.5
            if not is_valid:
                logger.warning("reCAPTCHA verification failed: success=%s, score=%s", success, score)
            return is_valid
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        logger.error("reCAPTCHA verification error: %s", e)
        return False


def validate_contact_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    result = bool(re.match(pattern, email))
    return result


def send_contact_email(recipient: str, sender_name: str, sender_email: str, message: str) -> bool:
    subject = f'Contact Form: Message from {sender_name}'
    body_text = f'Name: {sender_name}\nEmail: {sender_email}\n\nMessage:\n{message}'
    body_html = f'''<html>
<body>
<h2>New Contact Form Submission</h2>
<p><strong>Name:</strong> {sender_name}</p>
<p><strong>Email:</strong> <a href="mailto:{sender_email}">{sender_email}</a></p>
<h3>Message:</h3>
<p>{message.replace(chr(10), '<br>')}</p>
</body>
</html>'''
    try:
        get_ses_client().send_email(
            Source=recipient,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                }
            },
            ReplyToAddresses=[sender_email]
        )
        return True
    except ClientError as e:
        logger.error("Failed to send contact email: %s", e)
        return False


def _validate_contact_fields(fields: Dict[str, str]) -> Optional[Dict[str, Any]]:
    validations = [
        (not fields['recaptcha_token'], 'Missing required field: recaptcha_token'),
        (not fields['name'], 'Missing required field: name'),
        (len(fields['name']) > 100, 'Name must be less than 100 characters'),
        (not fields['email'], 'Missing required field: email'),
        (len(fields['email']) > 255, 'Email must be less than 255 characters'),
        (fields['email'] and not validate_contact_email(fields['email']), 'Invalid email address'),
        (not fields['message'], 'Missing required field: message'),
        (len(fields['message']) > 1000, 'Message must be less than 1000 characters'),
    ]
    result = None
    for condition, error_msg in validations:
        if condition and result is None:
            result = error_response(400, error_msg)
    return result


def _process_contact_submission(fields: Dict[str, str]) -> Dict[str, Any]:
    recaptcha_secret = get_recaptcha_secret()
    contact_email = os.environ.get('CONTACT_EMAIL')
    response: Dict[str, Any]
    if not recaptcha_secret:
        logger.error("reCAPTCHA secret not configured")
        response = error_response(500, 'Server configuration error')
    elif not verify_recaptcha(fields['recaptcha_token'], recaptcha_secret):
        response = error_response(400, 'reCAPTCHA verification failed')
    elif not contact_email:
        response = error_response(500, 'Server configuration error')
    elif send_contact_email(contact_email, fields['name'], fields['email'], fields['message']):
        logger.info("Contact form submitted: name=%s, email=%s", fields['name'], fields['email'])
        response = json_response(200, {'success': True, 'message': 'Message sent successfully'})
    else:
        response = error_response(500, 'Failed to send message')
    return response


def handle_contact_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        fields = {
            'recaptcha_token': body.get('recaptcha_token', '').strip(),
            'name': body.get('name', '').strip(),
            'email': body.get('email', '').strip(),
            'message': body.get('message', '').strip(),
        }
        validation_error = _validate_contact_fields(fields)
        if validation_error:
            response = validation_error
        elif is_test_mode():
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/contact'])
        else:
            response = _process_contact_submission(fields)
    except (ValueError, KeyError) as e:
        logger.error("Error handling contact form: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def handle_dependencies_health(_event: Dict[str, Any]) -> Dict[str, Any]:
    result = validate_all_dependencies()
    if result['valid']:
        response = json_response(200, {
            'status': 'healthy',
            'message': 'All infrastructure dependencies are valid',
            'checked_resources': result['checked_resources']
        })
    else:
        response = json_response(503, {
            'status': 'unhealthy',
            'message': 'Infrastructure dependencies are invalid',
            'errors': result['errors'],
            'checked_resources': result['checked_resources']
        })
    return response


ROUTE_MAP = {
    ('/v1/contact', 'POST'): handle_contact_post,
    ('/v1/echo', 'POST'): handle_echo_post,
    ('/v1/health/dependencies', 'GET'): handle_dependencies_health,
    ('/v1/docker-runner', 'POST'): handle_docker_runner_post,
    ('/v1/docker-runner', 'GET'): handle_docker_runner_get,
    ('/v1/ec2-runner', 'POST'): handle_ec2_runner_post,
    ('/v1/ec2-runner', 'GET'): handle_ec2_runner_get,
    ('/v1/image-for-ec2-runners', 'POST'): lambda e: handle_post_request(e, launch_packer_builder),
    ('/v1/image-for-ec2-runners', 'GET'): handle_ec2_image_get,
    ('/v1/image-for-ec2-runners/latest', 'GET'): handle_ec2_image_get
}


TEST_MODE_MOCK_PATHS = {
    '/v1/contact': {'success': True, 'message': 'Test mode - contact form not submitted', 'test_mode': True},
    '/v1/ec2-runner': {'success': True, 'instance_id': 'i-test-mode-mock', 'test_mode': True},
    '/v1/docker-runner': {'success': True, 'task_arn': 'arn:aws:ecs:test-mode-mock', 'test_mode': True},
    '/v1/image-for-ec2-runners': {'success': True, 'message': 'Test mode - no AMI created', 'test_mode': True}
}


def lambda_handler(event, _context):
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

    if not handler:
        if path.startswith('/v1/image-for-ec2-runners/') and method == 'DELETE':
            handler = handle_ec2_image_delete

    if handler:
        response = handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
