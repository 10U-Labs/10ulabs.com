"""Lambda handler for ECS runner API endpoint."""
import json
import logging
from typing import Any, Dict

from aws_clients import (
    get_ecs_client,
    get_ssm_client,
    get_dynamodb_client,
    set_client,
    reset_clients,
)
from github_runner_api import (
    get_github_token,
    get_runner_registration_token,
    list_repo_runners,
    delete_runner,
    cleanup_offline_runners,
    get_existing_runner_for_workflow,
    build_runner_labels,
    reset_github_token_cache,
)
from infra_validation import (
    ensure_dependencies_valid,
    validate_all_dependencies,
    validate_security_groups,
    validate_subnets,
    validate_vpc,
    get_dependencies_status,
    reset_dependency_validation,
    set_dependencies_status,
)
from lambda_http import (
    json_response,
    success_response,
    error_response,
    parse_body,
    is_capacity_error,
)
from fargate_ops import (
    get_latest_ecr_image,
    trigger_image_creation,
    launch_fargate_runner,
    get_ecs_runner_status,
    get_fargate_task_status,
    is_fargate_spot_interruption,
    wait_for_fargate_task_provisioned,
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
    """Get a header value case-insensitively."""
    if not headers:
        return ''
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value or ''
    return ''


def handle_ecs_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST requests to the ECS runner endpoint."""
    try:
        body = parse_body(event)
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')
        run_id = body.get('run_id')
        runner_type = body.get('runner_type', 'fargate')

        if not job_id:
            response = error_response(400, 'Missing required field: job_id')
        elif not github_repo:
            response = error_response(400, 'Missing required field: github_repo')
        elif is_test_mode():
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/runners/ecs'])
        else:
            image_check = get_latest_ecr_image()
            if not image_check['success']:
                logger.warning("No stable image found, triggering image creation")
                trigger_result = trigger_image_creation()
                response = json_response(202, {
                    'success': False,
                    'error': 'No stable image available',
                    'message': 'Image build triggered',
                    'trigger_result': trigger_result
                })
            else:
                result = launch_fargate_runner(job_id, job_labels, github_repo, run_id, runner_type)
                response_body = result.copy()
                capacity_error = not result.get('success') and is_capacity_error(result)
                status_code = 503 if capacity_error else (200 if result.get('success') else 500)
                response = json_response(status_code, response_body)
    except (ValueError, KeyError) as e:
        logger.error("Error handling POST request: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def handle_ecs_runner_get(_event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET requests to the ECS runner endpoint."""
    result = get_ecs_runner_status()
    response = success_response(result)
    return response


ROUTE_MAP = {
    ('/v1/runners/ecs', 'POST'): handle_ecs_runner_post,
    ('/v1/runners/ecs', 'GET'): handle_ecs_runner_get
}


TEST_MODE_MOCK_PATHS = {
    '/v1/runners/ecs': {'success': True, 'task_arn': 'arn:aws:ecs:test-mode-mock', 'test_mode': True}
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
            runner_type = body.get('runner_type', 'fargate')

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

            image_check = get_latest_ecr_image()
            if not image_check['success']:
                logger.warning("No stable image found, triggering image creation")
                trigger_image_creation()
                results.append({
                    'messageId': record.get('messageId'),
                    'error': 'No stable image available'
                })
                continue

            result = launch_fargate_runner(job_id, job_labels, github_repo, run_id, runner_type)
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

    failures = [r for r in results if r.get('error') or not r.get('result', {}).get('success')]
    if failures:
        logger.warning("Some SQS messages failed: %s", failures)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processed SQS records',
            'results': results
        })
    }


def lambda_handler(event, _context):
    """Main Lambda handler for ECS runner API requests (HTTP or SQS)."""
    logger.info("Received event: %s", json.dumps(event))

    records = event.get('Records', [])
    if records and records[0].get('eventSource') == 'aws:sqs':
        return _handle_sqs_event(event)

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

    if handler:
        response = handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
