"""Unit tests for test drift recovery."""
import json
import os
import urllib.error
from unittest.mock import patch, MagicMock, Mock

import pytest
from botocore.exceptions import ClientError

from .conftest import assert_response_status, create_mock_sns_publish_error


def wrap_in_sqs_event(config_event):
    """Wrap a config event in an SQS event structure."""
    return {
        'Records': [{
            'messageId': 'test-message-id',
            'body': json.dumps(config_event)
        }]
    }


class TestFormatDriftDetails:
    """Tests for the format_drift_details function."""

    def test_extracts_rule_name(self, drift_recovery):
        """Test extracts rule name."""
        event = {'configRuleName': 'required-tags'}
        result = drift_recovery.format_drift_details(event)
        assert result['rule_name'] == 'required-tags'

    def test_extracts_resource_type(self, drift_recovery):
        """Test extracts resource type."""
        event = {'resourceType': 'AWS::EC2::SecurityGroup'}
        result = drift_recovery.format_drift_details(event)
        assert result['resource_type'] == 'AWS::EC2::SecurityGroup'

    def test_extracts_resource_id(self, drift_recovery):
        """Test extracts resource id."""
        event = {'resourceId': 'sg-12345678'}
        result = drift_recovery.format_drift_details(event)
        assert result['resource_id'] == 'sg-12345678'

    def test_extracts_aws_region(self, drift_recovery):
        """Test extracts aws region."""
        event = {'awsRegion': 'us-east-1'}
        result = drift_recovery.format_drift_details(event)
        assert result['aws_region'] == 'us-east-1'

    def test_formats_summary(self, drift_recovery):
        """Test formats summary."""
        event = {
            'resourceType': 'AWS::EC2::SecurityGroup',
            'resourceId': 'sg-12345678',
            'awsRegion': 'us-east-1'
        }
        result = drift_recovery.format_drift_details(event)
        assert result['summary'] == 'AWS::EC2::SecurityGroup (sg-12345678) in us-east-1'

    def test_uses_unknown_for_missing_rule_name(self, drift_recovery):
        """Test uses unknown for missing rule name."""
        result = drift_recovery.format_drift_details({})
        assert result['rule_name'] == 'Unknown'

    def test_uses_unknown_for_missing_resource_type(self, drift_recovery):
        """Test uses unknown for missing resource type."""
        result = drift_recovery.format_drift_details({})
        assert result['resource_type'] == 'Unknown'

    def test_uses_unknown_for_missing_resource_id(self, drift_recovery):
        """Test uses unknown for missing resource id."""
        result = drift_recovery.format_drift_details({})
        assert result['resource_id'] == 'Unknown'

    def test_uses_unknown_for_missing_aws_region(self, drift_recovery):
        """Test uses unknown for missing aws region."""
        result = drift_recovery.format_drift_details({})
        assert result['aws_region'] == 'Unknown'


class TestExtractEventFromSqs:
    """Tests for the extract_event_from_sqs function."""

    def test_extracts_event_from_sqs_body(self, drift_recovery):
        """Test extracts event from sqs body."""
        config_event = {'detail': {'configRuleName': 'test-rule'}}
        sqs_event = wrap_in_sqs_event(config_event)
        result = drift_recovery.extract_event_from_sqs(sqs_event)
        assert result == config_event

    def test_returns_original_event_when_no_records(self, drift_recovery):
        """Test returns original event when no records."""
        direct_event = {'detail': {'configRuleName': 'test-rule'}}
        result = drift_recovery.extract_event_from_sqs(direct_event)
        assert result == direct_event

    def test_returns_original_event_when_records_empty(self, drift_recovery):
        """Test returns original event when records empty."""
        event = {'Records': [], 'detail': {'configRuleName': 'test-rule'}}
        result = drift_recovery.extract_event_from_sqs(event)
        assert result == event

    def test_parses_json_body_correctly(self, drift_recovery):
        """Test parses json body correctly."""
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
        """Test raises on invalid json body."""
        sqs_event = {'Records': [{'body': 'not valid json'}]}
        with pytest.raises(json.JSONDecodeError):
            drift_recovery.extract_event_from_sqs(sqs_event)


class TestGetGitHubToken:
    """Tests for the get_github_token function."""

    def test_returns_token_from_ssm(self, drift_recovery):
        """Test returns token from ssm."""
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_ssm.get_parameter.return_value = {
                'Parameter': {'Value': 'test-github-token'}
            }
            mock_boto_client.return_value = mock_ssm
            result = drift_recovery.get_github_token()
        assert result == 'test-github-token'

    def test_calls_ssm_with_decryption(self, drift_recovery):
        """Test calls ssm with decryption."""
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
        """Test returns empty string on client error."""
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
    """Tests for the trigger_api_workflow function."""

    def test_returns_success_on_204_response(self, drift_recovery):
        """Test returns success on 204 response."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 204
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            result = drift_recovery.trigger_api_workflow('test-token')
        assert result['success'] is True

    def test_returns_failure_on_non_204_response(self, drift_recovery):
        """Test returns failure on non 204 response."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 500
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            result = drift_recovery.trigger_api_workflow('test-token')
        assert result['success'] is False

    def test_returns_failure_on_url_error(self, drift_recovery):
        """Test returns failure on url error."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection refused')
            result = drift_recovery.trigger_api_workflow('test-token')
        assert result['success'] is False

    def test_returns_failure_on_http_error(self, drift_recovery):
        """Test returns failure on http error."""
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
        """Test includes error message on failure."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection refused')
            result = drift_recovery.trigger_api_workflow('test-token')
        assert 'error' in result


class TestSendNotification:
    """Tests for the send_notification function."""

    def test_publishes_to_sns_topic(self, drift_recovery):
        """Test publishes to sns topic."""
        with patch('boto3.client') as mock_boto_client:
            mock_sns = MagicMock()
            mock_boto_client.return_value = mock_sns
            drift_recovery.send_notification('Test Subject', 'Test Message')
        assert mock_sns.publish.called

    def test_skips_when_sns_topic_arn_not_configured(self, drift_recovery):
        """Test skips when sns topic arn not configured."""
        with patch.dict(os.environ, {'SNS_TOPIC_ARN': ''}):
            with patch('boto3.client') as mock_boto_client:
                mock_sns = MagicMock()
                mock_boto_client.return_value = mock_sns
                drift_recovery.send_notification('Test Subject', 'Test Message')
        assert not mock_sns.publish.called

    def test_handles_sns_publish_error(self, drift_recovery):
        """Test handles sns publish error."""
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.return_value = create_mock_sns_publish_error()
            drift_recovery.send_notification('Test Subject', 'Test Message')


class TestLambdaHandlerDriftTrigger:
    """Tests for lambda handler drift trigger events."""

    def test_triggers_workflow_on_drift_event(self, drift_recovery, lambda_context):
        """Test triggers workflow on drift event."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
        """Test sends notification on successful trigger."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
    """Tests for lambda handler GitHub token failure scenarios."""

    def test_returns_500_when_token_retrieval_fails(self, drift_recovery, lambda_context):
        """Test returns 500 when token retrieval fails."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
        """Test sends failure notification when token fails."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
    """Tests for lambda handler workflow trigger scenarios."""

    def test_returns_200_on_successful_workflow_trigger(self, drift_recovery, lambda_context):
        """Test returns 200 on successful workflow trigger."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
        """Test returns 500 on workflow trigger failure."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
    """Tests for lambda handler event parsing."""

    def test_handles_missing_config_rule_name(self, drift_recovery, lambda_context):
        """Test handles missing config rule name."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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

    def test_extracts_rule_name_from_event(self, drift_recovery, lambda_context):
        """Test extracts rule name from event."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'required-tags-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
        """Test notification includes resource details."""
        event = wrap_in_sqs_event({
            'configRuleName': 'required-tags',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123',
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
        assert 'AWS::EC2::VPC (vpc-managed123) in us-east-1' in call_args[1]['Message']


class TestClientCaching:
    """Tests for client caching behavior."""

    def test_ssm_client_is_cached(self, drift_recovery):
        """Test ssm client is cached."""
        with patch('boto3.client') as mock_boto_client:
            mock_ssm = MagicMock()
            mock_boto_client.return_value = mock_ssm
            drift_recovery.clear_clients()
            drift_recovery.get_ssm_client()
            drift_recovery.get_ssm_client()
        assert mock_boto_client.call_count == 1

    def test_sns_client_is_cached(self, drift_recovery):
        """Test sns client is cached."""
        with patch('boto3.client') as mock_boto_client:
            mock_sns = MagicMock()
            mock_boto_client.return_value = mock_sns
            drift_recovery.clear_clients()
            drift_recovery.get_sns_client()
            drift_recovery.get_sns_client()
        assert mock_boto_client.call_count == 1

    def test_ec2_client_is_cached(self, drift_recovery):
        """Test ec2 client is cached."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            drift_recovery.get_ec2_client()
            drift_recovery.get_ec2_client()
        assert mock_boto_client.call_count == 1


class TestIsResourceInManagedVpc:
    """Tests for the is_resource_in_managed_vpc function."""

    def test_returns_true_for_managed_vpc(self, drift_recovery):
        """Test returns true for managed vpc."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('vpc-managed123', 'AWS::EC2::VPC')
        assert result is True

    def test_returns_false_for_unmanaged_vpc(self, drift_recovery):
        """Test returns false for unmanaged vpc."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('vpc-other456', 'AWS::EC2::VPC')
        assert result is False

    def test_returns_true_for_subnet_in_managed_vpc(self, drift_recovery):
        """Test returns true for subnet in managed vpc."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_subnets.return_value = {
                'Subnets': [{'VpcId': 'vpc-managed123'}]
            }
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('subnet-123', 'AWS::EC2::Subnet')
        assert result is True

    def test_returns_false_for_subnet_in_unmanaged_vpc(self, drift_recovery):
        """Test returns false for subnet in unmanaged vpc."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_subnets.return_value = {
                'Subnets': [{'VpcId': 'vpc-other456'}]
            }
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('subnet-123', 'AWS::EC2::Subnet')
        assert result is False

    def test_returns_true_for_security_group_in_managed_vpc(self, drift_recovery):
        """Test returns true for security group in managed vpc."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-managed123', 'GroupName': 'custom-sg'}]
            }
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('sg-123', 'AWS::EC2::SecurityGroup')
        assert result is True

    def test_returns_false_for_security_group_in_unmanaged_vpc(self, drift_recovery):
        """Test returns false for security group in unmanaged vpc."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-other456', 'GroupName': 'custom-sg'}]
            }
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('sg-123', 'AWS::EC2::SecurityGroup')
        assert result is False

    def test_returns_false_for_default_security_group_in_managed_vpc(self, drift_recovery):
        """Test returns false for default security group in managed vpc."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-managed123', 'GroupName': 'default'}]
            }
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('sg-123', 'AWS::EC2::SecurityGroup')
        assert result is False

    def test_returns_false_when_subnet_not_found(self, drift_recovery):
        """Test returns false when subnet not found."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_subnets.return_value = {'Subnets': []}
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('subnet-missing', 'AWS::EC2::Subnet')
        assert result is False

    def test_returns_false_when_security_group_not_found(self, drift_recovery):
        """Test returns false when security group not found."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_security_groups.return_value = {'SecurityGroups': []}
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            resource_type = 'AWS::EC2::SecurityGroup'
            result = drift_recovery.is_resource_in_managed_vpc('sg-missing', resource_type)
        assert result is False

    def test_returns_false_on_client_error(self, drift_recovery):
        """Test returns false on client error."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ec2.describe_subnets.side_effect = ClientError(
                {'Error': {'Code': 'InvalidSubnetID.NotFound'}},
                'DescribeSubnets'
            )
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('subnet-invalid', 'AWS::EC2::Subnet')
        assert result is False

    def test_returns_true_when_managed_vpc_id_not_configured(self, drift_recovery):
        """Test returns true when managed vpc id not configured."""
        with patch.dict(os.environ, {'MANAGED_VPC_ID': ''}):
            result = drift_recovery.is_resource_in_managed_vpc('vpc-any', 'AWS::EC2::VPC')
        assert result is True

    def test_returns_true_for_unknown_resource_type(self, drift_recovery):
        """Test returns true for unknown resource type."""
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            result = drift_recovery.is_resource_in_managed_vpc('unknown-123', 'AWS::EC2::Unknown')
        assert result is True


class TestLambdaHandlerVpcFiltering:
    """Tests for lambda handler VPC filtering behavior."""

    def test_skips_resource_not_in_managed_vpc(self, drift_recovery, lambda_context):
        """Test skips resource not in managed vpc."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-other456'
        })
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            drift_recovery.clear_clients()
            response = drift_recovery.lambda_handler(event, lambda_context)
        assert response['body'] == 'Resource not in managed VPC, skipping'

    def test_processes_resource_in_managed_vpc(self, drift_recovery, lambda_context):
        """Test processes resource in managed vpc."""
        event = wrap_in_sqs_event({
            'source': 'drift-recovery-trigger',
            'configRuleName': 'test-rule',
            'resourceType': 'AWS::EC2::VPC',
            'resourceId': 'vpc-managed123'
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
