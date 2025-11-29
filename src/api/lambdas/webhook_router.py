import base64
import datetime
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

clients = {'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None}
webhook_secret_cache = {'value': None}
api_key_cache = {'value': None}
circuit_breaker_state: Dict[str, Any] = {
    'failures': 0,
    'last_failure_time': 0.0,
    'state': 'closed'
}


def get_ssm_client():
    if clients['ssm'] is None:
        clients['ssm'] = boto3.client('ssm')
    return clients['ssm']


def get_dynamodb_client():
    if clients['dynamodb'] is None:
        clients['dynamodb'] = boto3.client('dynamodb')
    return clients['dynamodb']


def get_sqs_client():
    if clients['sqs'] is None:
        clients['sqs'] = boto3.client('sqs')
    return clients['sqs']


def get_cloudwatch_client():
    if clients['cloudwatch'] is None:
        clients['cloudwatch'] = boto3.client('cloudwatch')
    return clients['cloudwatch']


test_mode_enabled = {'value': False}


def set_test_mode(enabled: bool):
    test_mode_enabled['value'] = enabled


def publish_metric(metric_name: str, value: float, unit: str = 'None'):
    if not test_mode_enabled['value']:
        try:
            cloudwatch = get_cloudwatch_client()
            cloudwatch.put_metric_data(
                Namespace='WebhookRouter',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.datetime.now(datetime.UTC)
                    }
                ]
            )
        except ClientError as e:
            logger.warning("Failed to publish metric %s: %s", metric_name, e)


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


def check_circuit_breaker() -> bool:
    current_time = time.time()
    failure_threshold = 5
    timeout_seconds = 60

    if circuit_breaker_state['state'] == 'open':
        if current_time - circuit_breaker_state['last_failure_time'] > timeout_seconds:
            logger.info("Circuit breaker transitioning to half-open state")
            circuit_breaker_state['state'] = 'half-open'
            circuit_breaker_state['failures'] = 0
            publish_metric('CircuitBreakerState', 1.0, 'Count')
            return True
        publish_metric('CircuitBreakerState', 2.0, 'Count')
        return False

    if circuit_breaker_state['failures'] >= failure_threshold:
        logger.warning("Circuit breaker opening due to %d failures", circuit_breaker_state['failures'])
        circuit_breaker_state['state'] = 'open'
        circuit_breaker_state['last_failure_time'] = current_time
        publish_metric('CircuitBreakerState', 2.0, 'Count')
        return False

    publish_metric('CircuitBreakerState', 0.0, 'Count')
    return True


def record_circuit_breaker_success():
    if circuit_breaker_state['state'] == 'half-open':
        logger.info("Circuit breaker closing after successful request")
        circuit_breaker_state['state'] = 'closed'
    circuit_breaker_state['failures'] = 0


def record_circuit_breaker_failure():
    circuit_breaker_state['failures'] += 1
    circuit_breaker_state['last_failure_time'] = time.time()
    if circuit_breaker_state['state'] == 'half-open':
        logger.warning("Circuit breaker reopening after failed request in half-open state")
        circuit_breaker_state['state'] = 'open'


def should_record_circuit_breaker_failure(status_code: int) -> bool:
    if status_code is None:
        return True
    if status_code == 503:
        return False
    if 500 <= status_code < 600:
        return True
    return False


def enqueue_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    queue_url = os.environ.get('JOB_QUEUE_URL')
    if not queue_url:
        logger.error("JOB_QUEUE_URL not set, cannot enqueue job")
        return {'success': False, 'error': 'Job queue not configured'}

    try:
        sqs = get_sqs_client()
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(job_data)
        )
        logger.info("Enqueued job to SQS: %s", response.get('MessageId'))

        queue_attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        queue_depth = int(queue_attrs['Attributes'].get('ApproximateNumberOfMessages', 0))
        publish_metric('QueueDepth', float(queue_depth), 'Count')

        return {'success': True, 'message_id': response.get('MessageId')}
    except ClientError as e:
        logger.error("Failed to enqueue job: %s", e)
        return {'success': False, 'error': str(e)}


def get_webhook_secret(force_refresh: bool = False) -> str:
    if force_refresh:
        webhook_secret_cache['value'] = None

    secret = webhook_secret_cache['value']
    if not secret:
        parameter_name = os.environ['WEBHOOK_SECRET_NAME']
        try:
            ssm = get_ssm_client()
            response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
            secret = response['Parameter']['Value']
            webhook_secret_cache['value'] = secret
        except ClientError as e:
            logger.error("Failed to retrieve webhook secret: %s", e)
            raise RuntimeError(f"Cannot retrieve webhook secret: {e}") from e
    return secret


def get_api_key(force_refresh: bool = False) -> str:
    if force_refresh:
        api_key_cache['value'] = None

    api_key = api_key_cache['value']
    if not api_key:
        try:
            parameter_name = os.environ['API_KEY_PARAMETER_NAME']
            ssm = get_ssm_client()
            response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
            api_key = response['Parameter']['Value']
            api_key_cache['value'] = api_key
        except ClientError as e:
            logger.error("Failed to retrieve API key: %s", e)
            raise RuntimeError(f"Cannot retrieve API key: {e}") from e
        except KeyError as e:
            logger.error("API_KEY_PARAMETER_NAME environment variable not set")
            raise RuntimeError("API_KEY_PARAMETER_NAME environment variable not set") from e
    return api_key


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


def make_http_request_with_retry(endpoint: str, payload: dict, headers: dict | None = None, max_retries: int = 3) -> tuple:
    base_delay = 1.0
    last_status_code = None
    if headers is None:
        headers = {}
    headers['Content-Type'] = 'application/json'
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as response:
                return (True, json.loads(response.read()), None, response.status)
        except urllib.error.HTTPError as e:
            last_status_code = e.code
            if 400 <= e.code < 500:
                return (False, None, f'HTTP {e.code}: {e.reason}', e.code)
            if attempt >= max_retries:
                return (False, None, f'HTTP {e.code} after {max_retries + 1} attempts', e.code)
            time.sleep(base_delay * (2 ** attempt))
        except (urllib.error.URLError, ValueError) as e:
            if attempt >= max_retries:
                return (False, None, f'{str(e)} after {max_retries + 1} attempts', last_status_code)
            time.sleep(base_delay * (2 ** attempt))
    return (False, None, 'Max retries exceeded', last_status_code)


def route_runner_request(job_id: int, job_labels: List[str], github_repo: str) -> Dict[str, Any]:
    if not check_circuit_breaker():
        logger.error("Circuit breaker is open, rejecting request for job %s", job_id)
        return {'success': False, 'error': 'Service temporarily unavailable (circuit breaker open)'}

    api_base_url = os.environ['API_BASE_URL']
    runner_label_ec2 = os.environ['RUNNER_LABEL_EC2_SPOT']
    runner_label_fargate = os.environ['RUNNER_LABEL_FARGATE_SPOT']
    if runner_label_ec2 in job_labels:
        endpoint, runner_type = f"{api_base_url}/v1/ec2-runner", "ec2"
    elif runner_label_fargate in job_labels:
        endpoint, runner_type = f"{api_base_url}/v1/docker-runner", "fargate"
    else:
        logger.error("No matching runner type for labels: %s", job_labels)
        return {'success': False, 'error': f'No matching runner type for labels: {job_labels}'}

    try:
        api_key = get_api_key()
    except RuntimeError as e:
        logger.error("Cannot route job %s: %s", job_id, e)
        return {'success': False, 'error': str(e)}

    payload = {'job_id': job_id, 'job_labels': job_labels, 'github_repo': github_repo}
    headers = {'x-api-key': api_key}
    logger.info("Routing job %s to %s runner: %s", job_id, runner_type, endpoint)

    success, response_data, error, status_code = make_http_request_with_retry(endpoint, payload, headers)
    if success:
        logger.info("Successfully routed job %s to %s runner", job_id, runner_type)
        record_circuit_breaker_success()
        return {'success': True, 'runner_type': runner_type, 'response': response_data}
    logger.error("Failed to route job %s: %s", job_id, error)
    if should_record_circuit_breaker_failure(status_code):
        record_circuit_breaker_failure()
    else:
        logger.warning("Status %s for job %s - not counting as circuit breaker failure", status_code, job_id)
    return {'success': False, 'error': error}


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

    runner_label_ec2 = os.environ['RUNNER_LABEL_EC2_SPOT']
    runner_label_fargate = os.environ['RUNNER_LABEL_FARGATE_SPOT']
    is_ec2_runner = runner_label_ec2 in job_labels
    is_fargate_runner = runner_label_fargate in job_labels

    if not (is_ec2_runner or is_fargate_runner):
        logger.info("Job labels %s don't contain EC2 or Fargate runner type labels", job_labels)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No matching runner type, ignoring'})
        }

    logger.info("Enqueueing runner request for job %s (%s)", job_id, job_name)

    job_data = {
        'job_id': job_id,
        'job_labels': job_labels,
        'github_repo': repo_full_name
    }

    result = enqueue_job(job_data)

    if result['success']:
        status_code = 200
        response_body = {
            'message': 'Job enqueued successfully',
            'job_id': job_id,
            'message_id': result.get('message_id')
        }
    else:
        status_code = 500
        response_body = {
            'message': 'Failed to enqueue job',
            'error': result['error'],
            'job_id': job_id
        }

    return {
        'statusCode': status_code,
        'body': json.dumps(response_body)
    }


def handle_sqs_message(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = json.loads(message['body'])
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')

        logger.info("Processing job from SQS: job_id=%s, labels=%s, repo=%s", job_id, job_labels, github_repo)

        result = route_runner_request(job_id, job_labels, github_repo)

        if result['success']:
            logger.info("Successfully processed SQS message for job %s", job_id)
            return {'success': True}

        logger.error("Failed to process SQS message for job %s: %s", job_id, result.get('error'))
        return {'success': False, 'error': result.get('error')}
    except (ValueError, KeyError) as e:
        logger.error("Failed to parse SQS message: %s", e)
        return {'success': False, 'error': f'Invalid message format: {e}'}


def handle_health_check() -> Dict[str, Any]:
    health_status = {
        'status': 'healthy',
        'circuit_breaker': circuit_breaker_state['state'],
        'timestamp': int(time.time())
    }
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(health_status)
    }


def parse_event_body(event: dict) -> tuple:
    body_str = event.get('body', '')
    if event.get('isBase64Encoded'):
        body_str = base64.b64decode(body_str).decode('utf-8')
    if body_str.startswith('payload='):
        payload_json = urllib.parse.unquote(body_str[8:])
        payload = json.loads(payload_json)
    else:
        payload = json.loads(body_str)
    return (body_str, payload)


def verify_webhook_signature(body_str: str, signature_header: str) -> dict:
    try:
        webhook_secret = get_webhook_secret()
        if not verify_signature(body_str, signature_header, webhook_secret):
            logger.error("Webhook signature verification failed")
            return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid signature'})}
        return {}
    except RuntimeError as e:
        logger.error("Cannot verify signature, secret unavailable: %s", e)
        return {'statusCode': 500, 'body': json.dumps({'error': 'Authentication system unavailable'})}


def get_header_case_insensitive(headers: dict, key: str) -> str | None:
    lower_key = key.lower()
    for header_name, header_value in headers.items():
        if header_name.lower() == lower_key:
            return header_value
    return None


def handle_api_gateway_event(event: dict, start_time: float) -> dict:
    headers = event.get('headers', {})
    set_test_mode(get_header_case_insensitive(headers, 'x-test-mode') == 'true')

    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
    if http_method == 'OPTIONS':
        result = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-github-event,x-hub-signature-256,x-github-delivery'
            },
            'body': ''
        }
        return result

    path = event.get('path', event.get('rawPath', ''))
    if path == '/v1/runners/health':
        result = handle_health_check()
        return result

    result = _process_webhook_event(event, headers, start_time)
    return result


def _process_webhook_event(event: dict, headers: dict, start_time: float) -> dict:
    try:
        body_str, payload = parse_event_body(event)
    except (ValueError, KeyError) as e:
        logger.error("Failed to parse request body: %s", e)
        logger.error("Body content (first 500 chars): %s", str(event.get('body', ''))[:500])
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON payload'})}

    signature_header = get_header_case_insensitive(headers, 'x-hub-signature-256')
    if signature_header:
        error_response = verify_webhook_signature(body_str, signature_header)
        if error_response:
            return error_response
    else:
        logger.warning("No signature header found, proceeding without verification")

    delivery_id = get_header_case_insensitive(headers, 'x-github-delivery')
    if delivery_id and check_and_record_idempotency(delivery_id):
        logger.info("Duplicate webhook delivery detected, returning success")
        publish_metric('ProcessingTime', (time.time() - start_time) * 1000, 'Milliseconds')
        return {'statusCode': 200, 'body': json.dumps({'message': 'Duplicate request ignored'})}

    event_type = get_header_case_insensitive(headers, 'x-github-event') or payload.get('event_type')
    logger.info("GitHub event type: %s", event_type)
    publish_metric('ProcessingTime', (time.time() - start_time) * 1000, 'Milliseconds')

    if event_type == 'workflow_job':
        result = handle_workflow_job(payload)
        return result

    logger.info("Received ping event" if event_type == 'ping' else f"Ignoring event type: {event_type}")
    message = 'pong' if event_type == 'ping' else f'Event type {event_type} ignored'
    result = {'statusCode': 200, 'body': json.dumps({'message': message})}
    return result


def lambda_handler(event, _context):
    start_time = time.time()
    logger.info("Received event: %s", json.dumps(event))

    if 'Records' in event and len(event['Records']) > 0 and event['Records'][0].get('eventSource') == 'aws:sqs':
        logger.info("Processing SQS event")
        results = [handle_sqs_message(record) for record in event['Records']]
        if not all(r['success'] for r in results):
            raise RuntimeError("One or more SQS messages failed to process")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Processed successfully'})}

    return handle_api_gateway_event(event, start_time)
