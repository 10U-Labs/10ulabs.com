"""Lambda handler for GitHub webhook routing to runner endpoints."""
import base64
import datetime
import hashlib
import hmac
import importlib
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Tuple

import boto3
from botocore.exceptions import ClientError

# Add lib directory to path for runner_labels import (needed at Lambda runtime)
_lib_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib', 'python')
if _lib_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_lib_path))

_runner_labels = importlib.import_module('runner_labels')
parse_labels = _runner_labels.parse_labels
validate_labels = _runner_labels.validate_labels
LabelParseError = _runner_labels.LabelParseError
LabelValidationError = _runner_labels.LabelValidationError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

clients = {'ssm': None, 'dynamodb': None, 'sqs': None, 'cloudwatch': None, 'ecs': None, 'ec2': None}
webhook_secret_cache = {'value': None}
api_key_cache = {'value': None}
circuit_breaker_state: Dict[str, Any] = {
    'failures': 0,
    'last_failure_time': 0.0,
    'state': 'closed'
}


def get_ssm_client():
    """Get or create cached SSM client."""
    if clients['ssm'] is None:
        clients['ssm'] = boto3.client('ssm')
    return clients['ssm']


def get_dynamodb_client():
    """Get or create cached DynamoDB client."""
    if clients['dynamodb'] is None:
        clients['dynamodb'] = boto3.client('dynamodb')
    return clients['dynamodb']


def get_sqs_client():
    """Get or create cached SQS client."""
    if clients['sqs'] is None:
        clients['sqs'] = boto3.client('sqs')
    return clients['sqs']


def get_cloudwatch_client():
    """Get or create cached CloudWatch client."""
    if clients['cloudwatch'] is None:
        clients['cloudwatch'] = boto3.client('cloudwatch')
    return clients['cloudwatch']


def get_ecs_client():
    """Get or create cached ECS client."""
    if clients['ecs'] is None:
        clients['ecs'] = boto3.client('ecs')
    return clients['ecs']


def get_ec2_client():
    """Get or create cached EC2 client."""
    if clients['ec2'] is None:
        clients['ec2'] = boto3.client('ec2')
    return clients['ec2']


github_token_cache = {'value': None}


def get_github_token() -> str:
    """Get GitHub token from SSM Parameter Store with caching."""
    if github_token_cache['value']:
        return github_token_cache['value']
    parameter_name = os.environ.get('GITHUB_TOKEN_SECRET_NAME')
    if not parameter_name:
        return ''
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        token = response['Parameter']['Value']
        github_token_cache['value'] = token
        return token
    except ClientError as e:
        logger.error("Failed to retrieve GitHub token: %s", e)
        return ''


test_mode_enabled = {'value': False}


def set_test_mode(enabled: bool):
    """Enable or disable test mode."""
    test_mode_enabled['value'] = enabled


def publish_metric(metric_name: str, value: float, unit: str = 'None'):
    """Publish a metric to CloudWatch."""
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
    """Check if request is duplicate and record for idempotency."""
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
    """Check if circuit breaker allows request processing."""
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
        failure_count = circuit_breaker_state['failures']
        logger.warning("Circuit breaker opening due to %d failures", failure_count)
        circuit_breaker_state['state'] = 'open'
        circuit_breaker_state['last_failure_time'] = current_time
        publish_metric('CircuitBreakerState', 2.0, 'Count')
        return False

    publish_metric('CircuitBreakerState', 0.0, 'Count')
    return True


def record_circuit_breaker_success():
    """Record successful request for circuit breaker."""
    if circuit_breaker_state['state'] == 'half-open':
        logger.info("Circuit breaker closing after successful request")
        circuit_breaker_state['state'] = 'closed'
    circuit_breaker_state['failures'] = 0


def record_circuit_breaker_failure():
    """Record failed request for circuit breaker tracking."""
    circuit_breaker_state['failures'] += 1
    circuit_breaker_state['last_failure_time'] = time.time()
    if circuit_breaker_state['state'] == 'half-open':
        logger.warning("Circuit breaker reopening after failed request in half-open state")
        circuit_breaker_state['state'] = 'open'


def should_record_circuit_breaker_failure(status_code: int | None) -> bool:
    """Determine if status code should be recorded as circuit breaker failure."""
    if status_code is None:
        return True
    if status_code == 503:
        return False
    if 500 <= status_code < 600:
        return True
    return False


def enqueue_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enqueue job to SQS for async processing."""
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


def get_workflow_runners(run_id: str) -> List[Dict[str, Any]]:
    """Get all runners associated with a workflow run from DynamoDB."""
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if not table_name:
        return []
    try:
        dynamodb = get_dynamodb_client()
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='run_id = :rid',
            ExpressionAttributeValues={':rid': {'S': str(run_id)}}
        )
        runners = []
        for item in response.get('Items', []):
            runners.append({
                'run_id': item['run_id']['S'],
                'runner_type': item['runner_type']['S'],
                'resource_id': item['resource_id']['S'],
                'runner_name': item.get('runner_name', {}).get('S', ''),
                'github_repo': item.get('github_repo', {}).get('S', '')
            })
        return runners
    except ClientError as e:
        logger.error("Failed to get workflow runners: %s", e)
        return []


def delete_workflow_runner(run_id: str, runner_type: str) -> bool:
    """Delete workflow runner record from DynamoDB."""
    table_name = os.environ.get('WORKFLOW_RUNNERS_TABLE')
    if not table_name:
        return False
    try:
        dynamodb = get_dynamodb_client()
        dynamodb.delete_item(
            TableName=table_name,
            Key={
                'run_id': {'S': str(run_id)},
                'runner_type': {'S': runner_type}
            }
        )
        return True
    except ClientError as e:
        logger.error("Failed to delete workflow runner: %s", e)
        return False


def delete_github_runner(github_token: str, github_repo: str, runner_name: str) -> bool:
    """Delete runner from GitHub Actions via API."""
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
                logger.info("Runner %s not found in GitHub", runner_name)
                return True
        delete_req = urllib.request.Request(
            f'https://api.github.com/repos/{github_repo}/actions/runners/{runner_id}',
            method='DELETE',
            headers=headers
        )
        with urllib.request.urlopen(delete_req, timeout=10):
            logger.info("Deleted GitHub runner %s (id=%s)", runner_name, runner_id)
            return True
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return True
        logger.error("Failed to delete GitHub runner %s: %s", runner_name, e)
        return False
    except (urllib.error.URLError, ValueError) as e:
        logger.error("Failed to delete GitHub runner %s: %s", runner_name, e)
        return False


def terminate_ecs_task(task_arn: str) -> bool:
    """Stop an ECS task by ARN."""
    cluster = os.environ.get('ECS_CLUSTER')
    if not cluster:
        return False
    try:
        get_ecs_client().stop_task(cluster=cluster, task=task_arn, reason='Workflow completed')
        logger.info("Stopped ECS task: %s", task_arn)
        return True
    except ClientError as e:
        logger.error("Failed to stop ECS task %s: %s", task_arn, e)
        return False


def terminate_ec2_instance(instance_id: str) -> bool:
    """Terminate an EC2 instance by ID."""
    try:
        get_ec2_client().terminate_instances(InstanceIds=[instance_id])
        logger.info("Terminated EC2 instance: %s", instance_id)
        return True
    except ClientError as e:
        logger.error("Failed to terminate EC2 instance %s: %s", instance_id, e)
        return False


def terminate_runners_for_workflow(run_id: str) -> Dict[str, Any]:
    """Terminate all runners for a completed workflow run."""
    runners = get_workflow_runners(run_id)
    if not runners:
        logger.info("No runners found for workflow run %s", run_id)
        return {'terminated': 0, 'failed': 0}
    github_token = get_github_token()
    terminated_count = 0
    failed_count = 0
    for runner in runners:
        runner_type = runner['runner_type']
        resource_id = runner['resource_id']
        runner_name = runner.get('runner_name', '')
        github_repo = runner.get('github_repo', '')
        success = False
        if runner_type.startswith('ec2'):
            success = terminate_ec2_instance(resource_id)
        elif runner_type.startswith('fargate'):
            success = terminate_ecs_task(resource_id)
        if success:
            terminated_count += 1
            delete_workflow_runner(run_id, runner_type)
            if github_token and runner_name and github_repo:
                delete_github_runner(github_token, github_repo, runner_name)
        else:
            failed_count += 1
    result = {'terminated': terminated_count, 'failed': failed_count}
    logger.info("Terminated runners for workflow %s: %s", run_id, result)
    return result


def handle_workflow_run(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workflow_run webhook events and cleanup runners."""
    action = event_data.get('action')
    workflow_run = event_data.get('workflow_run', {})
    run_id = workflow_run.get('id')
    workflow_name = workflow_run.get('name')
    conclusion = workflow_run.get('conclusion')
    logger.info("Received workflow_run event: action=%s, run_id=%s, workflow=%s, conclusion=%s",
                action, run_id, workflow_name, conclusion)
    if action != 'completed':
        logger.info("Ignoring action '%s' (only handle 'completed')", action)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"Ignored action: {action}"})
        }
    result = terminate_runners_for_workflow(str(run_id))
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Workflow run completed, runners terminated',
            'run_id': run_id,
            'terminated': result['terminated'],
            'failed': result['failed']
        })
    }


def get_webhook_secret(force_refresh: bool = False) -> str:
    """Get GitHub webhook secret from SSM with caching."""
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
    """Get API key from SSM with caching."""
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
    """Verify GitHub webhook HMAC-SHA256 signature."""
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


def make_http_request_with_retry(
    endpoint: str,
    payload: dict,
    headers: dict | None = None,
    max_retries: int = 3
) -> tuple:
    """Make HTTP POST request with exponential backoff retry."""
    base_delay = 1.0
    last_status_code = None
    if headers is None:
        headers = {}
    headers['Content-Type'] = 'application/json'
    for attempt in range(max_retries + 1):
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                endpoint, data=data, headers=headers, method='POST'
            )
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


def get_runner_type_from_labels(
    job_labels: List[str]
) -> Tuple[str | None, str | None]:
    """Determine runner type and endpoint from job labels.

    Supports both new composable label format (ecs/ec2 + compute + pricing)
    and legacy labels from environment variables for backwards compatibility.
    """
    runner_type: str | None = None
    endpoint_suffix: str | None = None

    # Try new label format first
    try:
        parsed = parse_labels(job_labels)
        validate_labels(parsed)
        is_e2e = 'e2e' in job_labels
        if parsed.platform == 'ec2':
            runner_type = 'ec2-e2e' if is_e2e else 'ec2'
            endpoint_suffix = 'ec2-runner'
        elif parsed.platform == 'ecs':
            runner_type = 'fargate-e2e' if is_e2e else 'fargate'
            endpoint_suffix = 'ecs-runner'
    except (LabelParseError, LabelValidationError):
        # Fall through to legacy label check
        pass

    # Legacy label format for backwards compatibility (if new format didn't match)
    if not runner_type:
        runner_label_ec2 = os.environ.get('RUNNER_LABEL_EC2')
        runner_label_ec2_e2e = os.environ.get('RUNNER_LABEL_EC2_E2E')
        runner_label_fargate = os.environ.get('RUNNER_LABEL_FARGATE')
        runner_label_fargate_e2e = os.environ.get('RUNNER_LABEL_FARGATE_E2E')
        is_ec2 = runner_label_ec2 in job_labels or runner_label_ec2_e2e in job_labels
        is_fargate = runner_label_fargate in job_labels or runner_label_fargate_e2e in job_labels
        is_e2e = runner_label_ec2_e2e in job_labels or runner_label_fargate_e2e in job_labels
        if is_ec2:
            runner_type = 'ec2-e2e' if is_e2e else 'ec2'
            endpoint_suffix = 'ec2-runner'
        elif is_fargate:
            runner_type = 'fargate-e2e' if is_e2e else 'fargate'
            endpoint_suffix = 'ecs-runner'

    return (runner_type, endpoint_suffix)


def _build_runner_endpoint(endpoint_suffix: str) -> str:
    """Build full runner API endpoint URL."""
    return f"{os.environ['API_BASE_URL']}/v1/{endpoint_suffix}"


def _handle_route_success(
    job_id: int,
    runner_type: str,
    response_data: Any
) -> Dict[str, Any]:
    """Handle successful runner request routing."""
    logger.info("Successfully routed job %s to %s runner", job_id, runner_type)
    record_circuit_breaker_success()
    return {'success': True, 'runner_type': runner_type, 'response': response_data}


def _handle_route_failure(
    job_id: int,
    error: str,
    status_code: int | None
) -> Dict[str, Any]:
    """Handle failed runner request routing."""
    logger.error("Failed to route job %s: %s", job_id, error)
    if should_record_circuit_breaker_failure(status_code):
        record_circuit_breaker_failure()
    else:
        logger.warning(
            "Status %s for job %s - not counting as circuit breaker failure",
            status_code, job_id
        )
    return {'success': False, 'error': error}


def route_runner_request(
    job_id: int,
    job_labels: List[str],
    github_repo: str,
    run_id: int | None = None
) -> Dict[str, Any]:
    """Route runner request to appropriate EC2 or ECS endpoint."""
    if not check_circuit_breaker():
        logger.error("Circuit breaker is open, rejecting request for job %s", job_id)
        return {'success': False, 'error': 'Service temporarily unavailable (circuit breaker open)'}
    runner_type, endpoint_suffix = get_runner_type_from_labels(job_labels)
    if not runner_type or not endpoint_suffix:
        logger.error("No matching runner type for labels: %s", job_labels)
        return {'success': False, 'error': f'No matching runner type for labels: {job_labels}'}
    try:
        api_key = get_api_key()
    except RuntimeError as e:
        logger.error("Cannot route job %s: %s", job_id, e)
        return {'success': False, 'error': str(e)}
    endpoint = _build_runner_endpoint(endpoint_suffix)
    payload = {
        'job_id': job_id,
        'job_labels': job_labels,
        'github_repo': github_repo,
        'run_id': run_id,
        'runner_type': runner_type
    }
    logger.info(
        "Routing job %s to %s runner: %s (run_id=%s)",
        job_id, runner_type, endpoint, run_id
    )
    success, response_data, error, status_code = make_http_request_with_retry(
        endpoint, payload, {'x-api-key': api_key}
    )
    if success:
        return _handle_route_success(job_id, runner_type, response_data)
    return _handle_route_failure(job_id, error, status_code)


def handle_workflow_job(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workflow_job webhook events and enqueue runner requests."""
    action = event_data.get('action')
    job = event_data.get('workflow_job', {})
    job_id = job.get('id')
    job_name = job.get('name')
    job_labels = job.get('labels', [])
    job_status = job.get('status')
    run_id = job.get('run_id')
    repo_full_name = event_data.get('repository', {}).get('full_name')

    logger.info(
        "Received workflow_job event: action=%s, job=%s, status=%s, labels=%s",
        action, job_name, job_status, job_labels
    )
    logger.info("workflow_job context: repo=%s, run_id=%s", repo_full_name, run_id)

    if action != 'queued':
        logger.info("Ignoring action '%s' (only handle 'queued')", action)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"Ignored action: {action}"})
        }

    runner_type, _ = get_runner_type_from_labels(job_labels)
    if not runner_type:
        logger.info("Job labels %s don't contain EC2 or Fargate runner type labels", job_labels)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No matching runner type, ignoring'})
        }

    logger.info(
        "Enqueueing runner request for job %s (%s), runner_type=%s",
        job_id, job_name, runner_type
    )

    job_data = {
        'job_id': job_id,
        'job_labels': job_labels,
        'github_repo': repo_full_name,
        'run_id': run_id,
        'runner_type': runner_type
    }

    result = enqueue_job(job_data)

    if result['success']:
        status_code = 200
        response_body = {
            'message': 'Job enqueued successfully',
            'job_id': job_id,
            'run_id': run_id,
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
    """Process a single SQS message containing a job request."""
    try:
        body = json.loads(message['body'])
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')
        run_id = body.get('run_id')

        logger.info(
            "Processing job from SQS: job_id=%s, labels=%s, repo=%s, run_id=%s",
            job_id, job_labels, github_repo, run_id
        )

        result = route_runner_request(job_id, job_labels, github_repo, run_id)

        if result['success']:
            logger.info("Successfully processed SQS message for job %s", job_id)
            return {'success': True}

        logger.error("Failed to process SQS message for job %s: %s", job_id, result.get('error'))
        return {'success': False, 'error': result.get('error')}
    except (ValueError, KeyError) as e:
        logger.error("Failed to parse SQS message: %s", e)
        return {'success': False, 'error': f'Invalid message format: {e}'}


def handle_health_check() -> Dict[str, Any]:
    """Return health check status including circuit breaker state."""
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
    """Parse webhook event body handling base64 and form encoding."""
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
    """Verify webhook signature and return error response if invalid."""
    try:
        webhook_secret = get_webhook_secret()
        if not verify_signature(body_str, signature_header, webhook_secret):
            logger.error("Webhook signature verification failed")
            return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid signature'})}
        return {}
    except RuntimeError as e:
        logger.error("Cannot verify signature, secret unavailable: %s", e)
        error_body = json.dumps({'error': 'Authentication system unavailable'})
        return {'statusCode': 500, 'body': error_body}


def get_header_case_insensitive(headers: dict, key: str) -> str | None:
    """Get header value with case-insensitive key matching."""
    lower_key = key.lower()
    for header_name, header_value in headers.items():
        if header_name.lower() == lower_key:
            return header_value
    return None


def handle_api_gateway_event(event: dict, start_time: float) -> dict:
    """Handle API Gateway HTTP events from webhooks."""
    headers = event.get('headers', {})
    set_test_mode(get_header_case_insensitive(headers, 'x-test-mode') == 'true')

    http_context = event.get('requestContext', {}).get('http', {})
    http_method = event.get('httpMethod', http_context.get('method', ''))
    if http_method == 'OPTIONS':
        result = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Headers': (
                    'Content-Type,x-api-key,x-github-event,'
                    'x-hub-signature-256,x-github-delivery'
                )
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
    """Process and route GitHub webhook event to appropriate handler."""
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

    if event_type == 'workflow_run':
        result = handle_workflow_run(payload)
        return result

    if event_type == 'ping':
        logger.info("Received ping event")
    else:
        logger.info("Ignoring event type: %s", event_type)
    message = 'pong' if event_type == 'ping' else f'Event type {event_type} ignored'
    result = {'statusCode': 200, 'body': json.dumps({'message': message})}
    return result


def lambda_handler(event, _context):
    """Main Lambda entry point for webhook and SQS events."""
    start_time = time.time()
    logger.info("Received event: %s", json.dumps(event))

    records = event.get('Records', [])
    is_sqs = records and records[0].get('eventSource') == 'aws:sqs'
    if is_sqs:
        logger.info("Processing SQS event")
        results = [handle_sqs_message(record) for record in event['Records']]
        if not all(r['success'] for r in results):
            raise RuntimeError("One or more SQS messages failed to process")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Processed successfully'})}

    return handle_api_gateway_event(event, start_time)
