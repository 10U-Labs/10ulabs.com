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
    parameter_name = os.environ.get('GITHUB_TOKEN_SECRET_NAME', '')
    if not parameter_name:
        return ''
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        logger.error("Failed to get GitHub token: %s", e)
        return ''


def get_workflow_run_status(github_token: str, github_repo: str, run_id: str) -> str:
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
            return data.get('status', 'unknown')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 'not_found'
        logger.error("Failed to get workflow run status: %s", e)
        return 'unknown'
    except urllib.error.URLError as e:
        logger.error("Failed to get workflow run status: %s", e)
        return 'unknown'


def delete_github_runner(github_token: str, github_repo: str, runner_name: str) -> bool:
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
                    break
            if runner_id is None:
                return True
        delete_req = urllib.request.Request(
            f'https://api.github.com/repos/{github_repo}/actions/runners/{runner_id}',
            method='DELETE',
            headers=headers
        )
        with urllib.request.urlopen(delete_req, timeout=10):
            logger.info("Deleted GitHub runner: %s", runner_name)
            return True
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return True
        logger.error("Failed to delete GitHub runner: %s", e)
        return False
    except urllib.error.URLError as e:
        logger.error("Failed to delete GitHub runner: %s", e)
        return False


def get_all_workflow_runners() -> list:
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if not table_name:
        return []
    try:
        response = get_dynamodb_client().scan(TableName=table_name)
        runners = []
        for item in response.get('Items', []):
            runners.append({
                'run_id': item['run_id']['S'],
                'runner_type': item['runner_type']['S'],
                'resource_id': item['resource_id']['S'],
                'runner_name': item.get('runner_name', {}).get('S', ''),
                'github_repo': item.get('github_repo', {}).get('S', ''),
                'created_at': int(item.get('created_at', {}).get('N', '0'))
            })
        return runners
    except ClientError as e:
        logger.error("Failed to scan workflow runners: %s", e)
        return []


def delete_workflow_runner(run_id: str, runner_type: str) -> bool:
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if not table_name:
        return False
    try:
        get_dynamodb_client().delete_item(
            TableName=table_name,
            Key={
                'run_id': {'S': run_id},
                'runner_type': {'S': runner_type}
            }
        )
        return True
    except ClientError as e:
        logger.error("Failed to delete workflow runner: %s", e)
        return False


def terminate_ecs_task(task_arn: str) -> bool:
    cluster = os.environ.get('ECS_CLUSTER', '')
    if not cluster:
        return False
    try:
        get_ecs_client().stop_task(cluster=cluster, task=task_arn, reason='Stale runner cleanup')
        logger.info("Stopped ECS task: %s", task_arn)
        return True
    except ClientError as e:
        if 'InvalidParameterException' in str(e) or 'TaskNotFound' in str(e):
            logger.info("Task already stopped or not found: %s", task_arn)
            return True
        logger.error("Failed to stop ECS task: %s", e)
        return False


def terminate_ec2_instance(instance_id: str) -> bool:
    try:
        get_ec2_client().terminate_instances(InstanceIds=[instance_id])
        logger.info("Terminated EC2 instance: %s", instance_id)
        return True
    except ClientError as e:
        if 'InvalidInstanceID' in str(e):
            logger.info("Instance already terminated or not found: %s", instance_id)
            return True
        logger.error("Failed to terminate EC2 instance: %s", e)
        return False


def cleanup_stale_runners() -> dict:
    github_token = get_github_token()
    if not github_token:
        logger.error("No GitHub token available")
        return {'cleaned': 0, 'errors': 1}
    runners = get_all_workflow_runners()
    current_time = int(time.time())
    cleaned_count = 0
    error_count = 0
    for runner in runners:
        run_id = runner['run_id']
        runner_type = runner['runner_type']
        resource_id = runner['resource_id']
        runner_name = runner['runner_name']
        github_repo = runner['github_repo']
        created_at = runner['created_at']
        age_seconds = current_time - created_at if created_at else STALE_THRESHOLD_SECONDS + 1
        if age_seconds < STALE_THRESHOLD_SECONDS:
            continue
        workflow_status = get_workflow_run_status(github_token, github_repo, run_id)
        if workflow_status in ['queued', 'in_progress', 'waiting']:
            logger.info("Workflow %s still active, skipping runner cleanup", run_id)
            continue
        logger.info(
            "Cleaning up stale runner: run_id=%s, type=%s, resource=%s, workflow_status=%s",
            run_id, runner_type, resource_id, workflow_status
        )
        success = False
        if runner_type.startswith('ec2'):
            success = terminate_ec2_instance(resource_id)
        elif runner_type.startswith('fargate'):
            success = terminate_ecs_task(resource_id)
        if success:
            delete_workflow_runner(run_id, runner_type)
            if runner_name and github_repo:
                delete_github_runner(github_token, github_repo, runner_name)
            cleaned_count += 1
        else:
            error_count += 1
    result = {'cleaned': cleaned_count, 'errors': error_count}
    logger.info("Stale runner cleanup complete: %s", result)
    return result


def lambda_handler(event, _context):
    logger.info("Starting stale runner cleanup")
    result = cleanup_stale_runners()
    response = {
        'statusCode': 200,
        'body': json.dumps(result)
    }
    return response
