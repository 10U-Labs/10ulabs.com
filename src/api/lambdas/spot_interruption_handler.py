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


def get_dynamodb_client():
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def get_ssm_client():
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_ecs_client():
    if 'ecs' not in _clients:
        _clients['ecs'] = boto3.client('ecs')
    return _clients['ecs']


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
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        logger.error("Failed to get workflow run status: %s", e)
    return result


def get_runner_from_dynamodb(run_id: str, runner_type: str) -> dict:
    result: dict = {}
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if table_name:
        try:
            response = get_dynamodb_client().get_item(
                TableName=table_name,
                Key={
                    'run_id': {'S': run_id},
                    'runner_type': {'S': runner_type}
                }
            )
            item = response.get('Item')
            if item:
                result = {
                    'run_id': item['run_id']['S'],
                    'runner_type': item['runner_type']['S'],
                    'resource_id': item['resource_id']['S'],
                    'runner_name': item.get('runner_name', {}).get('S', ''),
                    'github_repo': item.get('github_repo', {}).get('S', '')
                }
        except ClientError as e:
            logger.error("Failed to get runner from DynamoDB: %s", e)
    return result


def trigger_runner_replacement(run_id: str, runner_type: str, github_repo: str) -> bool:
    result = False
    api_base_url = os.environ.get('API_BASE_URL', '')
    api_key = os.environ.get('API_KEY', '')
    if not api_base_url or not api_key:
        logger.error("API_BASE_URL or API_KEY not configured")
    else:
        endpoint_suffix = 'ec2-runner' if runner_type.startswith('ec2') else 'docker-runner'
        endpoint = f"{api_base_url}/v1/{endpoint_suffix}"
        job_id = int(time.time() * 1000)
        labels = ['ec2'] if runner_type.startswith('ec2') else ['fargate']
        if 'e2e' in runner_type:
            labels.append('e2e')
        labels.append(f'runner-{run_id}')
        payload = {
            'job_id': job_id,
            'job_labels': labels,
            'github_repo': github_repo,
            'run_id': int(run_id),
            'runner_type': runner_type
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key
                }
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                logger.info("Replacement runner launched: %s", response.read().decode())
                result = True
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error("Failed to trigger runner replacement: %s", e)
    return result


def handle_ecs_task_stopped(event: dict) -> dict:
    detail = event.get('detail', {})
    stop_code = detail.get('stopCode', '')
    stopped_reason = detail.get('stoppedReason', '')
    task_arn = detail.get('taskArn', '')
    tag_dict = _get_ecs_task_tags(task_arn)
    run_id = tag_dict.get('RunId', '')
    runner_type = tag_dict.get('RunnerType', '')
    github_repo = tag_dict.get('GitHubRepo', '')
    logger.info(
        "ECS task stopped: arn=%s, stopCode=%s, reason=%s, run_id=%s, runner_type=%s",
        task_arn, stop_code, stopped_reason, run_id, runner_type
    )
    result: dict = {'statusCode': 200, 'body': 'No run_id or runner_type'}
    if not run_id or not runner_type:
        logger.info("No run_id or runner_type in task tags, skipping")
    else:
        is_spot_interruption = 'SpotInterruption' in stop_code or 'capacity' in stopped_reason.lower()
        if not is_spot_interruption:
            logger.info("Not a spot interruption, skipping replacement")
            result = {'statusCode': 200, 'body': 'Not a spot interruption'}
        else:
            github_token = get_github_token()
            if not github_token:
                logger.error("No GitHub token available")
                result = {'statusCode': 500, 'body': 'No GitHub token'}
            else:
                workflow_status = get_workflow_run_status(github_token, github_repo, run_id)
                if workflow_status not in ['queued', 'in_progress', 'waiting']:
                    logger.info("Workflow run %s is not active (status=%s), skipping replacement", run_id, workflow_status)
                    result = {'statusCode': 200, 'body': f'Workflow not active: {workflow_status}'}
                else:
                    logger.info("Triggering replacement runner for run_id=%s, runner_type=%s", run_id, runner_type)
                    success = trigger_runner_replacement(run_id, runner_type, github_repo)
                    result = {'statusCode': 200, 'body': 'Replacement runner triggered'} if success else {'statusCode': 500, 'body': 'Failed to trigger replacement'}
    return result


def _get_ecs_task_tags(task_arn: str) -> dict:
    tag_dict: dict = {}
    try:
        cluster = os.environ.get('ECS_CLUSTER', '')
        response = get_ecs_client().describe_tasks(
            cluster=cluster,
            tasks=[task_arn],
            include=['TAGS']
        )
        tasks = response.get('tasks', [])
        if tasks:
            tags = tasks[0].get('tags', [])
            tag_dict = {tag['key']: tag['value'] for tag in tags}
    except (ClientError, IndexError, KeyError) as e:
        logger.error("Failed to get ECS task tags: %s", e)
    return tag_dict


def _get_ec2_instance_tags(instance_id: str) -> dict:
    tag_dict: dict = {}
    try:
        response = boto3.client('ec2').describe_instances(InstanceIds=[instance_id])
        tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
        tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    except (ClientError, IndexError, KeyError) as e:
        logger.error("Failed to get instance tags: %s", e)
    return tag_dict


def handle_ec2_spot_interruption(event: dict) -> dict:
    instance_id = event.get('detail', {}).get('instance-id', '')
    logger.info("EC2 spot interruption warning for instance: %s", instance_id)
    result: dict = {'statusCode': 500, 'body': 'Failed to get instance tags'}
    tag_dict = _get_ec2_instance_tags(instance_id)
    if tag_dict:
        run_id = tag_dict.get('RunId', '')
        runner_type = tag_dict.get('RunnerType', '')
        github_repo = tag_dict.get('GitHubRepo', '')
        if not run_id or not runner_type:
            logger.info("No run_id or runner_type in instance tags, skipping")
            result = {'statusCode': 200, 'body': 'No run_id or runner_type'}
        else:
            github_token = get_github_token()
            if not github_token:
                logger.error("No GitHub token available")
                result = {'statusCode': 500, 'body': 'No GitHub token'}
            else:
                workflow_status = get_workflow_run_status(github_token, github_repo, run_id)
                if workflow_status not in ['queued', 'in_progress', 'waiting']:
                    logger.info("Workflow run %s is not active (status=%s), skipping replacement", run_id, workflow_status)
                    result = {'statusCode': 200, 'body': f'Workflow not active: {workflow_status}'}
                else:
                    logger.info("Triggering replacement runner for run_id=%s, runner_type=%s", run_id, runner_type)
                    success = trigger_runner_replacement(run_id, runner_type, github_repo)
                    result = {'statusCode': 200, 'body': 'Replacement runner triggered'} if success else {'statusCode': 500, 'body': 'Failed to trigger replacement'}
    return result


def lambda_handler(event, _context):
    logger.info("Received event: %s", json.dumps(event))
    source = event.get('source', '')
    detail_type = event.get('detail-type', '')
    result = {'statusCode': 200, 'body': 'Event ignored'}
    if source == 'aws.ecs' and detail_type == 'ECS Task State Change':
        last_status = event.get('detail', {}).get('lastStatus', '')
        if last_status == 'STOPPED':
            result = handle_ecs_task_stopped(event)
    elif source == 'aws.ec2' and detail_type == 'EC2 Spot Instance Interruption Warning':
        result = handle_ec2_spot_interruption(event)
    else:
        logger.info("Ignoring event: source=%s, detail-type=%s", source, detail_type)
    return result
