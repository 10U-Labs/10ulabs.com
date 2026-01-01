"""
Runners router handler for /v1/runners endpoint.

This Lambda routes runner requests to the appropriate endpoint
(/v1/runners/ec2 or /v1/runners/ecs) based on job labels.
"""

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any

import boto3

# Import runner_labels module (bundled as runner_labels.py)
import runner_labels

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
API_BASE_URL = os.environ.get('API_BASE_URL', '')
API_KEY_PARAMETER_NAME = os.environ.get('API_KEY_PARAMETER_NAME', '')

# Cache for API key
_api_key_cache: dict[str, str] = {}


def _get_api_key() -> str:
    """Get API key from SSM Parameter Store (cached)."""
    if 'api_key' in _api_key_cache:
        return _api_key_cache['api_key']

    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=API_KEY_PARAMETER_NAME, WithDecryption=True)
    api_key = response['Parameter']['Value']
    _api_key_cache['api_key'] = api_key
    return api_key


def _route_to_runner(
    endpoint_suffix: str,
    payload: dict[str, Any]
) -> dict[str, Any]:
    """Route request to the appropriate runner endpoint via HTTP POST."""
    url = f"{API_BASE_URL}/v1/runners/{endpoint_suffix}"
    api_key = _get_api_key()

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
    }

    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(url, data=data, headers=headers, method='POST')

    logger.info("Routing to %s", url)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode('utf-8')
            return {
                'statusCode': response.status,
                'body': response_body,
            }
    except urllib.error.HTTPError as exc:
        logger.error("HTTP error routing to %s: %s", url, exc)
        return {
            'statusCode': exc.code,
            'body': exc.read().decode('utf-8') if exc.fp else str(exc),
        }
    except urllib.error.URLError as exc:
        logger.error("URL error routing to %s: %s", url, exc)
        raise


def _process_runner_request(message_body: dict[str, Any]) -> dict[str, Any]:
    """Process a runner request and route to appropriate endpoint."""
    job_labels = message_body.get('job_labels', [])
    job_id = message_body.get('job_id')
    run_id = message_body.get('run_id')
    github_repo = message_body.get('github_repo')

    logger.info(
        "Processing runner request: job_id=%s, run_id=%s, labels=%s",
        job_id, run_id, job_labels
    )

    # Determine runner type from labels
    runner_type, endpoint_suffix = runner_labels.get_runner_type_from_labels(job_labels)

    if not runner_type or not endpoint_suffix:
        logger.warning("No matching runner type for labels: %s", job_labels)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'No matching runner type',
                'job_id': job_id,
                'labels': job_labels,
            }),
        }

    logger.info(
        "Determined runner_type=%s, endpoint=%s for job_id=%s",
        runner_type, endpoint_suffix, job_id
    )

    # Build payload for runner endpoint
    payload = {
        'job_id': job_id,
        'job_labels': job_labels,
        'github_repo': github_repo,
        'run_id': run_id,
        'runner_type': runner_type,
    }

    # Route to appropriate endpoint
    return _route_to_runner(endpoint_suffix, payload)


def _handle_sqs_event(event: dict[str, Any]) -> dict[str, Any]:
    """Handle SQS event containing runner request(s)."""
    records = event.get('Records', [])
    results = []

    for record in records:
        try:
            body = json.loads(record.get('body', '{}'))
            result = _process_runner_request(body)
            results.append({
                'messageId': record.get('messageId'),
                'result': result,
            })
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Error processing SQS record: %s", exc)
            results.append({
                'messageId': record.get('messageId'),
                'error': str(exc),
            })

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processed SQS records',
            'results': results,
        }),
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """
    Main Lambda handler.

    Handles SQS events from the runners queue.
    Routes requests to /v1/runners/ec2 or /v1/runners/ecs based on labels.
    """
    logger.info("Received event: %s", json.dumps(event))

    # Check if this is an SQS event
    if 'Records' in event and event['Records']:
        first_record = event['Records'][0]
        if first_record.get('eventSource') == 'aws:sqs':
            return _handle_sqs_event(event)

    # Direct invocation (for testing)
    logger.warning("Unexpected event format, expected SQS event")
    return {
        'statusCode': 400,
        'body': json.dumps({
            'error': 'Expected SQS event',
        }),
    }
