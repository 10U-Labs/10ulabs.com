import json
import logging
import os
import time
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def disable_sqs_event_source(lambda_function_name: str) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        response = lambda_client.list_event_source_mappings(
            FunctionName=lambda_function_name
        )

        disabled_count = 0
        for mapping in response.get('EventSourceMappings', []):
            if mapping['State'] == 'Enabled':
                lambda_client.update_event_source_mapping(
                    UUID=mapping['UUID'],
                    Enabled=False
                )
                logger.info("Disabled event source mapping: %s", mapping['UUID'])
                disabled_count += 1

        return {
            'success': True,
            'disabled_count': disabled_count,
            'message': f'Disabled {disabled_count} event source mappings'
        }
    except ClientError as e:
        logger.error("Failed to disable event source mappings: %s", e)
        return {'success': False, 'error': str(e)}


def set_lambda_reserved_concurrency(function_name: str, concurrency: int) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        lambda_client.put_function_concurrency(
            FunctionName=function_name,
            ReservedConcurrentExecutions=concurrency
        )
        logger.info("Set reserved concurrency for %s to %d", function_name, concurrency)
        return {
            'success': True,
            'message': f'Set reserved concurrency to {concurrency}'
        }
    except ClientError as e:
        logger.error("Failed to set reserved concurrency: %s", e)
        return {'success': False, 'error': str(e)}


def enable_sqs_event_source(lambda_function_name: str) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        response = lambda_client.list_event_source_mappings(
            FunctionName=lambda_function_name
        )

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


def remove_lambda_reserved_concurrency(function_name: str) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        lambda_client.delete_function_concurrency(FunctionName=function_name)
        logger.info("Removed reserved concurrency for %s", function_name)
        return {
            'success': True,
            'message': 'Removed reserved concurrency limit'
        }
    except ClientError as e:
        logger.error("Failed to remove reserved concurrency: %s", e)
        return {'success': False, 'error': str(e)}


def send_sns_notification(topic_arn: str, subject: str, message: str) -> dict:
    sns_client = boto3.client('sns')

    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        logger.info("Sent SNS notification: %s", response.get('MessageId'))
        return {'success': True, 'message_id': response.get('MessageId')}
    except ClientError as e:
        logger.error("Failed to send SNS notification: %s", e)
        return {'success': False, 'error': str(e)}


def record_incident(table_name: str, alarm_name: str, alarm_reason: str) -> dict:
    dynamodb = boto3.client('dynamodb')

    try:
        incident_id = f"{alarm_name}-{int(time.time())}"
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'incident_id': {'S': incident_id},
                'alarm_name': {'S': alarm_name},
                'alarm_reason': {'S': alarm_reason},
                'timestamp': {'N': str(int(time.time()))},
                'ttl': {'N': str(int(time.time()) + 2592000)}
            }
        )
        logger.info("Recorded incident: %s", incident_id)
        return {'success': True, 'incident_id': incident_id}
    except ClientError as e:
        logger.error("Failed to record incident: %s", e)
        return {'success': False, 'error': str(e)}


def update_circuit_breaker_state(table_name: str, state: str) -> dict:
    dynamodb = boto3.client('dynamodb')

    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'state_id': {'S': 'current'},
                'state': {'S': state},
                'recovery_attempts': {'N': '0'},
                'last_recovery_attempt': {'N': '0'},
                'last_failure_time': {'N': str(int(time.time()))},
                'ttl': {'N': str(int(time.time()) + 2592000)}
            }
        )
        logger.info("Updated circuit breaker state to: %s", state)
        return {'success': True}
    except ClientError as e:
        logger.error("Failed to update circuit breaker state: %s", e)
        return {'success': False, 'error': str(e)}


def handle_alarm_ok_state(
    result: dict,
    webhook_function_name: str,
    state_table_name: str,
    sns_topic_arn: str,
    alarm_name: str
) -> dict:
    logger.info("Alarm returned to OK state, resetting circuit breaker")

    enable_result = enable_sqs_event_source(webhook_function_name)
    if enable_result['success']:
        result['actions_taken'].append(f"Enabled SQS event sources: {enable_result['enabled_count']}")

    concurrency_result = remove_lambda_reserved_concurrency(webhook_function_name)
    if concurrency_result['success']:
        result['actions_taken'].append('Removed Lambda reserved concurrency limit')

    if state_table_name:
        state_result = update_circuit_breaker_state(state_table_name, 'closed')
        if state_result['success']:
            result['actions_taken'].append('Reset circuit breaker state to CLOSED')

    if sns_topic_arn:
        notification_message = f"""Circuit Breaker Auto-Recovery Complete

Alarm: {alarm_name}
State: OK

Actions Taken:
{chr(10).join(f"- {action}" for action in result['actions_taken'])}

The system has automatically recovered.
"""
        sns_result = send_sns_notification(
            sns_topic_arn,
            f"Circuit Breaker Recovered: {alarm_name}",
            notification_message
        )
        if sns_result['success']:
            result['actions_taken'].append('Sent recovery notification')

    result['message'] = 'Circuit breaker reset to closed state'
    logger.info("Recovery complete. Actions taken: %s", result['actions_taken'])
    return result


def handle_cloudwatch_alarm_event(event: dict) -> dict:
    detail = event.get('detail', {})
    alarm_name = detail.get('alarmName', 'Unknown')
    alarm_reason = detail.get('state', {}).get('reason', 'No reason provided')
    new_state_value = detail.get('state', {}).get('value', 'UNKNOWN')

    logger.info("Processing CloudWatch alarm event: %s (state: %s)", alarm_name, new_state_value)

    webhook_function_name = os.environ.get('WEBHOOK_FUNCTION_NAME')
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    incident_table_name = os.environ.get('INCIDENT_TABLE_NAME')
    state_table_name = os.environ.get('STATE_TABLE_NAME')

    result = {
        'alarm_name': alarm_name,
        'alarm_state': new_state_value,
        'actions_taken': []
    }

    if not webhook_function_name:
        logger.error("WEBHOOK_FUNCTION_NAME not set")
        return {'statusCode': 500, 'error': 'Configuration error'}

    if new_state_value == 'OK':
        return handle_alarm_ok_state(
            result, webhook_function_name, state_table_name, sns_topic_arn, alarm_name
        )

    if new_state_value != 'ALARM':
        logger.info("Alarm is not in ALARM or OK state, no action needed")
        result['message'] = 'Alarm not in actionable state'
        return result

    disable_result = disable_sqs_event_source(webhook_function_name)
    if disable_result['success']:
        result['actions_taken'].append(f"Disabled SQS event sources: {disable_result['disabled_count']}")

    concurrency_result = set_lambda_reserved_concurrency(webhook_function_name, 0)
    if concurrency_result['success']:
        result['actions_taken'].append('Set Lambda reserved concurrency to 0')

    if sns_topic_arn:
        notification_message = f"""Circuit Breaker Remediation Triggered

Alarm: {alarm_name}
State: {new_state_value}
Reason: {alarm_reason}

Actions Taken:
{chr(10).join(f"- {action}" for action in result['actions_taken'])}

Manual intervention may be required to restore service.
"""
        sns_result = send_sns_notification(
            sns_topic_arn,
            f"Circuit Breaker Alert: {alarm_name}",
            notification_message
        )
        if sns_result['success']:
            result['actions_taken'].append('Sent SNS notification')

    if incident_table_name:
        incident_result = record_incident(incident_table_name, alarm_name, alarm_reason)
        if incident_result['success']:
            result['actions_taken'].append(f"Recorded incident: {incident_result['incident_id']}")

    if state_table_name:
        state_result = update_circuit_breaker_state(state_table_name, 'open')
        if state_result['success']:
            result['actions_taken'].append('Set circuit breaker state to OPEN')
            result['actions_taken'].append('Auto-recovery will attempt after cooldown period')

    logger.info("Remediation complete. Actions taken: %s", result['actions_taken'])
    return result


def lambda_handler(event, _context):
    logger.info("Received event: %s", json.dumps(event))

    if event.get('source') == 'aws.cloudwatch' and event.get('detail-type') == 'CloudWatch Alarm State Change':
        result = handle_cloudwatch_alarm_event(event)
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    logger.warning("Unsupported event type, no action taken")
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Unsupported event type'})
    }
