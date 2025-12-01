import json
import logging
import os
import urllib.error
import urllib.request
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {}


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


def rerun_github_job(github_token: str, github_repo: str, job_id: str) -> bool:
    result = False
    if not job_id:
        logger.error("No job_id provided for re-run")
    else:
        url = f'https://api.github.com/repos/{github_repo}/actions/jobs/{job_id}/rerun'
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        try:
            req = urllib.request.Request(url, data=b'', headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 201:
                    logger.info("Successfully triggered re-run for job %s", job_id)
                    result = True
                else:
                    logger.warning("Unexpected response status %s for job re-run", response.status)
        except urllib.error.HTTPError as e:
            logger.error("Failed to re-run job %s: HTTP %s - %s", job_id, e.code, e.reason)
        except urllib.error.URLError as e:
            logger.error("Failed to re-run job %s: %s", job_id, e)
    return result


def handle_ecs_task_stopped(event: dict) -> dict:
    detail = event.get('detail', {})
    stop_code = detail.get('stopCode', '')
    stopped_reason = detail.get('stoppedReason', '')
    task_arn = detail.get('taskArn', '')
    tag_dict = _get_ecs_task_tags(task_arn)
    run_id = tag_dict.get('RunId', '')
    github_repo = tag_dict.get('GitHubRepo', '')
    job_id = tag_dict.get('GitHubJobId', '')
    logger.info(
        "ECS task stopped: arn=%s, stopCode=%s, reason=%s, run_id=%s, job_id=%s",
        task_arn, stop_code, stopped_reason, run_id, job_id
    )
    result: dict = {'statusCode': 200, 'body': 'No run_id or job_id'}
    if not run_id or not job_id:
        logger.info("No run_id or job_id in task tags, skipping")
    else:
        is_spot_interruption = 'SpotInterruption' in stop_code or 'capacity' in stopped_reason.lower()
        if not is_spot_interruption:
            logger.info("Not a spot interruption, skipping job re-run")
            result = {'statusCode': 200, 'body': 'Not a spot interruption'}
        else:
            github_token = get_github_token()
            if not github_token:
                logger.error("No GitHub token available")
                result = {'statusCode': 500, 'body': 'No GitHub token'}
            else:
                workflow_status = get_workflow_run_status(github_token, github_repo, run_id)
                if workflow_status not in ['queued', 'in_progress', 'waiting']:
                    logger.info("Workflow run %s is not active (status=%s), skipping job re-run", run_id, workflow_status)
                    result = {'statusCode': 200, 'body': f'Workflow not active: {workflow_status}'}
                else:
                    logger.info("Triggering job re-run for job_id=%s, run_id=%s", job_id, run_id)
                    success = rerun_github_job(github_token, github_repo, job_id)
                    result = {'statusCode': 200, 'body': 'Job re-run triggered'} if success else {'statusCode': 500, 'body': 'Failed to trigger job re-run'}
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
        github_repo = tag_dict.get('GitHubRepo', '')
        job_id = tag_dict.get('GitHubJobId', '')
        if not run_id or not job_id:
            logger.info("No run_id or job_id in instance tags, skipping")
            result = {'statusCode': 200, 'body': 'No run_id or job_id'}
        else:
            github_token = get_github_token()
            if not github_token:
                logger.error("No GitHub token available")
                result = {'statusCode': 500, 'body': 'No GitHub token'}
            else:
                workflow_status = get_workflow_run_status(github_token, github_repo, run_id)
                if workflow_status not in ['queued', 'in_progress', 'waiting']:
                    logger.info("Workflow run %s is not active (status=%s), skipping job re-run", run_id, workflow_status)
                    result = {'statusCode': 200, 'body': f'Workflow not active: {workflow_status}'}
                else:
                    logger.info("Triggering job re-run for job_id=%s, run_id=%s", job_id, run_id)
                    success = rerun_github_job(github_token, github_repo, job_id)
                    result = {'statusCode': 200, 'body': 'Job re-run triggered'} if success else {'statusCode': 500, 'body': 'Failed to trigger job re-run'}
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
