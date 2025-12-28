"""Lambda handler for EC2 runner API endpoint."""
import json
import logging
from typing import Any, Dict

from aws_clients import (
    get_ec2_client,
    get_ssm_client,
    get_dynamodb_client,
    set_client,
    reset_clients,
)
from github_runner_api import (
    build_runner_labels,
    cleanup_offline_runners,
    delete_runner,
    get_existing_runner_for_workflow,
    get_github_token,
    get_runner_registration_token,
    list_repo_runners,
    reset_github_token_cache,
)
from infra_validation import (
    ensure_dependencies_valid,
    get_api_key,
    get_dependencies_status,
    reset_dependency_validation,
    set_dependencies_status,
    validate_all_dependencies,
    validate_security_groups,
    validate_subnets,
    validate_vpc,
)
from lambda_http import (
    error_response,
    is_capacity_error,
    json_response,
    parse_body,
    success_response,
)
from fleet_ops import (
    create_ec2_user_data,
    get_ec2_config,
    get_ec2_runner_status,
    get_latest_ami,
    launch_ec2_runner,
    store_workflow_runner,
    trigger_ami_creation,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_test_mode = {'enabled': False}


def is_test_mode() -> bool:
    """Check if test mode is enabled."""
    return _test_mode['enabled']


def set_test_mode(enabled: bool):
    """Enable or disable test mode."""
    _test_mode['enabled'] = enabled


def get_header_case_insensitive(headers: dict, header_name: str) -> str:
    """Get a header value by name, case-insensitively."""
    if not headers:
        return ''
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value or ''
    return ''


def handle_ec2_runner_get(_event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET requests for EC2 runner status."""
    result = get_ec2_runner_status()
    response = success_response(result)
    return response


def handle_ec2_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST requests to launch a new EC2 runner."""
    try:
        body = parse_body(event)
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')
        run_id = body.get('run_id')
        runner_type = body.get('runner_type', 'ec2')

        if not job_id:
            response = error_response(400, 'Missing required field: job_id')
        elif not github_repo:
            response = error_response(400, 'Missing required field: github_repo')
        elif is_test_mode():
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/runners/ec2'])
        else:
            result = launch_ec2_runner(job_id, job_labels, github_repo, run_id, runner_type)
            response_body = result.copy()
            capacity_error = not result.get('success') and is_capacity_error(result)
            status_code = 503 if capacity_error else (200 if result.get('success') else 500)
            response = json_response(status_code, response_body)
    except (ValueError, KeyError) as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


ROUTE_MAP = {
    ('/v1/runners/ec2', 'POST'): handle_ec2_runner_post,
    ('/v1/runners/ec2', 'GET'): handle_ec2_runner_get
}


TEST_MODE_MOCK_PATHS = {
    '/v1/runners/ec2': {'success': True, 'instance_id': 'i-test-mode-mock', 'test_mode': True}
}


def _handle_sqs_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle SQS event containing runner request(s) from /v1/runners endpoint."""
    records = event.get('Records', [])
    results = []

    for record in records:
        try:
            body = json.loads(record.get('body', '{}'))
            job_id = body.get('job_id')
            job_labels = body.get('job_labels', [])
            github_repo = body.get('github_repo')
            run_id = body.get('run_id')
            runner_type = body.get('runner_type', 'ec2')

            logger.info(
                "Processing SQS runner request: job_id=%s, labels=%s, repo=%s",
                job_id, job_labels, github_repo
            )

            if not job_id or not github_repo:
                logger.error("Missing required fields in SQS message: job_id=%s, github_repo=%s",
                             job_id, github_repo)
                results.append({
                    'messageId': record.get('messageId'),
                    'error': 'Missing required fields'
                })
                continue

            result = launch_ec2_runner(job_id, job_labels, github_repo, run_id, runner_type)
            results.append({
                'messageId': record.get('messageId'),
                'result': result
            })
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Error processing SQS record: %s", exc)
            results.append({
                'messageId': record.get('messageId'),
                'error': str(exc)
            })

    # Check if any failures should cause message to be retried
    failures = [r for r in results if r.get('error') or not r.get('result', {}).get('success')]
    if failures:
        logger.warning("Some SQS messages failed: %s", failures)
        # Don't raise - let messages succeed even if EC2 launch failed
        # The result is already logged

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processed SQS records',
            'results': results
        })
    }


def lambda_handler(event, _context):
    """AWS Lambda handler for EC2 runner API requests (HTTP or SQS)."""
    logger.info("Received event: %s", json.dumps(event))

    # Check if this is an SQS event
    records = event.get('Records', [])
    if records and records[0].get('eventSource') == 'aws:sqs':
        return _handle_sqs_event(event)

    # HTTP request handling
    headers = event.get('headers', {})
    test_mode_header = get_header_case_insensitive(headers, 'x-test-mode')
    set_test_mode(test_mode_header == 'true')

    if is_test_mode():
        logger.info("Test mode enabled - will return mock responses for POST requests")

    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
            },
            'body': ''
        }

    path = event.get('path', '')
    handler = ROUTE_MAP.get((path, method))
    return handler(event) if handler else error_response(404, 'Not found')
