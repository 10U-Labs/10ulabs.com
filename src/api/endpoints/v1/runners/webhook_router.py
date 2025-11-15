import base64
import hashlib
import hmac
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secretsmanager = boto3.client('secretsmanager')

_webhook_secret_cache = {'value': None}


def get_webhook_secret() -> str:
    if _webhook_secret_cache['value']:
        return _webhook_secret_cache['value']

    secret_name = os.environ.get('WEBHOOK_SECRET_NAME', 'api-webhook-secret')
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']
        _webhook_secret_cache['value'] = secret
        return secret
    except ClientError as e:
        logger.error("Failed to retrieve webhook secret: %s", e)
        return ''


def verify_signature(payload_body: str, signature_header: str, secret: str) -> bool:
    if not signature_header:
        return False
    _, github_signature = signature_header.split('=')
    computed_signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_body.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_signature, github_signature)


def route_runner_request(job_id: int, job_labels: List[str], github_repo: str) -> Dict[str, Any]:
    api_base_url = os.environ.get('API_BASE_URL', 'https://api.10ulabs.com')

    is_ec2_runner = 'ephemeral-ec2-spot-instance' in job_labels
    is_fargate_runner = 'ephemeral-ecs-fargate-spot' in job_labels

    if is_ec2_runner:
        endpoint = f"{api_base_url}/v1/ec2-runner"
        runner_type = "ec2"
    elif is_fargate_runner:
        endpoint = f"{api_base_url}/v1/docker-runner"
        runner_type = "fargate"
    else:
        logger.error("No matching runner type for labels: %s", job_labels)
        return {
            'success': False,
            'error': f'No matching runner type for labels: {job_labels}'
        }

    payload = {
        'job_id': job_id,
        'job_labels': job_labels,
        'github_repo': github_repo
    }

    logger.info("Routing job %s to %s runner: %s", job_id, runner_type, endpoint)

    result = {'success': False, 'error': 'Unknown error'}

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read())
            logger.info("✅ Successfully routed job %s to %s runner", job_id, runner_type)
            result = {
                'success': True,
                'runner_type': runner_type,
                'response': response_data
            }
    except (urllib.error.URLError, ValueError) as e:
        logger.error("❌ Failed to route job %s to %s runner: %s", job_id, runner_type, e)
        result = {
            'success': False,
            'error': str(e)
        }

    return result


def handle_workflow_job(event_data: Dict[str, Any]) -> Dict[str, Any]:
    action = event_data.get('action')
    job = event_data.get('workflow_job', {})
    job_id = job.get('id')
    job_name = job.get('name')
    job_labels = job.get('labels', [])
    job_status = job.get('status')
    repo_full_name = event_data.get('repository', {}).get('full_name')

    logger.info("Received workflow_job event: action=%s, job=%s, status=%s, labels=%s, repo=%s",
               action, job_name, job_status, job_labels, repo_full_name)

    if action != 'queued':
        logger.info("Ignoring action '%s' (only handle 'queued')", action)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"Ignored action: {action}"})
        }

    is_ec2_runner = 'ephemeral-ec2-spot-instance' in job_labels
    is_fargate_runner = 'ephemeral-ecs-fargate-spot' in job_labels

    if not (is_ec2_runner or is_fargate_runner):
        logger.info("Job labels %s don't contain EC2 or Fargate runner type labels", job_labels)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No matching runner type, ignoring'})
        }

    logger.info("🚀 Routing runner request for job %s (%s)", job_id, job_name)

    result = route_runner_request(job_id, job_labels, repo_full_name)

    if result['success']:
        status_code = 200
        response_body = {
            'message': 'Runner launched successfully',
            'runner_type': result['runner_type'],
            'job_id': job_id,
            'response': result['response']
        }
    else:
        status_code = 500
        response_body = {
            'message': 'Failed to launch runner',
            'error': result['error'],
            'job_id': job_id
        }

    return {
        'statusCode': status_code,
        'body': json.dumps(response_body)
    }


def lambda_handler(event, _context):
    logger.info("Received event: %s", json.dumps(event))

    try:
        body_str = event.get('body', '')
        if event.get('isBase64Encoded'):
            body_str = base64.b64decode(body_str).decode('utf-8')

        if body_str.startswith('payload='):
            payload_json = urllib.parse.unquote(body_str[8:])
            payload = json.loads(payload_json)
        else:
            payload = json.loads(body_str)
    except (ValueError, KeyError) as e:
        logger.error("Failed to parse request body: %s", e)
        logger.error("Body content (first 500 chars): %s", str(event.get('body', ''))[:500])
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON payload'})
        }

    signature_header = event.get('headers', {}).get('x-hub-signature-256')
    if signature_header:
        webhook_secret = get_webhook_secret()
        if webhook_secret and not verify_signature(body_str, signature_header, webhook_secret):
            logger.error("Webhook signature verification failed")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid signature'})
            }
    else:
        logger.warning("No signature header found, proceeding without verification")

    event_type = event.get('headers', {}).get('x-github-event', payload.get('event_type'))
    logger.info("GitHub event type: %s", event_type)

    if event_type == 'workflow_job':
        return handle_workflow_job(payload)

    if event_type == 'ping':
        logger.info("Received ping event")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'pong'})
        }

    logger.info("Ignoring event type: %s", event_type)
    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'Event type {event_type} ignored'})
    }
