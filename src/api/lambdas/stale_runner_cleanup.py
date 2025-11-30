import json
import logging
import os
import time
import urllib.error
import urllib.request
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {}

STALE_THRESHOLD_SECONDS = 3600


def get_dynamodb_client():
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def get_ecs_client():
    if 'ecs' not in _clients:
        _clients['ecs'] = boto3.client('ecs')
    return _clients['ecs']


def get_ec2_client():
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def get_ssm_client():
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_github_token() -> str:
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


def delete_github_runner(github_token: str, github_repo: str, runner_name: str) -> bool:
    result = False
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    try:
        req = urllib.request.Request(
            f'https://api.github.com/repos/{github_repo}/actions/runners',
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            runners = data.get('runners', [])
            runner_id = None
            for runner in runners:
                if runner.get('name') == runner_name:
                    runner_id = runner.get('id')
        if runner_id is None:
            result = True
        else:
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
            logger.error("Failed to delete GitHub runner: %s", e)
    except urllib.error.URLError as e:
        logger.error("Failed to delete GitHub runner: %s", e)
    return result


def get_all_workflow_runners() -> list:
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
    result = False
    cluster = os.environ.get('ECS_CLUSTER', '')
    if cluster:
        try:
            get_ecs_client().stop_task(cluster=cluster, task=task_arn, reason='Stale runner cleanup')
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
        logger.info("Stale runner cleanup complete: cleaned=%d, errors=%d", counts['cleaned'], counts['errors'])
    return counts


def lambda_handler(_event, _context):
    logger.info("Starting stale runner cleanup")
    result = cleanup_stale_runners()
    response = {
        'statusCode': 200,
        'body': json.dumps(result)
    }
    return response
