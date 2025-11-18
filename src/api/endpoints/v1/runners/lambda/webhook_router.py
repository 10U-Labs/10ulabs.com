import base64
import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {'secretsmanager': None, 'dynamodb': None}
_webhook_secret_cache = {'value': None}


def get_secretsmanager_client():
    if _clients['secretsmanager'] is None:
        _clients['secretsmanager'] = boto3.client('secretsmanager')
    return _clients['secretsmanager']


def get_dynamodb_client():
    if _clients['dynamodb'] is None:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def check_and_record_idempotency(request_id: str) -> bool:
    table_name = os.environ.get('IDEMPOTENCY_TABLE_NAME')
    if not table_name:
        logger.warning("IDEMPOTENCY_TABLE_NAME not set, skipping idempotency check")
        return False

    try:
        dynamodb = get_dynamodb_client()
        ttl = int(time.time()) + 86400

        dynamodb.put_item(
            TableName=table_name,
            Item={
                'request_id': {'S': request_id},
                'ttl': {'N': str(ttl)},
                'timestamp': {'N': str(int(time.time()))}
            },
            ConditionExpression='attribute_not_exists(request_id)'
        )
        return False
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning("Duplicate request detected: %s", request_id)
            return True
        logger.error("Failed to check idempotency: %s", e)
        return False


def get_webhook_secret() -> str:
    secret = _webhook_secret_cache['value']
    if not secret:
        secret_name = os.environ.get('WEBHOOK_SECRET_NAME', 'api-webhook-secret')
        try:
            secretsmanager = get_secretsmanager_client()
            response = secretsmanager.get_secret_value(SecretId=secret_name)
            secret = response['SecretString']
            _webhook_secret_cache['value'] = secret
        except ClientError as e:
            logger.error("Failed to retrieve webhook secret: %s", e)
            raise RuntimeError(f"Cannot retrieve webhook secret: {e}") from e
    return secret


def verify_signature(payload_body: str, signature_header: str, secret: str) -> bool:
    if not signature_header:
        return False
    parts = signature_header.split('=', 1)
    if len(parts) != 2:
        return False
    _, github_signature = parts
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

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read())
                logger.info("Successfully routed job %s to %s runner on attempt %d", job_id, runner_type, attempt + 1)
                return {
                    'success': True,
                    'runner_type': runner_type,
                    'response': response_data
                }
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500:
                logger.error("Client error routing job %s (HTTP %d), not retrying", job_id, e.code)
                return {
                    'success': False,
                    'error': f'HTTP {e.code}: {e.reason}'
                }

            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning("Server error routing job %s (HTTP %d), retry %d/%d after %ds", job_id, e.code, attempt + 1, max_retries, delay)
                time.sleep(delay)
            else:
                logger.error("Failed to route job %s after %d attempts (HTTP %d)", job_id, max_retries + 1, e.code)
                return {
                    'success': False,
                    'error': f'HTTP {e.code} after {max_retries + 1} attempts'
                }
        except (urllib.error.URLError, ValueError) as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning("Error routing job %s, retry %d/%d after %ds: %s", job_id, attempt + 1, max_retries, delay, e)
                time.sleep(delay)
            else:
                logger.error("Failed to route job %s after %d attempts: %s", job_id, max_retries + 1, e)
                return {
                    'success': False,
                    'error': f'{str(e)} after {max_retries + 1} attempts'
                }

    return {'success': False, 'error': 'Max retries exceeded'}


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

    logger.info("Routing runner request for job %s (%s)", job_id, job_name)

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
        try:
            webhook_secret = get_webhook_secret()
            if not verify_signature(body_str, signature_header, webhook_secret):
                logger.error("Webhook signature verification failed")
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': 'Invalid signature'})
                }
        except RuntimeError as e:
            logger.error("Cannot verify signature, secret unavailable: %s", e)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Authentication system unavailable'})
            }
    else:
        logger.warning("No signature header found, proceeding without verification")

    delivery_id = event.get('headers', {}).get('x-github-delivery')
    if delivery_id:
        is_duplicate = check_and_record_idempotency(delivery_id)
        if is_duplicate:
            logger.info("Duplicate webhook delivery detected, returning success")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Duplicate request ignored'})
            }

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
