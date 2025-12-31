"""Fargate task operations for ECS runner API."""
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

from botocore.exceptions import ClientError

from aws_clients import (
    get_ecs_client,
    get_ecr_client,
)
from github_runner_api import (
    get_github_token,
    get_runner_registration_token,
    get_existing_runner_for_workflow,
    cleanup_offline_runners,
    build_runner_labels,
)
from infra_validation import ensure_dependencies_valid
from runner_labels import (
    parse_labels,
    validate_labels,
    is_spot,
    LabelParseError,
    LabelValidationError,
)

logger = logging.getLogger()


FARGATE_SPOT_MAX_RETRIES = 3
FARGATE_SPOT_POLL_INTERVAL = 2
FARGATE_SPOT_MAX_POLL_ATTEMPTS = 10


def get_latest_ecr_image() -> Dict[str, Any]:
    """Get the latest stable ECR image."""
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


def trigger_image_creation() -> Dict[str, Any]:
    """Trigger ECR image creation via the image API."""
    api_fqdn = os.environ['API_FQDN']
    image_endpoint = f'https://{api_fqdn}/v1/runners/ecs/images'

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


def get_default_capacity_provider() -> str:
    """Get the default capacity provider from config."""
    use_spot = os.environ.get('USE_SPOT', 'true').lower() == 'true'
    return 'FARGATE_SPOT' if use_spot else 'FARGATE'


def get_fargate_task_status(cluster: str, task_arn: str) -> Dict[str, Any]:
    """Get the current status of a Fargate task."""
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
    """Check if task was stopped due to Spot interruption."""
    reason = task_status.get('stopped_reason', '')
    return 'Spot' in reason and 'interrupt' in reason.lower()


def wait_for_fargate_task_provisioned(cluster: str, task_arn: str) -> Dict[str, Any]:
    """Wait for a Fargate task to reach running state or fail."""
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
                reason = task_status['stopped_reason']
                logger.warning("Task %s interrupted by Spot: %s", task_arn, reason)
                result['spot_interrupted'] = True
            return result
        if status in ('PENDING', 'PROVISIONING', 'ACTIVATING'):
            if attempt < FARGATE_SPOT_MAX_POLL_ATTEMPTS - 1:
                time.sleep(FARGATE_SPOT_POLL_INTERVAL)
            continue
        return result
    result['success'] = True
    return result


def _get_capacity_provider(job_labels: List[str]) -> str:
    """Determine the capacity provider based on job labels."""
    try:
        parsed = parse_labels(job_labels)
        validate_labels(parsed)
        if is_spot(parsed):
            return 'FARGATE_SPOT'
        return 'FARGATE'
    except (LabelParseError, LabelValidationError) as e:
        default = get_default_capacity_provider()
        logger.warning("Could not parse labels, defaulting to %s: %s", default, e)
        return default


def _launch_fargate_task_in_subnet(cfg: Dict[str, Any], subnet: str) -> Dict[str, Any]:
    run_id = cfg['run_id']
    job_id = cfg['job_id']
    runner_name = f"fargate-runner-{run_id}" if run_id else f"fargate-runner-{job_id}"
    capacity_provider = _get_capacity_provider(cfg['job_labels'])
    logger.info("Using capacity provider %s for job %s", capacity_provider, job_id)

    container_overrides: Dict[str, Any] = {
        'name': os.environ['CONTAINER_NAME'],
        'command': [
            '--repo', cfg['github_repo'], '--name', runner_name,
            '--labels', ','.join(cfg['job_labels']), '--token', cfg['registration_token']
        ],
    }

    github_token = cfg.get('github_token', '')
    if github_token:
        container_overrides['environment'] = [
            {'name': 'GITHUB_TOKEN', 'value': github_token}
        ]

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
        capacityProviderStrategy=[{
            'capacityProvider': capacity_provider, 'weight': 100, 'base': 0
        }],
        overrides={
            'containerOverrides': [container_overrides]
        },
        tags=[
            {'key': 'Type', 'value': 'workflow-runner'},
            {'key': 'ManagedBy', 'value': 'ecs-runner-api'},
            {'key': 'GitHubJobId', 'value': str(cfg['job_id'])},
            {'key': 'JobLabels', 'value': ' '.join(cfg['job_labels'])},
            {'key': 'GitHubRepo', 'value': cfg['github_repo']},
            {'key': 'RunId', 'value': str(cfg['run_id']) if cfg['run_id'] else ''},
            {'key': 'RunnerType', 'value': cfg['runner_type']},
            {'key': 'CapacityProvider', 'value': capacity_provider}
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
        provision_result = wait_for_fargate_task_provisioned(cluster, task_arn)
        if provision_result['spot_interrupted']:
            logger.warning("Task %s spot interrupted, will retry in different AZ", task_arn)
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
            retry_msg = "Retrying after spot interruption (attempt %d/%d)"
            logger.info(retry_msg, attempt + 1, FARGATE_SPOT_MAX_RETRIES)
            continue
        break
    err_msg = "Failed to launch Fargate runner for job %s after %d attempts: %s"
    logger.error(err_msg, cfg['job_id'], FARGATE_SPOT_MAX_RETRIES, last_error)
    result['error'] = last_error if last_error else 'No capacity in any availability zone'
    return result


def launch_fargate_runner(
    job_id: int, job_labels: list, github_repo: str,
    run_id: int | None = None, runner_type: str = 'fargate'
) -> Dict[str, Any]:
    """Launch a Fargate runner for a GitHub Actions job."""
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
        existing_runner = get_existing_runner_for_workflow(
            github_token, github_repo, run_id, job_labels)
        if existing_runner:
            runner_name = existing_runner.get('name')
            logger.info("Reusing existing runner %s for run %s", runner_name, run_id)
            result = {
                'success': True,
                'job_id': job_id,
                'runner_type': runner_type,
                'run_id': run_id,
                'runner_name': runner_name,
                'reused': True
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
        'registration_token': registration_token, 'run_id': run_id, 'runner_type': runner_type,
        'github_token': github_token,
    }
    return _try_launch_fargate_task(runner_config)


def get_ecs_runner_status() -> Dict[str, Any]:
    """Get the status of running ECS tasks."""
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
                started = task.get('startedAt')
                started_at = started.isoformat() if started else None
                tasks.append({
                    'task_arn': task['taskArn'],
                    'task_id': task['taskArn'].split('/')[-1],
                    'status': task['lastStatus'],
                    'desired_status': task['desiredStatus'],
                    'started_at': started_at,
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
