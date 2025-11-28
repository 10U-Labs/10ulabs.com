import json
import logging
import os
import time
from typing import Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_circuit_breaker_state(table_name: str) -> dict:
    dynamodb = boto3.client('dynamodb')

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={'state_id': {'S': 'current'}}
        )

        if 'Item' not in response:
            return {
                'state': 'closed',
                'recovery_attempts': 0,
                'last_recovery_attempt': 0,
                'last_failure_time': 0
            }

        item = response['Item']
        return {
            'state': item.get('state', {}).get('S', 'closed'),
            'recovery_attempts': int(item.get('recovery_attempts', {}).get('N', '0')),
            'last_recovery_attempt': int(item.get('last_recovery_attempt', {}).get('N', '0')),
            'last_failure_time': int(item.get('last_failure_time', {}).get('N', '0'))
        }
    except ClientError as e:
        logger.error("Failed to get circuit breaker state: %s", e)
        return {'state': 'unknown', 'recovery_attempts': 0, 'last_recovery_attempt': 0, 'last_failure_time': 0}


def update_circuit_breaker_state(table_name: str, state: str, recovery_attempts: int) -> dict:
    dynamodb = boto3.client('dynamodb')
    current_time = int(time.time())
    result: dict[str, Any] = {'success': False}

    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'state_id': {'S': 'current'},
                'state': {'S': state},
                'recovery_attempts': {'N': str(recovery_attempts)},
                'last_recovery_attempt': {'N': str(current_time)},
                'last_failure_time': {'N': str(current_time)},
                'ttl': {'N': str(current_time + 2592000)}
            }
        )
        logger.info("Updated circuit breaker state to: %s", state)
        result = {'success': True}
    except ClientError as e:
        logger.error("Failed to update circuit breaker state: %s", e)
        result = {'success': False, 'error': str(e)}

    return result


def calculate_backoff_seconds(recovery_attempts: int) -> int:
    base_delay = 60
    max_delay = 3600
    backoff = min(base_delay * (2 ** recovery_attempts), max_delay)
    return backoff


def check_health(function_name: str) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'httpMethod': 'GET',
                'path': '/v1/runners/health',
                'headers': {}
            })
        )

        payload = json.loads(response['Payload'].read())
        status_code = payload.get('statusCode', 500)

        if status_code == 200:
            body = json.loads(payload.get('body', '{}'))
            circuit_state = body.get('circuit_breaker', 'unknown')
            logger.info("Health check passed. Circuit state: %s", circuit_state)
            return {'healthy': True, 'circuit_state': circuit_state}

        logger.warning("Health check returned status %d", status_code)
        return {'healthy': False, 'reason': f'Status code {status_code}'}

    except (ClientError, json.JSONDecodeError) as e:
        logger.error("Health check failed: %s", e)
        return {'healthy': False, 'reason': str(e)}


def enable_event_source_mappings(function_name: str) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        response = lambda_client.list_event_source_mappings(FunctionName=function_name)

        enabled_count = 0
        for mapping in response.get('EventSourceMappings', []):
            if mapping['State'] == 'Disabled':
                lambda_client.update_event_source_mapping(
                    UUID=mapping['UUID'],
                    Enabled=True
                )
                logger.info("Enabled event source mapping: %s", mapping['UUID'])
                enabled_count += 1

        return {
            'success': True,
            'enabled_count': enabled_count,
            'message': f'Enabled {enabled_count} event source mappings'
        }
    except ClientError as e:
        logger.error("Failed to enable event source mappings: %s", e)
        return {'success': False, 'error': str(e)}


def set_lambda_reserved_concurrency(function_name: str, concurrency: int) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        if concurrency == 0:
            lambda_client.delete_function_concurrency(FunctionName=function_name)
            logger.info("Removed reserved concurrency limit for %s", function_name)
        else:
            lambda_client.put_function_concurrency(
                FunctionName=function_name,
                ReservedConcurrentExecutions=concurrency
            )
            logger.info("Set reserved concurrency for %s to %d", function_name, concurrency)

        return {'success': True, 'concurrency': concurrency}
    except ClientError as e:
        logger.error("Failed to set reserved concurrency: %s", e)
        return {'success': False, 'error': str(e)}


def send_recovery_notification(topic_arn: str, state: str, recovery_attempts: int, actions: list) -> dict:
    sns_client = boto3.client('sns')

    try:
        message = f"""Circuit Breaker Auto-Recovery

State Transition: {state}
Recovery Attempts: {recovery_attempts}

Actions Taken:
{chr(10).join(f"- {action}" for action in actions)}

The system is attempting to self-heal.
"""
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=f"Circuit Breaker Recovery: {state}",
            Message=message
        )
        logger.info("Sent recovery notification: %s", response.get('MessageId'))
        return {'success': True, 'message_id': response.get('MessageId')}
    except ClientError as e:
        logger.error("Failed to send notification: %s", e)
        return {'success': False, 'error': str(e)}


def attempt_recovery() -> dict:
    state_table = os.environ.get('STATE_TABLE_NAME')
    webhook_function = os.environ.get('WEBHOOK_FUNCTION_NAME')
    sns_topic = os.environ.get('SNS_TOPIC_ARN')
    max_recovery_attempts = int(os.environ.get('MAX_RECOVERY_ATTEMPTS', '5'))

    if not state_table or not webhook_function:
        logger.error("Missing required environment variables")
        return {'error': 'Configuration error', 'message': 'Missing STATE_TABLE_NAME or WEBHOOK_FUNCTION_NAME'}

    current_state = get_circuit_breaker_state(state_table)
    recovery_attempts = current_state['recovery_attempts']
    last_recovery = current_state['last_recovery_attempt']
    current_time = int(time.time())

    result = {
        'current_state': current_state['state'],
        'recovery_attempts': recovery_attempts,
        'actions_taken': []
    }

    if current_state['state'] != 'open':
        logger.info("Circuit breaker not in open state (%s), no recovery needed", current_state['state'])
        result['message'] = 'Circuit breaker not in open state'
        return result

    required_backoff = calculate_backoff_seconds(recovery_attempts)
    time_since_last_attempt = current_time - last_recovery

    if time_since_last_attempt < required_backoff:
        logger.info("Backoff period not elapsed (%ds remaining)", required_backoff - time_since_last_attempt)
        result['message'] = f'Waiting for backoff period ({required_backoff - time_since_last_attempt}s remaining)'
        return result

    if recovery_attempts >= max_recovery_attempts:
        logger.error("Max recovery attempts reached (%d), manual intervention required", max_recovery_attempts)
        result['message'] = 'Max recovery attempts reached - manual intervention required'
        result['manual_intervention_required'] = True

        if sns_topic:
            send_recovery_notification(
                sns_topic,
                'FAILED',
                recovery_attempts,
                ['Max recovery attempts exceeded', 'Manual intervention required']
            )

        return result

    logger.info("Attempting recovery (attempt %d/%d)", recovery_attempts + 1, max_recovery_attempts)

    health_check = check_health(webhook_function)

    if not health_check.get('healthy'):
        logger.warning("Health check failed: %s", health_check.get('reason'))
        update_circuit_breaker_state(state_table, 'open', recovery_attempts + 1)
        result['message'] = f"Health check failed: {health_check.get('reason')}"
        result['recovery_attempts'] = recovery_attempts + 1
        return result

    result['actions_taken'].append('Health check passed')

    concurrency_level = min(10, 2 ** recovery_attempts)
    concurrency_result = set_lambda_reserved_concurrency(webhook_function, concurrency_level)

    if concurrency_result['success']:
        result['actions_taken'].append(f'Set reserved concurrency to {concurrency_level}')

    enable_result = enable_event_source_mappings(webhook_function)

    if enable_result['success']:
        result['actions_taken'].append(f"Enabled {enable_result['enabled_count']} event source mappings")

    update_circuit_breaker_state(state_table, 'half-open', recovery_attempts + 1)
    result['new_state'] = 'half-open'
    result['recovery_attempts'] = recovery_attempts + 1
    result['concurrency_level'] = concurrency_level

    if sns_topic:
        send_recovery_notification(
            sns_topic,
            'HALF-OPEN',
            recovery_attempts + 1,
            result['actions_taken']
        )

    logger.info("Recovery attempt successful - moved to half-open state with concurrency %d", concurrency_level)

    return result


def lambda_handler(_event, _context):
    logger.info("Starting circuit breaker recovery check")

    result = attempt_recovery()

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
