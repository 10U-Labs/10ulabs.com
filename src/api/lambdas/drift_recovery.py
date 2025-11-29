import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients: dict[str, Any] = {}


def clear_clients():
    _clients.clear()


def get_ssm_client():
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_sns_client():
    if 'sns' not in _clients:
        _clients['sns'] = boto3.client('sns')
    return _clients['sns']


def get_github_token():
    parameter_name = os.environ['GITHUB_TOKEN_PARAMETER_NAME']
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        logger.error("Failed to retrieve GitHub token: %s", e)
        return ''


def trigger_api_workflow(github_token):
    github_repo = os.environ['GITHUB_REPO']
    workflow_file = 'api.yml'

    url = f'https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/dispatches'

    payload = {
        'ref': 'main',
        'inputs': {
            'github_hosted': 'true'
        }
    }

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json'
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 204:
                return {'success': True, 'message': 'Workflow triggered'}
            return {'success': False, 'error': f'Unexpected status: {response.status}'}
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        logger.error("Failed to trigger workflow: %s", e)
        return {'success': False, 'error': str(e)}


def send_notification(subject, message):
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    if not sns_topic_arn:
        logger.warning("SNS_TOPIC_ARN not configured, skipping notification")
        return
    try:
        get_sns_client().publish(TopicArn=sns_topic_arn, Subject=subject, Message=message)
        logger.info("Notification sent: %s", subject)
    except ClientError as e:
        logger.error("Failed to send notification: %s", e)


def extract_event_from_sqs(event):
    records = event.get('Records', [])
    if not records:
        return event
    body = records[0].get('body', '{}')
    return json.loads(body)


def format_drift_details(trigger_event):
    rule_name = trigger_event.get('configRuleName', 'Unknown')
    resource_type = trigger_event.get('resourceType', 'Unknown')
    resource_id = trigger_event.get('resourceId', 'Unknown')
    aws_region = trigger_event.get('awsRegion', 'Unknown')

    return {
        'rule_name': rule_name,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'aws_region': aws_region,
        'summary': f"{resource_type} ({resource_id}) in {aws_region}"
    }


def lambda_handler(event, _context):
    logger.info("Received SQS event: %s", json.dumps(event))

    trigger_event = extract_event_from_sqs(event)
    drift = format_drift_details(trigger_event)

    logger.info("Drift detected: %s", drift['summary'])

    github_repo = os.environ.get('GITHUB_REPO', '')

    github_token = get_github_token()
    if not github_token:
        error_msg = 'Failed to retrieve GitHub token'
        logger.error(error_msg)
        send_notification(
            f"Drift Recovery FAILED: {drift['rule_name']}",
            f"Infrastructure drift was detected.\n\n"
            f"Resource: {drift['summary']}\n"
            f"Rule: {drift['rule_name']}\n\n"
            f"FAILED to trigger recovery workflow: {error_msg}\n\n"
            f"MANUAL INTERVENTION REQUIRED"
        )
        return {'statusCode': 500, 'body': error_msg}

    result = trigger_api_workflow(github_token)

    if result['success']:
        logger.info("Successfully triggered api.yml workflow for drift recovery")
        send_notification(
            f"Drift Recovery Triggered: {drift['rule_name']}",
            f"Infrastructure drift was detected.\n\n"
            f"Resource: {drift['summary']}\n"
            f"Rule: {drift['rule_name']}\n\n"
            f"Automatically triggered api.yml workflow to recover infrastructure.\n\n"
            f"Monitor the workflow at: https://github.com/{github_repo}/actions"
        )
        return {'statusCode': 200, 'body': 'Recovery workflow triggered'}

    logger.error("Failed to trigger workflow: %s", result.get('error'))
    send_notification(
        f"Drift Recovery FAILED: {drift['rule_name']}",
        f"Infrastructure drift was detected.\n\n"
        f"Resource: {drift['summary']}\n"
        f"Rule: {drift['rule_name']}\n\n"
        f"FAILED to trigger recovery workflow: {result.get('error')}\n\n"
        f"MANUAL INTERVENTION REQUIRED"
    )
    return {'statusCode': 500, 'body': 'Failed to trigger recovery'}
