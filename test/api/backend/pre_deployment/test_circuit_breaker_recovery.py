import json
import os
import time
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from .conftest import (
    parse_response_body,
    assert_response_status,
    create_mock_lambda_list_mappings_error,
    create_mock_lambda_put_concurrency_error,
    create_mock_sns_publish_error,
    create_mock_lambda_with_mappings
)


def test_get_circuit_breaker_state_returns_default_when_not_exists(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = {}
        mock_boto_client.return_value = mock_dynamodb
        result = circuit_breaker_recovery.get_circuit_breaker_state('test-table')
    assert result['state'] == 'closed'


def test_get_circuit_breaker_state_returns_stored_state(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'state': {'S': 'open'},
                'recovery_attempts': {'N': '3'},
                'last_recovery_attempt': {'N': '1234567890'},
                'last_failure_time': {'N': '1234567890'}
            }
        }
        mock_boto_client.return_value = mock_dynamodb
        result = circuit_breaker_recovery.get_circuit_breaker_state('test-table')
    assert result['state'] == 'open'


def test_get_circuit_breaker_state_handles_dynamodb_error(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable'}},
            'GetItem'
        )
        mock_boto_client.return_value = mock_dynamodb
        result = circuit_breaker_recovery.get_circuit_breaker_state('test-table')
    assert result['state'] == 'unknown'


def test_update_circuit_breaker_state_writes_to_dynamodb(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_recovery.update_circuit_breaker_state('test-table', 'half-open', 2)
    assert mock_dynamodb.put_item.called


def test_update_circuit_breaker_state_sets_correct_state(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_recovery.update_circuit_breaker_state('test-table', 'half-open', 2)
        call_args = mock_dynamodb.put_item.call_args
    assert call_args[1]['Item']['state']['S'] == 'half-open'


def test_update_circuit_breaker_state_sets_recovery_attempts(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_recovery.update_circuit_breaker_state('test-table', 'half-open', 3)
        call_args = mock_dynamodb.put_item.call_args
    assert call_args[1]['Item']['recovery_attempts']['N'] == '3'


def test_calculate_backoff_seconds_starts_at_60(circuit_breaker_recovery):
    result = circuit_breaker_recovery.calculate_backoff_seconds(0)
    assert result == 60


def test_calculate_backoff_seconds_doubles_each_attempt(circuit_breaker_recovery):
    result = circuit_breaker_recovery.calculate_backoff_seconds(2)
    assert result == 240


def test_calculate_backoff_seconds_caps_at_3600(circuit_breaker_recovery):
    result = circuit_breaker_recovery.calculate_backoff_seconds(10)
    assert result == 3600


def test_calculate_backoff_seconds_handles_first_attempt(circuit_breaker_recovery):
    result = circuit_breaker_recovery.calculate_backoff_seconds(1)
    assert result == 120


def test_calculate_backoff_seconds_handles_max_attempts(circuit_breaker_recovery):
    result = circuit_breaker_recovery.calculate_backoff_seconds(5)
    assert result == 1920


def test_check_health_invokes_health_endpoint(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({'circuit_breaker': 'closed'})
            }).encode())
        }
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_recovery.check_health('test-function')
    assert mock_lambda.invoke.called


def test_check_health_returns_healthy_when_200(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({'circuit_breaker': 'closed'})
            }).encode())
        }
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_recovery.check_health('test-function')
    assert result['healthy'] is True


def test_check_health_returns_unhealthy_when_non_200(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal error'})
            }).encode())
        }
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_recovery.check_health('test-function')
    assert result['healthy'] is False


def test_check_health_extracts_circuit_state_from_response(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({'circuit_breaker': 'half-open'})
            }).encode())
        }
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_recovery.check_health('test-function')
    assert result['circuit_state'] == 'half-open'


def test_check_health_handles_lambda_invoke_error(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.invoke.side_effect = ClientError(
            {'Error': {'Code': 'FunctionNotFound'}},
            'Invoke'
        )
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_recovery.check_health('test-function')
    assert result['healthy'] is False


def test_check_health_handles_malformed_response(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: b'invalid json')
        }
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_recovery.check_health('test-function')
    assert result['healthy'] is False


def test_enable_event_source_mappings_enables_disabled_sources(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.return_value = {
            'EventSourceMappings': [{'UUID': 'test-uuid', 'State': 'Disabled'}]
        }
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_recovery.enable_event_source_mappings('test-function')
    assert mock_lambda.update_event_source_mapping.called


def test_enable_event_source_mappings_skips_already_enabled(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = create_mock_lambda_with_mappings()
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_recovery.enable_event_source_mappings('test-function')
    assert not mock_lambda.update_event_source_mapping.called


def test_enable_event_source_mappings_counts_enabled_sources(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.return_value = {
            'EventSourceMappings': [
                {'UUID': 'uuid-1', 'State': 'Disabled'},
                {'UUID': 'uuid-2', 'State': 'Disabled'}
            ]
        }
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_recovery.enable_event_source_mappings('test-function')
    assert result['enabled_count'] == 2


def test_enable_event_source_mappings_handles_no_mappings(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.return_value = {'EventSourceMappings': []}
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_recovery.enable_event_source_mappings('test-function')
    assert result['enabled_count'] == 0


def test_enable_event_source_mappings_handles_api_error(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = create_mock_lambda_list_mappings_error()
        result = circuit_breaker_recovery.enable_event_source_mappings('test-function')
    assert result['success'] is False


def test_set_lambda_reserved_concurrency_sets_limit(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_recovery.set_lambda_reserved_concurrency('test-function', 5)
    assert mock_lambda.put_function_concurrency.called


def test_set_lambda_reserved_concurrency_removes_limit_when_zero(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_recovery.set_lambda_reserved_concurrency('test-function', 0)
    assert mock_lambda.delete_function_concurrency.called


def test_set_lambda_reserved_concurrency_handles_api_error(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = create_mock_lambda_put_concurrency_error()
        result = circuit_breaker_recovery.set_lambda_reserved_concurrency('test-function', 5)
    assert result['success'] is False


def test_attempt_recovery_skips_when_not_in_open_state(circuit_breaker_recovery):
    with patch.dict(os.environ, {'STATE_TABLE_NAME': 'test-table', 'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        with patch('boto3.client') as mock_boto_client:
            mock_dynamodb = MagicMock()
            mock_dynamodb.get_item.return_value = {
                'Item': {
                    'state': {'S': 'closed'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_boto_client.return_value = mock_dynamodb
            result = circuit_breaker_recovery.attempt_recovery()
    assert 'message' in result


def test_attempt_recovery_waits_for_backoff_period(circuit_breaker_recovery):
    current_time = int(time.time())
    with patch.dict(os.environ, {'STATE_TABLE_NAME': 'test-table', 'WEBHOOK_FUNCTION_NAME': 'test-function'}):
        with patch('boto3.client') as mock_boto_client:
            mock_dynamodb = MagicMock()
            mock_dynamodb.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '1'},
                    'last_recovery_attempt': {'N': str(current_time - 30)},
                    'last_failure_time': {'N': str(current_time)}
                }
            }
            mock_boto_client.return_value = mock_dynamodb
            result = circuit_breaker_recovery.attempt_recovery()
    assert 'Waiting for backoff period' in result.get('message', '')


def test_attempt_recovery_checks_max_attempts(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'MAX_RECOVERY_ATTEMPTS': '5'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_dynamodb = MagicMock()
            mock_dynamodb.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '5'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_boto_client.return_value = mock_dynamodb
            result = circuit_breaker_recovery.attempt_recovery()
    assert result.get('manual_intervention_required') is True


def test_attempt_recovery_performs_health_check(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_client.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker': 'closed'})
                }).encode())
            }
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_recovery.attempt_recovery()
    actions_str = str(result.get('actions_taken', []))
    assert 'Health check passed' in actions_str


def test_attempt_recovery_fails_when_health_check_fails(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_client.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Internal error'})
                }).encode())
            }
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_recovery.attempt_recovery()
    assert 'Health check failed' in result.get('message', '')


def test_attempt_recovery_increments_recovery_attempts(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '1'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_client.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Internal error'})
                }).encode())
            }
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_recovery.attempt_recovery()
    assert result['recovery_attempts'] == 2


def test_attempt_recovery_sets_gradual_concurrency(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_client.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker': 'closed'})
                }).encode())
            }
            mock_client.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_recovery.attempt_recovery()
    assert result['concurrency_level'] == 1


def test_attempt_recovery_enables_event_sources(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_client.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker': 'closed'})
                }).encode())
            }
            mock_client.list_event_source_mappings.return_value = {
                'EventSourceMappings': [{'UUID': 'test-uuid', 'State': 'Disabled'}]
            }
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_recovery.attempt_recovery()
    actions_str = str(result.get('actions_taken', []))
    assert 'Enabled 1 event source mappings' in actions_str


def test_attempt_recovery_updates_state_to_half_open(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_client.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker': 'closed'})
                }).encode())
            }
            mock_client.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_recovery.attempt_recovery()
    assert result['new_state'] == 'half-open'


def test_attempt_recovery_calculates_correct_concurrency_level(circuit_breaker_recovery):
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_item.return_value = {
                'Item': {
                    'state': {'S': 'open'},
                    'recovery_attempts': {'N': '2'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_client.invoke.return_value = {
                'Payload': MagicMock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'circuit_breaker': 'closed'})
                }).encode())
            }
            mock_client.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_recovery.attempt_recovery()
    assert result['concurrency_level'] == 4


def test_lambda_handler_processes_scheduled_event(circuit_breaker_recovery, lambda_context):
    event = {}
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_dynamodb = MagicMock()
            mock_dynamodb.get_item.return_value = {
                'Item': {
                    'state': {'S': 'closed'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_boto_client.return_value = mock_dynamodb
            response = circuit_breaker_recovery.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_returns_recovery_result(circuit_breaker_recovery, lambda_context):
    event = {}
    with patch.dict(os.environ, {
        'STATE_TABLE_NAME': 'test-table',
        'WEBHOOK_FUNCTION_NAME': 'test-function'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_dynamodb = MagicMock()
            mock_dynamodb.get_item.return_value = {
                'Item': {
                    'state': {'S': 'closed'},
                    'recovery_attempts': {'N': '0'},
                    'last_recovery_attempt': {'N': '0'},
                    'last_failure_time': {'N': '0'}
                }
            }
            mock_boto_client.return_value = mock_dynamodb
            response = circuit_breaker_recovery.lambda_handler(event, lambda_context)
            body = parse_response_body(response)
    assert 'current_state' in body


def test_send_recovery_notification_publishes_to_sns(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {'MessageId': 'test-id'}
        mock_boto_client.return_value = mock_sns
        circuit_breaker_recovery.send_recovery_notification('arn:aws:sns:test', 'half-open', 2, ['action1'])
    assert mock_sns.publish.called


def test_send_recovery_notification_includes_recovery_attempts(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {'MessageId': 'test-id'}
        mock_boto_client.return_value = mock_sns
        circuit_breaker_recovery.send_recovery_notification('arn:aws:sns:test', 'half-open', 3, ['action1'])
        call_args = mock_sns.publish.call_args
    assert '3' in call_args[1]['Message']


def test_send_recovery_notification_handles_api_error(circuit_breaker_recovery):
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = create_mock_sns_publish_error()
        result = circuit_breaker_recovery.send_recovery_notification('arn:aws:sns:test', 'half-open', 2, [])
    assert result['success'] is False
