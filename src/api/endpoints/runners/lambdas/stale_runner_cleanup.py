"""Lambda handler for cleaning up stale and orphaned workflow runners."""
import json
import logging
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {}

STALE_THRESHOLD_SECONDS = 3600
ECS_MANAGED_BY_TAG = 'ecs-runner-api'
WORKFLOW_RUNNER_TYPE_TAG = 'workflow-runner'


def get_dynamodb_client():
    """Get or create cached DynamoDB client."""
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def get_ecs_client():
    """Get or create cached ECS client."""
    if 'ecs' not in _clients:
        _clients['ecs'] = boto3.client('ecs')
    return _clients['ecs']


def get_ec2_client():
    """Get or create cached EC2 client."""
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def get_ssm_client():
    """Get or create cached SSM client."""
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_github_token() -> str:
    """Retrieve GitHub token from SSM Parameter Store."""
    result = ''
    parameter_name = os.environ.get('GITHUB_TOKEN_SECRET_NAME', '')
    if parameter_name:
        try:
            response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
            result = response['Parameter']['Value']
        except ClientError as e:
            logger.error("Failed to get GitHub token: %s", e)
    return result


def get_workflow_run_status(github_token: str, github_repo: str, run_id: str) -> str:
    """Get the status of a GitHub Actions workflow run."""
    result = 'unknown'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    try:
        req = urllib.request.Request(
            f'https://api.github.com/repos/{github_repo}/actions/runs/{run_id}',
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            result = data.get('status', 'unknown')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            result = 'not_found'
        else:
            logger.error("Failed to get workflow run status: %s", e)
    except urllib.error.URLError as e:
        logger.error("Failed to get workflow run status: %s", e)
    return result


def get_all_github_runners(github_token: str, github_repo: str) -> list | None:
    """Get all self-hosted runners for a GitHub repository."""
    result: list | None = None
    runners: list = []
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    try:
        page = 1
        has_more = True
        while has_more:
            base = f'https://api.github.com/repos/{github_repo}/actions/runners'
            url = f'{base}?per_page=100&page={page}'
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                page_runners = data.get('runners', [])
                runners.extend(page_runners)
                if len(page_runners) < 100:
                    has_more = False
                else:
                    page += 1
        result = runners
    except urllib.error.HTTPError as e:
        logger.error("Failed to list GitHub runners: %s", e)
    except urllib.error.URLError as e:
        logger.error("Failed to list GitHub runners: %s", e)
    return result


def delete_github_runner_by_id(
    github_token: str, github_repo: str, runner_id: int, runner_name: str
) -> bool:
    """Delete a GitHub runner by its ID."""
    result = False
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    try:
        delete_req = urllib.request.Request(
            f'https://api.github.com/repos/{github_repo}/actions/runners/{runner_id}',
            method='DELETE',
            headers=headers
        )
        with urllib.request.urlopen(delete_req, timeout=10):
            logger.info("Deleted GitHub runner: %s", runner_name)
            result = True
    except urllib.error.HTTPError as e:
        if e.code == 204:
            result = True
        else:
            logger.error("Failed to delete GitHub runner %s: %s", runner_name, e)
    except urllib.error.URLError as e:
        logger.error("Failed to delete GitHub runner %s: %s", runner_name, e)
    return result


def delete_github_runner(github_token: str, github_repo: str, runner_name: str) -> bool:
    """Delete a GitHub runner by its name."""
    result = False
    runners = get_all_github_runners(github_token, github_repo)
    if runners is None:
        result = False
    else:
        runner_id = None
        for runner in runners:
            if runner.get('name') == runner_name:
                runner_id = runner.get('id')
        if runner_id is None:
            result = True
        else:
            result = delete_github_runner_by_id(github_token, github_repo, runner_id, runner_name)
    return result


def get_all_workflow_runners() -> list:
    """Get all workflow runners from DynamoDB."""
    runners: list = []
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if table_name:
        try:
            response = get_dynamodb_client().scan(TableName=table_name)
            for item in response.get('Items', []):
                runners.append({
                    'run_id': item['run_id']['S'],
                    'runner_type': item['runner_type']['S'],
                    'resource_id': item['resource_id']['S'],
                    'runner_name': item.get('runner_name', {}).get('S', ''),
                    'github_repo': item.get('github_repo', {}).get('S', ''),
                    'created_at': int(item.get('created_at', {}).get('N', '0'))
                })
        except ClientError as e:
            logger.error("Failed to scan workflow runners: %s", e)
    return runners


def delete_workflow_runner(run_id: str, runner_type: str) -> bool:
    """Delete a workflow runner from DynamoDB."""
    result = False
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if table_name:
        try:
            get_dynamodb_client().delete_item(
                TableName=table_name,
                Key={
                    'run_id': {'S': run_id},
                    'runner_type': {'S': runner_type}
                }
            )
            result = True
        except ClientError as e:
            logger.error("Failed to delete workflow runner: %s", e)
    return result


def terminate_ecs_task(task_arn: str) -> bool:
    """Terminate an ECS task."""
    result = False
    cluster = os.environ.get('ECS_CLUSTER', '')
    if cluster:
        try:
            get_ecs_client().stop_task(
                cluster=cluster, task=task_arn, reason='Stale runner cleanup'
            )
            logger.info("Stopped ECS task: %s", task_arn)
            result = True
        except ClientError as e:
            if 'InvalidParameterException' in str(e) or 'TaskNotFound' in str(e):
                logger.info("Task already stopped or not found: %s", task_arn)
                result = True
            else:
                logger.error("Failed to stop ECS task: %s", e)
    return result


def terminate_ec2_instance(instance_id: str) -> bool:
    """Terminate an EC2 instance."""
    result = False
    try:
        get_ec2_client().terminate_instances(InstanceIds=[instance_id])
        logger.info("Terminated EC2 instance: %s", instance_id)
        result = True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code in ['InvalidInstanceID.NotFound', 'InvalidInstanceID.Malformed']:
            logger.info("Instance already terminated or not found: %s", instance_id)
            result = True
        else:
            logger.error("Failed to terminate EC2 instance: %s", e)
    return result


def _is_runner_stale(created_at: int, current_time: int) -> bool:
    age_seconds = current_time - created_at if created_at else STALE_THRESHOLD_SECONDS + 1
    return age_seconds >= STALE_THRESHOLD_SECONDS


def _is_orphaned_ecs_task(task: dict, current_time: datetime) -> dict | None:
    tags = {t['key']: t['value'] for t in task.get('tags', [])}
    if tags.get('Type') != WORKFLOW_RUNNER_TYPE_TAG or tags.get('ManagedBy') != ECS_MANAGED_BY_TAG:
        return None
    started_at = task.get('startedAt')
    if not started_at:
        return None
    age_seconds = (current_time - started_at).total_seconds()
    if age_seconds < STALE_THRESHOLD_SECONDS:
        return None
    return {
        'task_arn': task['taskArn'],
        'age_seconds': int(age_seconds),
        'runner_name': tags.get('Name', ''),
        'github_repo': tags.get('GitHubRepo', '')
    }


def get_orphaned_ecs_tasks() -> list:
    """Get ECS tasks that are running past the stale threshold."""
    tasks: list[dict] = []
    cluster = os.environ.get('ECS_CLUSTER', '')
    if not cluster:
        return tasks
    try:
        ecs = get_ecs_client()
        paginator = ecs.get_paginator('list_tasks')
        task_arns = []
        for page in paginator.paginate(cluster=cluster, desiredStatus='RUNNING'):
            task_arns.extend(page.get('taskArns', []))
        if not task_arns:
            return tasks
        current_time = datetime.now(timezone.utc)
        for i in range(0, len(task_arns), 100):
            batch = task_arns[i:i + 100]
            response = ecs.describe_tasks(cluster=cluster, tasks=batch, include=['TAGS'])
            for task in response.get('tasks', []):
                orphaned = _is_orphaned_ecs_task(task, current_time)
                if orphaned:
                    tasks.append(orphaned)
    except ClientError as e:
        logger.error("Failed to get orphaned ECS tasks: %s", e)
    return tasks


def get_orphaned_ec2_instances() -> list:
    """Get EC2 instances that are running past the stale threshold."""
    instances: list[dict] = []
    ec2_managed_by_tag = os.environ.get('EC2_MANAGED_BY_TAG', '')
    if not ec2_managed_by_tag:
        return instances
    try:
        ec2 = get_ec2_client()
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Type', 'Values': [WORKFLOW_RUNNER_TYPE_TAG]},
                {'Name': 'tag:ManagedBy', 'Values': [ec2_managed_by_tag]},
                {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
            ]
        )
        current_time = datetime.now(timezone.utc)
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                launch_time = instance.get('LaunchTime')
                if launch_time:
                    age_seconds = (current_time - launch_time).total_seconds()
                    if age_seconds >= STALE_THRESHOLD_SECONDS:
                        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
                        instances.append({
                            'instance_id': instance['InstanceId'],
                            'age_seconds': int(age_seconds),
                            'runner_name': tags.get('Name', ''),
                            'github_repo': tags.get('GitHubRepo', '')
                        })
    except ClientError as e:
        logger.error("Failed to get orphaned EC2 instances: %s", e)
    return instances


def _has_running_ec2_by_name(runner_name: str) -> bool:
    result = False
    ec2_managed_by_tag = os.environ.get('EC2_MANAGED_BY_TAG', '')
    if not ec2_managed_by_tag:
        result = False
    else:
        try:
            response = get_ec2_client().describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [runner_name]},
                    {'Name': 'tag:ManagedBy', 'Values': [ec2_managed_by_tag]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
                ]
            )
            for reservation in response.get('Reservations', []):
                if reservation.get('Instances'):
                    result = True
        except ClientError as e:
            logger.error("Failed to check EC2 instance by name %s: %s", runner_name, e)
    return result


def _extract_run_id_from_runner_name(runner_name: str) -> str:
    if runner_name.startswith('fargate-runner-'):
        return runner_name.replace('fargate-runner-', '')
    if runner_name.startswith('ec2-runner-'):
        return runner_name.replace('ec2-runner-', '')
    return ''


def _get_ecs_task_arns(cluster: str) -> list:
    task_arns = []
    ecs = get_ecs_client()
    paginator = ecs.get_paginator('list_tasks')
    for status in ['RUNNING', 'PENDING']:
        for page in paginator.paginate(cluster=cluster, desiredStatus=status):
            task_arns.extend(page.get('taskArns', []))
    return task_arns


def _check_tasks_for_run_id(cluster: str, task_arns: list, run_id: str) -> bool:
    ecs = get_ecs_client()
    for i in range(0, len(task_arns), 100):
        batch = task_arns[i:i + 100]
        response = ecs.describe_tasks(cluster=cluster, tasks=batch, include=['TAGS'])
        for task in response.get('tasks', []):
            tags = {t['key']: t['value'] for t in task.get('tags', [])}
            if tags.get('RunId') == run_id:
                return True
    return False


def _has_running_ecs_task_by_name(runner_name: str) -> bool:
    result = False
    cluster = os.environ.get('ECS_CLUSTER', '')
    run_id = _extract_run_id_from_runner_name(runner_name)
    if cluster and run_id:
        try:
            task_arns = _get_ecs_task_arns(cluster)
            result = _check_tasks_for_run_id(cluster, task_arns, run_id)
        except ClientError as e:
            logger.error("Failed to check ECS task by name %s: %s", runner_name, e)
    return result


def _runner_has_infrastructure(runner_name: str) -> bool:
    has_ec2 = _has_running_ec2_by_name(runner_name)
    has_ecs = _has_running_ecs_task_by_name(runner_name) if not has_ec2 else False
    return has_ec2 or has_ecs


def cleanup_orphaned_github_runners(github_token: str) -> dict:
    """Clean up GitHub runners without backing infrastructure."""
    counts = {'github_cleaned': 0, 'errors': 0}
    github_repo = os.environ.get('GITHUB_REPO', '')
    if not github_repo or not github_token:
        counts['errors'] = 1
    else:
        runners = get_all_github_runners(github_token, github_repo)
        if runners is None:
            counts['errors'] = 1
            runners = []
        for runner in runners:
            status = runner.get('status', '')
            runner_name = runner.get('name', '')
            runner_id = runner.get('id')
            if status != 'offline':
                continue
            if not runner_name or not runner_id:
                continue
            if _runner_has_infrastructure(runner_name):
                logger.info("Offline runner %s has infrastructure, skipping", runner_name)
                continue
            logger.info("Cleaning up orphaned GitHub runner: %s (id=%s)", runner_name, runner_id)
            if delete_github_runner_by_id(github_token, github_repo, runner_id, runner_name):
                counts['github_cleaned'] += 1
            else:
                counts['errors'] += 1
    logger.info("Orphaned GitHub runner cleanup complete: cleaned=%d, errors=%d",
                counts['github_cleaned'], counts['errors'])
    return counts


def cleanup_orphaned_resources(github_token: str) -> dict:
    """Clean up orphaned ECS tasks and EC2 instances."""
    counts = {'ecs_cleaned': 0, 'ec2_cleaned': 0, 'errors': 0}
    github_repo = os.environ.get('GITHUB_REPO', '')
    orphaned_tasks = get_orphaned_ecs_tasks()
    for task in orphaned_tasks:
        logger.info(
            "Cleaning orphaned ECS task: %s (age=%ds)",
            task['task_arn'], task['age_seconds']
        )
        if terminate_ecs_task(task['task_arn']):
            counts['ecs_cleaned'] += 1
            runner_name = task.get('runner_name', '')
            task_repo = task.get('github_repo', '') or github_repo
            if runner_name and task_repo and github_token:
                delete_github_runner(github_token, task_repo, runner_name)
        else:
            counts['errors'] += 1
    orphaned_instances = get_orphaned_ec2_instances()
    for instance in orphaned_instances:
        logger.info(
            "Cleaning orphaned EC2 instance: %s (age=%ds)",
            instance['instance_id'], instance['age_seconds']
        )
        if terminate_ec2_instance(instance['instance_id']):
            counts['ec2_cleaned'] += 1
            runner_name = instance.get('runner_name', '')
            instance_repo = instance.get('github_repo', '') or github_repo
            if runner_name and instance_repo and github_token:
                delete_github_runner(github_token, instance_repo, runner_name)
        else:
            counts['errors'] += 1
    logger.info("Orphaned resource cleanup complete: ecs=%d, ec2=%d, errors=%d",
                counts['ecs_cleaned'], counts['ec2_cleaned'], counts['errors'])
    return counts


def _terminate_runner(runner_type: str, resource_id: str) -> bool:
    result = False
    if runner_type.startswith('ec2'):
        result = terminate_ec2_instance(resource_id)
    elif runner_type.startswith('fargate'):
        result = terminate_ecs_task(resource_id)
    return result


def _cleanup_single_runner(github_token: str, runner: dict, counts: dict):
    workflow_status = get_workflow_run_status(github_token, runner['github_repo'], runner['run_id'])
    if workflow_status in ['queued', 'in_progress', 'waiting']:
        logger.info("Workflow %s still active, skipping runner cleanup", runner['run_id'])
    else:
        logger.info(
            "Cleaning up stale runner: run_id=%s, type=%s, resource=%s, workflow_status=%s",
            runner['run_id'], runner['runner_type'], runner['resource_id'], workflow_status
        )
        if _terminate_runner(runner['runner_type'], runner['resource_id']):
            delete_workflow_runner(runner['run_id'], runner['runner_type'])
            if runner['runner_name'] and runner['github_repo']:
                delete_github_runner(github_token, runner['github_repo'], runner['runner_name'])
            counts['cleaned'] += 1
        else:
            counts['errors'] += 1


def cleanup_stale_runners() -> dict:
    """Clean up stale runners from DynamoDB."""
    counts = {'cleaned': 0, 'errors': 0}
    github_token = get_github_token()
    if not github_token:
        logger.error("No GitHub token available")
        counts['errors'] = 1
    else:
        runners = get_all_workflow_runners()
        current_time = int(time.time())
        for runner in runners:
            if _is_runner_stale(runner['created_at'], current_time):
                _cleanup_single_runner(github_token, runner, counts)
        logger.info(
            "Stale runner cleanup: cleaned=%d, errors=%d",
            counts['cleaned'], counts['errors']
        )
    return counts


def lambda_handler(_event, _context):
    """Main Lambda handler for stale runner cleanup."""
    logger.info("Starting stale runner cleanup")
    github_token = get_github_token()
    dynamo_result = cleanup_stale_runners()
    orphan_result = cleanup_orphaned_resources(github_token)
    github_result = cleanup_orphaned_github_runners(github_token)
    result = {
        'dynamodb_cleaned': dynamo_result['cleaned'],
        'orphaned_ecs_cleaned': orphan_result['ecs_cleaned'],
        'orphaned_ec2_cleaned': orphan_result['ec2_cleaned'],
        'orphaned_github_cleaned': github_result['github_cleaned'],
        'errors': dynamo_result['errors'] + orphan_result['errors'] + github_result['errors']
    }
    logger.info("Full cleanup complete: %s", result)
    response = {
        'statusCode': 200,
        'body': json.dumps(result)
    }
    return response
