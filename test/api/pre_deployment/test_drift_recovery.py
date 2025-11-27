import json
import os
from unittest.mock import patch, MagicMock, Mock
from test.api.pre_deployment.conftest import (
    assert_response_status,
    create_mock_sns_publish_error
)
from botocore.exceptions import ClientError
import urllib.error


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


class TestLambdaHandlerComplianceFiltering:
    def test_returns_no_action_when_compliant(self, drift_recovery, lambda_context):
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {
                    'complianceType': 'COMPLIANT'
                },
                'resourceId': 'sg-test123'
            }
        }
        response = drift_recovery.lambda_handler(event, lambda_context)
        assert response['body'] == 'No action needed'

    def test_returns_no_action_when_not_applicable(self, drift_recovery, lambda_context):
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {
                    'complianceType': 'NOT_APPLICABLE'
                },
                'resourceId': 'sg-test123'
            }
        }
        response = drift_recovery.lambda_handler(event, lambda_context)
        assert response['body'] == 'No action needed'

    def test_processes_non_compliant_event(self, drift_recovery, lambda_context):
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {
                    'complianceType': 'NON_COMPLIANT'
                },
                'resourceId': 'sg-test123'
            }
        }
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


class TestLambdaHandlerGitHubTokenFailure:
    def test_returns_500_when_token_retrieval_fails(self, drift_recovery, lambda_context):
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {
                    'complianceType': 'NON_COMPLIANT'
                },
                'resourceId': 'sg-test123'
            }
        }
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
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {
                    'complianceType': 'NON_COMPLIANT'
                },
                'resourceId': 'sg-test123'
            }
        }
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
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {
                    'complianceType': 'NON_COMPLIANT'
                },
                'resourceId': 'sg-test123'
            }
        }
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
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'newEvaluationResult': {
                    'complianceType': 'NON_COMPLIANT'
                },
                'resourceId': 'sg-test123'
            }
        }
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
    def test_handles_missing_detail(self, drift_recovery, lambda_context):
        event = {}
        response = drift_recovery.lambda_handler(event, lambda_context)
        assert response['body'] == 'No action needed'

    def test_handles_missing_compliance_type(self, drift_recovery, lambda_context):
        event = {
            'detail': {
                'configRuleName': 'test-rule',
                'resourceId': 'sg-test123'
            }
        }
        response = drift_recovery.lambda_handler(event, lambda_context)
        assert response['body'] == 'No action needed'

    def test_extracts_rule_name_from_event(self, drift_recovery, lambda_context):
        event = {
            'detail': {
                'configRuleName': 'required-tags-rule',
                'newEvaluationResult': {
                    'complianceType': 'NON_COMPLIANT'
                },
                'resourceId': 'sg-test123'
            }
        }
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


class TestClientCaching:
    def test_ssm_client_is_cached(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_boto_client.return_value = mock_ssm
            drift_recovery._clients.clear()
            drift_recovery.get_ssm_client()
            drift_recovery.get_ssm_client()
        assert mock_boto_client.call_count == 1

    def test_sns_client_is_cached(self, drift_recovery):
        with patch('boto3.client') as mock_boto_client:
            mock_sns = MagicMock()
            mock_boto_client.return_value = mock_sns
            drift_recovery._clients.clear()
            drift_recovery.get_sns_client()
            drift_recovery.get_sns_client()
        assert mock_boto_client.call_count == 1
