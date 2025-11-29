import json
import os
import urllib.error
from unittest.mock import patch, MagicMock, Mock
from test.api.pre_deployment.conftest import assert_response_status, create_mock_sns_publish_error

import pytest
from botocore.exceptions import ClientError


def wrap_in_sqs_event(config_event):
    return {
        'Records': [{
            'messageId': 'test-message-id',
            'body': json.dumps(config_event)
        }]
    }


class TestFormatDriftDetails:
    def test_extracts_rule_name(self, drift_recovery):
        event = {'configRuleName': 'required-tags'}
        result = drift_recovery.format_drift_details(event)
        assert result['rule_name'] == 'required-tags'

    def test_extracts_resource_type(self, drift_recovery):
        event = {'resourceType': 'AWS::EC2::SecurityGroup'}
        result = drift_recovery.format_drift_details(event)
        assert result['resource_type'] == 'AWS::EC2::SecurityGroup'

    def test_extracts_resource_id(self, drift_recovery):
        event = {'resourceId': 'sg-12345678'}
        result = drift_recovery.format_drift_details(event)
        assert result['resource_id'] == 'sg-12345678'

    def test_extracts_aws_region(self, drift_recovery):
        event = {'awsRegion': 'us-east-1'}
        result = drift_recovery.format_drift_details(event)
        assert result['aws_region'] == 'us-east-1'

    def test_formats_summary(self, drift_recovery):
        event = {
            'resourceType': 'AWS::EC2::SecurityGroup',
            'resourceId': 'sg-12345678',
            'awsRegion': 'us-east-1'
        }
        result = drift_recovery.format_drift_details(event)
        assert result['summary'] == 'AWS::EC2::SecurityGroup (sg-12345678) in us-east-1'

    def test_uses_unknown_for_missing_rule_name(self, drift_recovery):
        result = drift_recovery.format_drift_details({})
        assert result['rule_name'] == 'Unknown'

    def test_uses_unknown_for_missing_resource_type(self, drift_recovery):
        result = drift_recovery.format_drift_details({})
        assert result['resource_type'] == 'Unknown'

    def test_uses_unknown_for_missing_resource_id(self, drift_recovery):
        result = drift_recovery.format_drift_details({})
        assert result['resource_id'] == 'Unknown'

    def test_uses_unknown_for_missing_aws_region(self, drift_recovery):
        result = drift_recovery.format_drift_details({})
        assert result['aws_region'] == 'Unknown'


class TestExtractEventFromSqs:
    def test_extracts_event_from_sqs_body(self, drift_recovery):
        config_event = {'detail': {'configRuleName': 'test-rule'}}
        sqs_event = wrap_in_sqs_event(config_event)
        result = drift_recovery.extract_event_from_sqs(sqs_event)
        assert result == config_event

    def test_returns_original_event_when_no_records(self, drift_recovery):
        direct_event = {'detail': {'configRuleName': 'test-rule'}}
        result = drift_recovery.extract_event_from_sqs(direct_event)
        assert result == direct_event

    def test_returns_original_event_when_records_empty(self, drift_recovery):
        event = {'Records': [], 'detail': {'configRuleName': 'test-rule'}}
        result = drift_recovery.extract_event_from_sqs(event)
        assert result == event

    def test_parses_json_body_correctly(self, drift_recovery):
        nested_event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {'complianceType': 'NON_COMPLIANT'}
            }
        }
        sqs_event = wrap_in_sqs_event(nested_event)
        result = drift_recovery.extract_event_from_sqs(sqs_event)
        assert result['detail']['newEvaluationResult']['complianceType'] == 'NON_COMPLIANT'

    def test_raises_on_invalid_json_body(self, drift_recovery):
        sqs_event = {'Records': [{'body': 'not valid json'}]}
        with pytest.raises(json.JSONDecodeError):
            drift_recovery.extract_event_from_sqs(sqs_event)


class TestGetGitHubToken:
    def test_returns_token_from_ssm(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.return_value = {
                'Parameter': {'Value': 'test-github-token'}
            }
            mock_boto_client.return_value = mock_ssm
            result = drift_recovery.get_github_token()
        assert result == 'test-github-token'

    def test_calls_ssm_with_decryption(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_ssm
            drift_recovery.get_github_token()
            call_args = mock_ssm.get_parameter.call_args
        assert call_args[1]['WithDecryption'] is True

    def test_returns_empty_string_on_client_error(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}},
                'GetParameter'
            )
            mock_boto_client.return_value = mock_ssm
            result = drift_recovery.get_github_token()
        assert result == ''


class TestTriggerApiWorkflow:
    def test_returns_success_on_204_response(self, drift_recovery):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 204
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            result = drift_recovery.trigger_api_workflow('test-token')
        assert result['success'] is True

    def test_returns_failure_on_non_204_response(self, drift_recovery):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 500
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            result = drift_recovery.trigger_api_workflow('test-token')
        assert result['success'] is False

    def test_returns_failure_on_url_error(self, drift_recovery):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection refused')
            result = drift_recovery.trigger_api_workflow('test-token')
        assert result['success'] is False

    def test_returns_failure_on_http_error(self, drift_recovery):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url='https://api.github.com',
                code=401,
                msg='Unauthorized',
                hdrs={},
                fp=None
            )
            result = drift_recovery.trigger_api_workflow('test-token')
        assert result['success'] is False

    def test_includes_error_message_on_failure(self, drift_recovery):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection refused')
            result = drift_recovery.trigger_api_workflow('test-token')
        assert 'error' in result


class TestSendNotification:
    def test_publishes_to_sns_topic(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_sns = MagicMock()
            mock_boto_client.return_value = mock_sns
            drift_recovery.send_notification('Test Subject', 'Test Message')
        assert mock_sns.publish.called

    def test_skips_when_sns_topic_arn_not_configured(self, drift_recovery):
        with patch.dict(os.environ, {'SNS_TOPIC_ARN': ''}):
            with patch('boto3.client') as mock_boto_client:
                mock_sns = MagicMock()
                mock_boto_client.return_value = mock_sns
                drift_recovery.send_notification('Test Subject', 'Test Message')
        assert not mock_sns.publish.called

    def test_handles_sns_publish_error(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.return_value = create_mock_sns_publish_error()
            drift_recovery.send_notification('Test Subject', 'Test Message')


class TestLambdaHandlerDriftTrigger:
    def test_triggers_workflow_on_drift_event(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_ssm
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.status = 204
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response
                response = drift_recovery.lambda_handler(event, lambda_context)
        assert_response_status(response, 200)

    def test_sends_notification_on_successful_trigger(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_client
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.status = 204
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response
                drift_recovery.lambda_handler(event, lambda_context)
        assert mock_client.publish.called


class TestLambdaHandlerGitHubTokenFailure:
    def test_returns_500_when_token_retrieval_fails(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}},
                'GetParameter'
            )
            mock_boto_client.return_value = mock_ssm
            response = drift_recovery.lambda_handler(event, lambda_context)
        assert_response_status(response, 500)

    def test_sends_failure_notification_when_token_fails(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}},
                'GetParameter'
            )
            mock_boto_client.return_value = mock_client
            drift_recovery.lambda_handler(event, lambda_context)
        assert mock_client.publish.called


class TestLambdaHandlerWorkflowTrigger:
    def test_returns_200_on_successful_workflow_trigger(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_ssm
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.status = 204
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response
                response = drift_recovery.lambda_handler(event, lambda_context)
        assert response['body'] == 'Recovery workflow triggered'

    def test_returns_500_on_workflow_trigger_failure(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_ssm
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = urllib.error.URLError('Connection refused')
                response = drift_recovery.lambda_handler(event, lambda_context)
        assert_response_status(response, 500)


class TestLambdaHandlerEventParsing:
    def test_handles_missing_config_rule_name(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({'source': 'drift-recovery-trigger'})
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_ssm
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.status = 204
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response
                response = drift_recovery.lambda_handler(event, lambda_context)
        assert_response_status(response, 200)

    def test_extracts_rule_name_from_event(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'required-tags-rule'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_client
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.status = 204
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response
                drift_recovery.lambda_handler(event, lambda_context)
                call_args = mock_client.publish.call_args
        assert 'required-tags-rule' in call_args[1]['Subject']

    def test_notification_includes_resource_details(self, drift_recovery, lambda_context):
        event = wrap_in_sqs_event({
            'configRuleName': 'required-tags',
            'resourceType': 'AWS::EC2::SecurityGroup',
            'resourceId': 'sg-12345678',
            'awsRegion': 'us-east-1'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_client = MagicMock()
            mock_client.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token'}
            }
            mock_boto_client.return_value = mock_client
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.status = 204
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response
                drift_recovery.lambda_handler(event, lambda_context)
                call_args = mock_client.publish.call_args
        assert 'AWS::EC2::SecurityGroup (sg-12345678) in us-east-1' in call_args[1]['Message']


class TestClientCaching:
    def test_ssm_client_is_cached(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_boto_client.return_value = mock_ssm
            drift_recovery.clear_clients()
            drift_recovery.get_ssm_client()
            drift_recovery.get_ssm_client()
        assert mock_boto_client.call_count == 1

    def test_sns_client_is_cached(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_sns = MagicMock()
            mock_boto_client.return_value = mock_sns
            drift_recovery.clear_clients()
            drift_recovery.get_sns_client()
            drift_recovery.get_sns_client()
        assert mock_boto_client.call_count == 1
