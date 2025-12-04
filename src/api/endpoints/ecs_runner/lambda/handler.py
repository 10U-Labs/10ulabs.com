import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List
import boto3
from botocore.exceptions import ClientError


@dataclass
class WorkflowRunner:
    run_id: int
    runner_type: str
    resource_id: str
    runner_name: str
    github_repo: str
    state: str = 'requested'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients: Dict[str, Any] = {}
_github_token_cache: Dict[str, str] = {'value': ''}
_test_mode = {'enabled': False}
_dependencies_validated: Dict[str, Any] = {'checked': False, 'valid': False, 'errors': []}


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


def get_dynamodb_client():
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def set_client(name: str, client: Any):
    _clients[name] = client


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
    body: Dict[str, Any] = {'success': False, 'error': error}
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
    image_endpoint = f'{api_endpoint}/v1/image-for-ecs-runners'

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


def cleanup_offline_runners(github_token: str, github_repo: str, run_id: int | None) -> Dict[str, Any]:
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


def get_existing_runner_for_workflow(github_token: str, github_repo: str, run_id: int, job_labels: list) -> Dict[str, Any] | None:
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
    base_labels = ['self-hosted', 'linux', 'x64']
    for label in job_labels:
        if label not in base_labels:
            base_labels.append(label)
    if run_id:
        base_labels.append(f'runner-{run_id}')
    return base_labels


def store_workflow_runner(runner: WorkflowRunner) -> bool:
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if not table_name:
        logger.warning("WORKFLOW_RUNNERS_TABLE not set, skipping runner storage")
        return False
    if not runner.run_id:
        logger.warning("run_id not provided, skipping runner storage")
        return False
    try:
        ttl = int(time.time()) + 86400
        get_dynamodb_client().put_item(
            TableName=table_name,
            Item={
                'run_id': {'S': str(runner.run_id)},
                'runner_type': {'S': runner.runner_type},
                'resource_id': {'S': runner.resource_id},
                'runner_name': {'S': runner.runner_name},
                'github_repo': {'S': runner.github_repo},
                'state': {'S': runner.state},
                'ttl': {'N': str(ttl)},
                'created_at': {'N': str(int(time.time()))}
            }
        )
        logger.info("Stored workflow runner: run_id=%s, type=%s, resource=%s, state=%s", runner.run_id, runner.runner_type, runner.resource_id, runner.state)
        return True
    except ClientError as e:
        logger.error("Failed to store workflow runner: %s", e)
        return False


FARGATE_SPOT_MAX_RETRIES = 3
FARGATE_SPOT_POLL_INTERVAL = 2
FARGATE_SPOT_MAX_POLL_ATTEMPTS = 10


def get_fargate_task_status(cluster: str, task_arn: str) -> Dict[str, Any]:
    try:
        response = get_ecs_client().describe_tasks(cluster=cluster, tasks=[task_arn])
        if response.get('tasks'):
            task = response['tasks'][0]
            return {
                'status': task.get('lastStatus', ''),
                'stopped_reason': task.get('stoppedReason', ''),
                'started_at': task.get('startedAt')
            }
    except ClientError as e:
        logger.warning("Failed to get task status for %s: %s", task_arn, e)
    return {'status': 'UNKNOWN', 'stopped_reason': '', 'started_at': None}


def is_fargate_spot_interruption(task_status: Dict[str, Any]) -> bool:
    return 'Spot' in task_status.get('stopped_reason', '') and 'interrupt' in task_status.get('stopped_reason', '').lower()


def wait_for_fargate_task_provisioned(cluster: str, task_arn: str) -> Dict[str, Any]:
    result = {'success': False, 'spot_interrupted': False, 'status': ''}
    for attempt in range(FARGATE_SPOT_MAX_POLL_ATTEMPTS):
        task_status = get_fargate_task_status(cluster, task_arn)
        status = task_status['status']
        result['status'] = status
        if status == 'RUNNING':
            result['success'] = True
            return result
        if status == 'STOPPED':
            if is_fargate_spot_interruption(task_status):
                logger.warning("Task %s was interrupted by Spot reclamation: %s", task_arn, task_status['stopped_reason'])
                result['spot_interrupted'] = True
            return result
        if status in ('PENDING', 'PROVISIONING', 'ACTIVATING'):
            if attempt < FARGATE_SPOT_MAX_POLL_ATTEMPTS - 1:
                time.sleep(FARGATE_SPOT_POLL_INTERVAL)
            continue
        return result
    result['success'] = True
    return result


def _launch_fargate_task_in_subnet(cfg: Dict[str, Any], subnet: str) -> Dict[str, Any]:
    runner_name = f"fargate-runner-{cfg['run_id']}" if cfg['run_id'] else f"fargate-runner-{cfg['job_id']}"
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
        capacityProviderStrategy=[{'capacityProvider': 'FARGATE', 'weight': 100, 'base': 0}],
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
            {'key': 'ManagedBy', 'value': 'ecs-runner-api'},
            {'key': 'GitHubJobId', 'value': str(cfg['job_id'])},
            {'key': 'JobLabels', 'value': ' '.join(cfg['job_labels'])},
            {'key': 'GitHubRepo', 'value': cfg['github_repo']},
            {'key': 'RunId', 'value': str(cfg['run_id']) if cfg['run_id'] else ''},
            {'key': 'RunnerType', 'value': cfg['runner_type']}
        ]
    )
    return {'response': response, 'runner_name': runner_name}


def _try_launch_in_subnet(cfg: Dict[str, Any], subnet: str, cluster: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {'success': False, 'spot_interrupted': False, 'retry': False}
    try:
        launch = _launch_fargate_task_in_subnet(cfg, subnet)
        response, runner_name = launch['response'], launch['runner_name']
        if not response['tasks']:
            failures = response.get('failures', [])
            if any('Capacity' in str(f.get('reason', '')) for f in failures):
                logger.warning("No Fargate Spot capacity in subnet %s, trying next AZ...", subnet)
                result['retry'] = True
                result['error'] = failures
                return result
            logger.error("Failed to launch Fargate runner for job %s: %s", cfg['job_id'], failures)
            result['error'] = failures
            return result
        task_arn = response['tasks'][0]['taskArn']
        logger.info("Launched Fargate runner for job %s: %s", cfg['job_id'], task_arn)
        if cfg['run_id']:
            runner = WorkflowRunner(run_id=cfg['run_id'], runner_type=cfg['runner_type'], resource_id=task_arn, runner_name=runner_name, github_repo=cfg['github_repo'])
            store_workflow_runner(runner)
        provision_result = wait_for_fargate_task_provisioned(cluster, task_arn)
        if provision_result['spot_interrupted']:
            logger.warning("Task %s spot interrupted before running, will retry in different AZ", task_arn)
            result['spot_interrupted'] = True
            result['retry'] = True
            return result
        result = {
            'success': True, 'task_arn': task_arn, 'job_id': cfg['job_id'],
            'runner_type': cfg['runner_type'], 'run_id': cfg['run_id'], 'runner_name': runner_name
        }
    except ClientError as e:
        logger.error("Error launching Fargate runner for job %s: %s", cfg['job_id'], e)
        result['error'] = str(e)
    return result


def _try_launch_fargate_task(cfg: Dict[str, Any]) -> Dict[str, Any]:
    last_error: Any = None
    result: Dict[str, Any] = {'success': False, 'job_id': cfg['job_id']}
    cluster = os.environ['ECS_CLUSTER']
    all_subnets = os.environ['SUBNETS'].split(',')
    excluded_subnets: List[str] = []
    for attempt in range(FARGATE_SPOT_MAX_RETRIES):
        available_subnets = [s for s in all_subnets if s not in excluded_subnets]
        if not available_subnets:
            logger.error("No subnets remaining after excluding spot-interrupted AZs")
            break
        for subnet in available_subnets:
            launch_result = _try_launch_in_subnet(cfg, subnet, cluster)
            if launch_result.get('success'):
                return launch_result
            if launch_result.get('spot_interrupted'):
                excluded_subnets.append(subnet)
                last_error = 'Spot interruption'
                break
            if launch_result.get('retry'):
                last_error = launch_result.get('error', 'Capacity unavailable')
                continue
            result['error'] = launch_result.get('error', 'Unknown error')
            return result
        if launch_result.get('spot_interrupted'):
            logger.info("Retrying after spot interruption (attempt %d/%d)", attempt + 1, FARGATE_SPOT_MAX_RETRIES)
            continue
        break
    logger.error("Failed to launch Fargate runner for job %s after %d attempts: %s", cfg['job_id'], FARGATE_SPOT_MAX_RETRIES, last_error)
    result['error'] = last_error if last_error else 'No capacity in any availability zone'
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

    if run_id:
        existing_runner = get_existing_runner_for_workflow(github_token, github_repo, run_id, job_labels)
        if existing_runner:
            logger.info("Reusing existing runner %s for workflow run %s", existing_runner.get('name'), run_id)
            result = {
                'success': True, 'job_id': job_id, 'runner_type': runner_type, 'run_id': run_id,
                'runner_name': existing_runner.get('name'), 'reused': True
            }
            return result

    cleanup_offline_runners(github_token, github_repo, run_id)

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


def handle_ecs_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
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
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/ecs-runner'])
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


def get_ecs_runner_status() -> Dict[str, Any]:
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

        logger.info("ECS runner status: %d running tasks", len(task_arns))
        return result
    except ClientError as e:
        logger.error("Error getting ECS runner status: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def handle_ecs_runner_get(_event: Dict[str, Any]) -> Dict[str, Any]:
    result = get_ecs_runner_status()
    response = success_response(result)
    return response


ROUTE_MAP = {
    ('/v1/ecs-runner', 'POST'): handle_ecs_runner_post,
    ('/v1/ecs-runner', 'GET'): handle_ecs_runner_get
}


TEST_MODE_MOCK_PATHS = {
    '/v1/ecs-runner': {'success': True, 'task_arn': 'arn:aws:ecs:test-mode-mock', 'test_mode': True}
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

    if handler:
        response = handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
