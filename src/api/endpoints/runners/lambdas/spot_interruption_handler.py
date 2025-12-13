"""Lambda handler for EC2 and ECS spot instance interruption events."""
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Tuple

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {}


def get_ssm_client():
    """Get or create cached SSM client."""
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_ecs_client():
    """Get or create cached ECS client."""
    if 'ecs' not in _clients:
        _clients['ecs'] = boto3.client('ecs')
    return _clients['ecs']


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


def get_workflow_run_status(
    github_token: str, github_repo: str, run_id: str
) -> str:
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
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        logger.error("Failed to get workflow run status: %s", e)
    return result


def cancel_workflow_run(github_token: str, github_repo: str, run_id: str) -> bool:
    """Cancel a GitHub Actions workflow run."""
    url = f'https://api.github.com/repos/{github_repo}/actions/runs/{run_id}/cancel'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    try:
        req = urllib.request.Request(url, data=b'', headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 202:
                logger.info("Successfully cancelled workflow run %s", run_id)
                return True
            logger.warning("Unexpected response status %s for cancel", response.status)
    except urllib.error.HTTPError as e:
        logger.error("Failed to cancel workflow %s: HTTP %s - %s", run_id, e.code, e.reason)
    except urllib.error.URLError as e:
        logger.error("Failed to cancel workflow %s: %s", run_id, e)
    return False


def create_check_run_annotation(
    github_token: str,
    github_repo: str,
    head_sha: str,
    title: str,
    summary: str
) -> bool:
    """Create a Check Run with annotation explaining the cancellation."""
    url = f'https://api.github.com/repos/{github_repo}/check-runs'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json'
    }
    payload = {
        'name': 'Spot Interruption Handler',
        'head_sha': head_sha,
        'status': 'completed',
        'conclusion': 'neutral',
        'output': {
            'title': title,
            'summary': summary
        }
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 201:
                logger.info("Successfully created check run annotation")
                return True
            logger.warning("Unexpected response status %s for check run", response.status)
    except urllib.error.HTTPError as e:
        logger.error("Failed to create check run: HTTP %s - %s", e.code, e.reason)
    except urllib.error.URLError as e:
        logger.error("Failed to create check run: %s", e)
    return False


def wait_for_workflow_completion(
    github_token: str,
    github_repo: str,
    run_id: str,
    timeout_seconds: int = 60
) -> bool:
    """Poll workflow run until it completes or times out."""
    url = f'https://api.github.com/repos/{github_repo}/actions/runs/{run_id}'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                if data.get('status') == 'completed':
                    logger.info("Workflow %s completed", run_id)
                    return True
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.warning("Error polling workflow status: %s", e)
        time.sleep(5)
    logger.warning("Timeout waiting for workflow %s to complete", run_id)
    return False


def get_workflow_info_from_run(
    github_token: str,
    github_repo: str,
    run_id: str
) -> Tuple[str, str]:
    """Get workflow ID and head_sha from a workflow run."""
    url = f'https://api.github.com/repos/{github_repo}/actions/runs/{run_id}'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            workflow_id = str(data.get('workflow_id', ''))
            head_sha = data.get('head_sha', '')
            return (workflow_id, head_sha)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        logger.error("Failed to get workflow info: %s", e)
    return ('', '')


def dispatch_workflow(
    github_token: str,
    github_repo: str,
    workflow_id: str,
    ref: str,
    reason: str
) -> bool:
    """Dispatch a new workflow run with a reason message."""
    url = f'https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_id}/dispatches'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json'
    }
    payload = {
        'ref': ref,
        'inputs': {
            'spot_recovery_reason': reason
        }
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 204:
                logger.info("Successfully dispatched workflow %s", workflow_id)
                return True
            logger.warning("Unexpected response status %s for dispatch", response.status)
    except urllib.error.HTTPError as e:
        logger.error("Failed to dispatch workflow: HTTP %s - %s", e.code, e.reason)
    except urllib.error.URLError as e:
        logger.error("Failed to dispatch workflow: %s", e)
    return False


def recover_from_spot_interruption(
    github_token: str,
    github_repo: str,
    run_id: str,
    instance_id: str
) -> dict:
    """
    Handle spot interruption recovery:
    1. Cancel the workflow
    2. Add annotation explaining why
    3. Wait for completion
    4. Dispatch new workflow
    """
    workflow_id, head_sha = get_workflow_info_from_run(
        github_token, github_repo, run_id
    )
    if not workflow_id:
        logger.error("Failed to get workflow info for run %s", run_id)
        return {'statusCode': 500, 'body': 'Failed to get workflow info'}

    if not cancel_workflow_run(github_token, github_repo, run_id):
        logger.error("Failed to cancel workflow run %s", run_id)
        return {'statusCode': 500, 'body': 'Failed to cancel workflow'}

    reason = (
        f"EC2 Spot Instance {instance_id} received interruption warning. "
        f"AWS is reclaiming spot capacity. Workflow cancelled and will be "
        f"automatically re-triggered."
    )
    create_check_run_annotation(
        github_token, github_repo, head_sha,
        "Spot Instance Interruption",
        reason
    )

    wait_for_workflow_completion(github_token, github_repo, run_id)

    recovery_reason = f"Auto-recovery from spot interruption of instance {instance_id}"
    if dispatch_workflow(
        github_token, github_repo, workflow_id, "main", recovery_reason
    ):
        logger.info("Successfully dispatched recovery workflow for %s", workflow_id)
        return {'statusCode': 200, 'body': 'Recovery workflow dispatched'}

    logger.error("Failed to dispatch recovery workflow")
    return {'statusCode': 500, 'body': 'Failed to dispatch recovery workflow'}


def _is_spot_interruption(stop_code: str, stopped_reason: str) -> bool:
    """Check if the task stop was due to spot interruption."""
    return 'SpotInterruption' in stop_code or 'capacity' in stopped_reason.lower()


def _trigger_ecs_recovery(github_repo: str, run_id: str, task_arn: str) -> dict:
    """Trigger recovery for an ECS spot interruption."""
    github_token = get_github_token()
    if not github_token:
        logger.error("No GitHub token available")
        return {'statusCode': 500, 'body': 'No GitHub token'}
    workflow_status = get_workflow_run_status(github_token, github_repo, run_id)
    if workflow_status not in ['queued', 'in_progress', 'waiting']:
        logger.info("Workflow %s not active (status=%s), skipping", run_id, workflow_status)
        return {'statusCode': 200, 'body': f'Workflow not active: {workflow_status}'}
    logger.info("Initiating ECS spot recovery for run_id=%s", run_id)
    return recover_from_ecs_spot_interruption(
        github_token, github_repo, run_id, task_arn
    )


def recover_from_ecs_spot_interruption(
    github_token: str,
    github_repo: str,
    run_id: str,
    task_arn: str
) -> dict:
    """
    Handle ECS spot interruption recovery:
    1. Cancel the workflow
    2. Add annotation explaining why
    3. Wait for completion
    4. Dispatch new workflow
    """
    workflow_id, head_sha = get_workflow_info_from_run(
        github_token, github_repo, run_id
    )
    if not workflow_id:
        logger.error("Failed to get workflow info for run %s", run_id)
        return {'statusCode': 500, 'body': 'Failed to get workflow info'}

    if not cancel_workflow_run(github_token, github_repo, run_id):
        logger.error("Failed to cancel workflow run %s", run_id)
        return {'statusCode': 500, 'body': 'Failed to cancel workflow'}

    task_id = task_arn.split('/')[-1] if '/' in task_arn else task_arn
    reason = (
        f"ECS Fargate Spot task {task_id} was interrupted. "
        f"AWS reclaimed spot capacity. Workflow cancelled and will be "
        f"automatically re-triggered."
    )
    create_check_run_annotation(
        github_token, github_repo, head_sha,
        "ECS Spot Interruption",
        reason
    )

    wait_for_workflow_completion(github_token, github_repo, run_id)

    recovery_reason = f"Auto-recovery from ECS spot interruption of task {task_id}"
    if dispatch_workflow(
        github_token, github_repo, workflow_id, "main", recovery_reason
    ):
        logger.info("Successfully dispatched recovery workflow for %s", workflow_id)
        return {'statusCode': 200, 'body': 'Recovery workflow dispatched'}

    logger.error("Failed to dispatch recovery workflow")
    return {'statusCode': 500, 'body': 'Failed to dispatch recovery workflow'}


def handle_ecs_task_stopped(event: dict) -> dict:
    """Handle ECS task stopped event for spot interruption."""
    detail = event.get('detail', {})
    stop_code = detail.get('stopCode', '')
    stopped_reason = detail.get('stoppedReason', '')
    task_arn = detail.get('taskArn', '')
    tag_dict = _get_ecs_task_tags(task_arn)
    run_id = tag_dict.get('RunId', '')
    github_repo = tag_dict.get('GitHubRepo', '')
    logger.info(
        "ECS task stopped: arn=%s, stopCode=%s, reason=%s, run_id=%s",
        task_arn, stop_code, stopped_reason, run_id
    )
    if not run_id:
        logger.info("No run_id in task tags, skipping")
        return {'statusCode': 200, 'body': 'No run_id'}
    if not _is_spot_interruption(stop_code, stopped_reason):
        logger.info("Not a spot interruption, skipping recovery")
        return {'statusCode': 200, 'body': 'Not a spot interruption'}
    return _trigger_ecs_recovery(github_repo, run_id, task_arn)


def _get_ecs_task_tags(task_arn: str) -> dict:
    """Get tags from an ECS task."""
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
    """Get tags from an EC2 instance."""
    tag_dict: dict = {}
    try:
        response = boto3.client('ec2').describe_instances(InstanceIds=[instance_id])
        tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
        tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    except (ClientError, IndexError, KeyError) as e:
        logger.error("Failed to get instance tags: %s", e)
    return tag_dict


def handle_ec2_spot_interruption(event: dict) -> dict:
    """Handle EC2 spot interruption warning event."""
    instance_id = event.get('detail', {}).get('instance-id', '')
    logger.info("EC2 spot interruption warning for instance: %s", instance_id)
    result: dict = {'statusCode': 500, 'body': 'Failed to get instance tags'}
    tag_dict = _get_ec2_instance_tags(instance_id)
    if tag_dict:
        run_id = tag_dict.get('RunId', '')
        github_repo = tag_dict.get('GitHubRepo', '')
        if not run_id:
            logger.info("No run_id in instance tags, skipping")
            result = {'statusCode': 200, 'body': 'No run_id'}
        else:
            github_token = get_github_token()
            if not github_token:
                logger.error("No GitHub token available")
                result = {'statusCode': 500, 'body': 'No GitHub token'}
            else:
                workflow_status = get_workflow_run_status(github_token, github_repo, run_id)
                if workflow_status not in ['queued', 'in_progress', 'waiting']:
                    logger.info(
                        "Workflow %s not active (status=%s), skipping",
                        run_id, workflow_status
                    )
                    body = f'Workflow not active: {workflow_status}'
                    result = {'statusCode': 200, 'body': body}
                else:
                    logger.info(
                        "Initiating spot interruption recovery for run_id=%s", run_id
                    )
                    result = recover_from_spot_interruption(
                        github_token, github_repo, run_id, instance_id
                    )
    return result


def lambda_handler(event, _context):
    """Main Lambda handler for spot interruption events."""
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
