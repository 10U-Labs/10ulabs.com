import hashlib
import hmac
import json
import logging
import os
import urllib.request
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secretsmanager = boto3.client('secretsmanager')

_webhook_secret_cache = None


def get_webhook_secret() -> str:
    global _webhook_secret_cache
    if _webhook_secret_cache:
        return _webhook_secret_cache

    secret_name = os.environ.get('WEBHOOK_SECRET_NAME', 'api-webhook-secret')
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        _webhook_secret_cache = response['SecretString']
        return _webhook_secret_cache
    except Exception as e:
        logger.error(f"Failed to retrieve webhook secret: {e}")
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


def route_runner_request(job_id: int, job_labels: list, github_repo: str) -> dict:
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
        logger.error(f"No matching runner type for labels: {job_labels}")
        return {
            'success': False,
            'error': f'No matching runner type for labels: {job_labels}'
        }

    payload = {
        'job_id': job_id,
        'job_labels': job_labels,
        'github_repo': github_repo
    }

    logger.info(f"Routing job {job_id} to {runner_type} runner: {endpoint}")

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read())
            logger.info(f"✅ Successfully routed job {job_id} to {runner_type} runner")
            return {
                'success': True,
                'runner_type': runner_type,
                'response': response_data
            }
    except Exception as e:
        logger.error(f"❌ Failed to route job {job_id} to {runner_type} runner: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def handle_workflow_job(event_data: dict) -> dict:
    action = event_data.get('action')
    job = event_data.get('workflow_job', {})
    job_id = job.get('id')
    job_name = job.get('name')
    job_labels = job.get('labels', [])
    job_status = job.get('status')
    repo_full_name = event_data.get('repository', {}).get('full_name')

    logger.info(f"Received workflow_job event: action={action}, job={job_name}, status={job_status}, labels={job_labels}, repo={repo_full_name}")

    if action != 'queued':
        logger.info(f"Ignoring action '{action}' (only handle 'queued')")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"Ignored action: {action}"})
        }

    is_ec2_runner = 'ephemeral-ec2-spot-instance' in job_labels
    is_fargate_runner = 'ephemeral-ecs-fargate-spot' in job_labels

    if not (is_ec2_runner or is_fargate_runner):
        logger.info(f"Job labels {job_labels} don't contain EC2 or Fargate runner type labels")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No matching runner type, ignoring'})
        }

    logger.info(f"🚀 Routing runner request for job {job_id} ({job_name})")

    result = route_runner_request(job_id, job_labels, repo_full_name)

    if result['success']:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Runner launched successfully',
                'runner_type': result['runner_type'],
                'job_id': job_id,
                'response': result['response']
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to launch runner',
                'error': result['error'],
                'job_id': job_id
            })
        }


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        import urllib.parse
        import base64

        body_str = event.get('body', '')
        if event.get('isBase64Encoded'):
            body_str = base64.b64decode(body_str).decode('utf-8')

        if body_str.startswith('payload='):
            payload_json = urllib.parse.unquote(body_str[8:])
            payload = json.loads(payload_json)
        else:
            payload = json.loads(body_str)
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        logger.error(f"Body content (first 500 chars): {str(event.get('body', ''))[:500]}")
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
    logger.info(f"GitHub event type: {event_type}")

    if event_type == 'workflow_job':
        return handle_workflow_job(payload)
    elif event_type == 'ping':
        logger.info("Received ping event")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'pong'})
        }
    else:
        logger.info(f"Ignoring event type: {event_type}")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Event type {event_type} ignored'})
        }
