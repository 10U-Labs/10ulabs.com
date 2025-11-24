import os
from unittest.mock import patch, MagicMock
from test.api.pre_deployment.conftest import (
    parse_response_body,
    assert_response_status,
    create_mock_lambda_list_mappings_error,
    create_mock_lambda_put_concurrency_error,
    create_mock_sns_publish_error,
    create_mock_lambda_with_mappings
)
from botocore.exceptions import ClientError


def test_disable_sqs_event_source_lists_mappings(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.return_value = {'EventSourceMappings': []}
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_remediation.disable_sqs_event_source('test-function')
    assert mock_lambda.list_event_source_mappings.called


def test_disable_sqs_event_source_disables_enabled_mappings(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.return_value = {
            'EventSourceMappings': [
                {'UUID': 'mapping-1', 'State': 'Enabled'}
            ]
        }
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_remediation.disable_sqs_event_source('test-function')
    assert mock_lambda.update_event_source_mapping.called


def test_disable_sqs_event_source_counts_disabled(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.return_value = {
            'EventSourceMappings': [
                {'UUID': 'mapping-1', 'State': 'Enabled'},
                {'UUID': 'mapping-2', 'State': 'Enabled'}
            ]
        }
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_remediation.disable_sqs_event_source('test-function')
    assert result['disabled_count'] == 2


def test_disable_sqs_event_source_handles_no_mappings(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.return_value = {'EventSourceMappings': []}
        mock_boto_client.return_value = mock_lambda
        result = circuit_breaker_remediation.disable_sqs_event_source('test-function')
    assert result['disabled_count'] == 0


def test_disable_sqs_event_source_handles_api_error(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = create_mock_lambda_list_mappings_error()
        result = circuit_breaker_remediation.disable_sqs_event_source('test-function')
    assert result['success'] is False


def test_set_lambda_reserved_concurrency_sets_to_zero(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda
        circuit_breaker_remediation.set_lambda_reserved_concurrency('test-function', 0)
    assert mock_lambda.put_function_concurrency.called


def test_set_lambda_reserved_concurrency_handles_api_error(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = create_mock_lambda_put_concurrency_error()
        result = circuit_breaker_remediation.set_lambda_reserved_concurrency('test-function', 0)
    assert result['success'] is False


def test_send_sns_notification_publishes_message(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id'}
        mock_boto_client.return_value = mock_sns
        circuit_breaker_remediation.send_sns_notification('arn:aws:sns:test', 'Subject', 'Message')
    assert mock_sns.publish.called


def test_send_sns_notification_includes_subject(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id'}
        mock_boto_client.return_value = mock_sns
        circuit_breaker_remediation.send_sns_notification('arn:aws:sns:test', 'Test Subject', 'Message')
        call_args = mock_sns.publish.call_args
    assert call_args[1]['Subject'] == 'Test Subject'


def test_send_sns_notification_handles_api_error(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = create_mock_sns_publish_error()
        result = circuit_breaker_remediation.send_sns_notification('arn:aws:sns:test', 'Subject', 'Message')
    assert result['success'] is False


def test_record_incident_creates_incident_record(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_remediation.record_incident('test-table', 'test-alarm', 'test-reason')
    assert mock_dynamodb.put_item.called


def test_record_incident_sets_correct_attributes(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_remediation.record_incident('test-table', 'test-alarm', 'test-reason')
        call_args = mock_dynamodb.put_item.call_args
    assert 'alarm_name' in str(call_args)


def test_record_incident_handles_dynamodb_error(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable'}},
            'PutItem'
        )
        mock_boto_client.return_value = mock_dynamodb
        result = circuit_breaker_remediation.record_incident('test-table', 'test-alarm', 'test-reason')
    assert result['success'] is False


def test_update_circuit_breaker_state_sets_open_state(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_remediation.update_circuit_breaker_state('test-table', 'open')
        call_args = mock_dynamodb.put_item.call_args
    assert call_args[1]['Item']['state']['S'] == 'open'


def test_update_circuit_breaker_state_resets_recovery_attempts(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_remediation.update_circuit_breaker_state('test-table', 'open')
        call_args = mock_dynamodb.put_item.call_args
    assert call_args[1]['Item']['recovery_attempts']['N'] == '0'


def test_update_circuit_breaker_state_sets_ttl(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        circuit_breaker_remediation.update_circuit_breaker_state('test-table', 'open')
        call_args = mock_dynamodb.put_item.call_args
    assert 'ttl' in call_args[1]['Item']


def test_update_circuit_breaker_state_handles_dynamodb_error(circuit_breaker_remediation):
    with patch('boto3.client') as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable'}},
            'PutItem'
        )
        mock_boto_client.return_value = mock_dynamodb
        result = circuit_breaker_remediation.update_circuit_breaker_state('test-table', 'open')
    assert result['success'] is False


def test_handle_cloudwatch_alarm_event_parses_alarm_details(circuit_breaker_remediation):
    event = {
        'source': 'aws.cloudwatch',
        'detail-type': 'CloudWatch Alarm State Change',
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'SNS_TOPIC_ARN': 'arn:aws:sns:test',
        'INCIDENT_TABLE_NAME': 'test-incidents',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client'):
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert result['alarm_name'] == 'test-alarm'


def test_handle_cloudwatch_alarm_event_skips_non_alarm_state(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'OK', 'reason': 'Back to normal'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'SNS_TOPIC_ARN': 'arn:aws:sns:test',
        'INCIDENT_TABLE_NAME': 'test-incidents',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client'):
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert 'message' in result


def test_handle_cloudwatch_alarm_event_disables_event_sources(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.return_value = create_mock_lambda_with_mappings()
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert any('Disabled SQS event sources' in action for action in result.get('actions_taken', []))


def test_handle_cloudwatch_alarm_event_sets_zero_concurrency(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_lambda = MagicMock()
            mock_lambda.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_boto_client.return_value = mock_lambda
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert any('reserved concurrency to 0' in action for action in result.get('actions_taken', []))


def test_handle_cloudwatch_alarm_event_sends_notification(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'SNS_TOPIC_ARN': 'arn:aws:sns:test',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_client.publish.return_value = {'MessageId': 'test-id'}
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert any('SNS notification' in action for action in result.get('actions_taken', []))


def test_handle_cloudwatch_alarm_event_records_incident(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'INCIDENT_TABLE_NAME': 'test-incidents',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert any('Recorded incident' in action for action in result.get('actions_taken', []))


def test_handle_cloudwatch_alarm_event_updates_state_table(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert any('circuit breaker state to OPEN' in action for action in result.get('actions_taken', []))


def test_handle_cloudwatch_alarm_event_tracks_all_actions(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'SNS_TOPIC_ARN': 'arn:aws:sns:test',
        'INCIDENT_TABLE_NAME': 'test-incidents',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.list_event_source_mappings.return_value = {'EventSourceMappings': []}
            mock_client.publish.return_value = {'MessageId': 'test-id'}
            mock_boto_client.return_value = mock_client
            result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert len(result.get('actions_taken', [])) >= 3


def test_handle_cloudwatch_alarm_event_handles_missing_config(circuit_breaker_remediation):
    event = {
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {}, clear=True):
        result = circuit_breaker_remediation.handle_cloudwatch_alarm_event(event)
    assert 'error' in result


def test_lambda_handler_routes_cloudwatch_alarm_events(circuit_breaker_remediation, lambda_context):
    event = {
        'source': 'aws.cloudwatch',
        'detail-type': 'CloudWatch Alarm State Change',
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client'):
            response = circuit_breaker_remediation.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_handles_unsupported_event_types(circuit_breaker_remediation, lambda_context):
    event = {
        'source': 'aws.ec2',
        'detail-type': 'EC2 Instance State-change Notification'
    }
    with patch('boto3.client'):
        response = circuit_breaker_remediation.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_returns_result_for_valid_events(circuit_breaker_remediation, lambda_context):
    event = {
        'source': 'aws.cloudwatch',
        'detail-type': 'CloudWatch Alarm State Change',
        'detail': {
            'alarmName': 'test-alarm',
            'state': {'value': 'ALARM', 'reason': 'Threshold exceeded'}
        }
    }
    with patch.dict(os.environ, {
        'WEBHOOK_FUNCTION_NAME': 'test-function',
        'STATE_TABLE_NAME': 'test-state'
    }):
        with patch('boto3.client'):
            response = circuit_breaker_remediation.lambda_handler(event, lambda_context)
            body = parse_response_body(response)
    assert 'alarm_name' in body
