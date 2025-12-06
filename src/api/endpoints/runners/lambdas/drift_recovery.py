"""Lambda handler for infrastructure drift detection and recovery."""
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
    """Clear cached AWS clients."""
    _clients.clear()


def get_ssm_client():
    """Get or create cached SSM client."""
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_sns_client():
    """Get or create cached SNS client."""
    if 'sns' not in _clients:
        _clients['sns'] = boto3.client('sns')
    return _clients['sns']


def get_ec2_client():
    """Get or create cached EC2 client."""
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def is_resource_in_managed_vpc(resource_id, resource_type):
    """Check if a resource is in the managed VPC."""
    managed_vpc_id = os.environ.get('MANAGED_VPC_ID', '')
    result = True
    if managed_vpc_id:
        ec2 = get_ec2_client()
        try:
            if resource_type == 'AWS::EC2::VPC':
                result = resource_id == managed_vpc_id
            elif resource_type == 'AWS::EC2::Subnet':
                response = ec2.describe_subnets(SubnetIds=[resource_id])
                subnets = response.get('Subnets', [])
                result = subnets[0].get('VpcId') == managed_vpc_id if subnets else False
            elif resource_type == 'AWS::EC2::SecurityGroup':
                response = ec2.describe_security_groups(GroupIds=[resource_id])
                groups = response.get('SecurityGroups', [])
                if groups:
                    group = groups[0]
                    is_default = group.get('GroupName') == 'default'
                    is_in_vpc = group.get('VpcId') == managed_vpc_id
                    result = is_in_vpc and not is_default
                else:
                    result = False
        except ClientError as e:
            logger.warning("Failed to check resource VPC: %s", e)
            result = False
    return result


def get_github_token():
    """Retrieve GitHub token from SSM Parameter Store."""
    parameter_name = os.environ['GITHUB_TOKEN_PARAMETER_NAME']
    result = ''
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        result = response['Parameter']['Value']
    except ClientError as e:
        logger.error("Failed to retrieve GitHub token: %s", e)
    return result


def trigger_api_workflow(github_token):
    """Trigger the api.yml workflow to recover infrastructure."""
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
    result: dict = {'success': False, 'error': 'Unknown error'}
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 204:
                result = {'success': True, 'message': 'Workflow triggered'}
            else:
                result = {'success': False, 'error': f'Unexpected status: {response.status}'}
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        logger.error("Failed to trigger workflow: %s", e)
        result = {'success': False, 'error': str(e)}
    return result


def send_notification(subject, message):
    """Send an SNS notification."""
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    if not sns_topic_arn:
        logger.warning("SNS_TOPIC_ARN not configured, skipping notification")
    else:
        try:
            get_sns_client().publish(TopicArn=sns_topic_arn, Subject=subject, Message=message)
            logger.info("Notification sent: %s", subject)
        except ClientError as e:
            logger.error("Failed to send notification: %s", e)


def extract_event_from_sqs(event):
    """Extract the underlying event from an SQS record."""
    records = event.get('Records', [])
    result = event
    if records:
        body = records[0].get('body', '{}')
        result = json.loads(body)
    return result


def format_drift_details(trigger_event):
    """Extract and format drift details from the trigger event."""
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
    """Main Lambda handler for drift recovery."""
    logger.info("Received SQS event: %s", json.dumps(event))
    trigger_event = extract_event_from_sqs(event)
    drift = format_drift_details(trigger_event)
    logger.info("Drift detected: %s", drift['summary'])
    response: dict = {'statusCode': 200, 'body': 'Resource not in managed VPC, skipping'}
    if not is_resource_in_managed_vpc(drift['resource_id'], drift['resource_type']):
        logger.info("Resource %s is not in managed VPC, skipping", drift['resource_id'])
    else:
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
            response = {'statusCode': 500, 'body': error_msg}
        else:
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
                response = {'statusCode': 200, 'body': 'Recovery workflow triggered'}
            else:
                logger.error("Failed to trigger workflow: %s", result.get('error'))
                send_notification(
                    f"Drift Recovery FAILED: {drift['rule_name']}",
                    f"Infrastructure drift was detected.\n\n"
                    f"Resource: {drift['summary']}\n"
                    f"Rule: {drift['rule_name']}\n\n"
                    f"FAILED to trigger recovery workflow: {result.get('error')}\n\n"
                    f"MANUAL INTERVENTION REQUIRED"
                )
                response = {'statusCode': 500, 'body': 'Failed to trigger recovery'}
    return response
