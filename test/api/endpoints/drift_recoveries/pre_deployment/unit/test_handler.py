"""Unit tests for drift recoveries Lambda handler."""
import urllib.error
from typing import Any, Dict
from unittest.mock import MagicMock, patch


class TestExtractEventFromSqs:
    """Tests for _extract_event_from_sqs function."""

    def test_extracts_body_from_sqs_record(
        self, handler_module, sample_sqs_event: Dict[str, Any]
    ):
        """Extracts body from SQS record."""
        extract_fn = getattr(handler_module, '_extract_event_from_sqs')
        result = extract_fn(sample_sqs_event)
        assert result['configRuleName'] == '10ULabs-required-tags'

    def test_returns_event_when_no_records(
        self, handler_module, sample_direct_event: Dict[str, Any]
    ):
        """Returns original event when no SQS records."""
        extract_fn = getattr(handler_module, '_extract_event_from_sqs')
        result = extract_fn(sample_direct_event)
        assert result == sample_direct_event


class TestFormatDriftDetails:
    """Tests for _format_drift_details function."""

    def test_formats_drift_details(
        self, handler_module, sample_direct_event: Dict[str, Any]
    ):
        """Formats drift details from event."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn(sample_direct_event)
        assert result['rule_name'] == '10ULabs-required-tags'

    def test_includes_resource_type(
        self, handler_module, sample_direct_event: Dict[str, Any]
    ):
        """Includes resource type in formatted details."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn(sample_direct_event)
        assert result['resource_type'] == 'AWS::EC2::Subnet'

    def test_includes_resource_id(
        self, handler_module, sample_direct_event: Dict[str, Any]
    ):
        """Includes resource ID in formatted details."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn(sample_direct_event)
        assert result['resource_id'] == 'subnet-12345678'

    def test_includes_aws_region(
        self, handler_module, sample_direct_event: Dict[str, Any]
    ):
        """Includes AWS region in formatted details."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn(sample_direct_event)
        assert result['aws_region'] == 'us-east-2'

    def test_formats_summary(
        self, handler_module, sample_direct_event: Dict[str, Any]
    ):
        """Formats summary string."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn(sample_direct_event)
        assert 'AWS::EC2::Subnet' in result['summary']


class TestIsResourceInManagedVpc:
    """Tests for _is_resource_in_managed_vpc function."""

    def test_returns_true_when_no_managed_vpc(self, handler_module):
        """Returns True when MANAGED_VPC_ID not configured."""
        with patch.dict('os.environ', {'MANAGED_VPC_ID': ''}):
            check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
            result = check_fn('sg-123', 'AWS::EC2::SecurityGroup')
            assert result is True

    def test_vpc_type_matches_managed_vpc(self, handler_module):
        """Returns True when VPC ID matches managed VPC."""
        check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
        result = check_fn('vpc-12345678', 'AWS::EC2::VPC')
        assert result is True

    def test_vpc_type_does_not_match(self, handler_module):
        """Returns False when VPC ID does not match."""
        check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
        result = check_fn('vpc-other', 'AWS::EC2::VPC')
        assert result is False

    def test_subnet_in_managed_vpc(self, handler_module):
        """Returns True when subnet is in managed VPC."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_subnets.return_value = {
                'Subnets': [{'VpcId': 'vpc-12345678'}]
            }
            check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
            result = check_fn('subnet-123', 'AWS::EC2::Subnet')
            assert result is True

    def test_subnet_not_in_managed_vpc(self, handler_module):
        """Returns False when subnet is not in managed VPC."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_subnets.return_value = {
                'Subnets': [{'VpcId': 'vpc-other'}]
            }
            check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
            result = check_fn('subnet-123', 'AWS::EC2::Subnet')
            assert result is False


class TestGetGithubToken:
    """Tests for _get_github_token function."""

    def test_retrieves_token_from_ssm(self, handler_module):
        """Retrieves GitHub token from SSM Parameter Store."""
        with patch.object(
            handler_module, 'get_ssm_client'
        ) as mock_get_ssm:
            mock_client = mock_get_ssm.return_value
            mock_client.get_parameter.return_value = {
                'Parameter': {'Value': 'test-token-123'}
            }
            get_token_fn = getattr(handler_module, '_get_github_token')
            result = get_token_fn()
            assert result == 'test-token-123'

    def test_returns_empty_when_no_parameter_name(self, handler_module):
        """Returns empty string when parameter name not configured."""
        with patch.dict('os.environ', {'GITHUB_TOKEN_PARAMETER_NAME': ''}):
            get_token_fn = getattr(handler_module, '_get_github_token')
            result = get_token_fn()
            assert result == ''


class TestSendNotification:
    """Tests for _send_notification function."""

    def test_sends_notification_to_sns(self, handler_module):
        """Sends notification to SNS topic."""
        with patch.object(
            handler_module, 'get_sns_client'
        ) as mock_get_sns:
            mock_client = mock_get_sns.return_value
            send_fn = getattr(handler_module, '_send_notification')
            send_fn('Test Subject', 'Test Message')
            assert mock_client.publish.call_count == 1

    def test_skips_when_no_topic_arn(self, handler_module):
        """Skips notification when SNS_TOPIC_ARN not configured."""
        with patch.dict('os.environ', {'SNS_TOPIC_ARN': ''}):
            with patch.object(
                handler_module, 'get_sns_client'
            ) as mock_get_sns:
                mock_client = mock_get_sns.return_value
                send_fn = getattr(handler_module, '_send_notification')
                send_fn('Test Subject', 'Test Message')
                assert mock_client.publish.call_count == 0


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_skips_resource_not_in_managed_vpc(
        self, handler_module, sample_sqs_event, lambda_context
    ):
        """Skips processing when resource not in managed VPC."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-other', 'GroupName': 'test'}]
            }
            result = handler_module.lambda_handler(sample_sqs_event, lambda_context)
            assert result['statusCode'] == 200

    def test_returns_error_when_no_github_token(
        self, handler_module, sample_sqs_event, lambda_context
    ):
        """Returns error when GitHub token not available."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-12345678', 'GroupName': 'test'}]
            }
            with patch.object(
                handler_module, 'get_ssm_client'
            ) as mock_get_ssm:
                mock_ssm = mock_get_ssm.return_value
                mock_ssm.get_parameter.return_value = {
                    'Parameter': {'Value': ''}
                }
                with patch.object(
                    handler_module, 'get_sns_client'
                ):
                    result = handler_module.lambda_handler(
                        sample_sqs_event, lambda_context
                    )
                    assert result['statusCode'] == 500

    def test_triggers_workflow_successfully(
        self, handler_module, sample_sqs_event, lambda_context
    ):
        """Successfully triggers workflow when all conditions met."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-12345678', 'GroupName': 'test'}]
            }
            with patch.object(
                handler_module, 'get_ssm_client'
            ) as mock_get_ssm:
                mock_ssm = mock_get_ssm.return_value
                mock_ssm.get_parameter.return_value = {
                    'Parameter': {'Value': 'test-github-token'}
                }
                with patch.object(handler_module, 'get_sns_client'):
                    with patch(
                        'urllib.request.urlopen'
                    ) as mock_urlopen:
                        mock_response = MagicMock()
                        mock_response.status = 204
                        mock_response.__enter__ = MagicMock(
                            return_value=mock_response
                        )
                        mock_response.__exit__ = MagicMock(return_value=False)
                        mock_urlopen.return_value = mock_response
                        result = handler_module.lambda_handler(
                            sample_sqs_event, lambda_context
                        )
                        assert result['statusCode'] == 200

    def test_returns_error_when_workflow_trigger_fails(
        self, handler_module, sample_sqs_event, lambda_context
    ):
        """Returns error when workflow trigger fails."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-12345678', 'GroupName': 'test'}]
            }
            with patch.object(
                handler_module, 'get_ssm_client'
            ) as mock_get_ssm:
                mock_ssm = mock_get_ssm.return_value
                mock_ssm.get_parameter.return_value = {
                    'Parameter': {'Value': 'test-github-token'}
                }
                with patch.object(handler_module, 'get_sns_client'):
                    with patch(
                        'urllib.request.urlopen'
                    ) as mock_urlopen:
                        mock_urlopen.side_effect = urllib.error.HTTPError(
                            'url', 403, 'Forbidden', {}, None
                        )
                        result = handler_module.lambda_handler(
                            sample_sqs_event, lambda_context
                        )
                        assert result['statusCode'] == 500


class TestTriggerApiWorkflow:
    """Tests for _trigger_api_workflow function."""

    def test_returns_success_on_204_response(self, handler_module):
        """Returns success dict when GitHub returns 204."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 204
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response
            trigger_fn = getattr(handler_module, '_trigger_api_workflow')
            result = trigger_fn('test-token')
            assert result['success'] is True

    def test_returns_failure_on_non_204_status(self, handler_module):
        """Returns failure dict when GitHub returns non-204 status."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response
            trigger_fn = getattr(handler_module, '_trigger_api_workflow')
            result = trigger_fn('test-token')
            assert result['success'] is False

    def test_returns_failure_on_http_error(self, handler_module):
        """Returns failure dict on HTTPError."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                'url', 401, 'Unauthorized', {}, None
            )
            trigger_fn = getattr(handler_module, '_trigger_api_workflow')
            result = trigger_fn('test-token')
            assert result['success'] is False

    def test_includes_http_code_in_error(self, handler_module):
        """Includes HTTP status code in error message."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                'url', 404, 'Not Found', {}, None
            )
            trigger_fn = getattr(handler_module, '_trigger_api_workflow')
            result = trigger_fn('test-token')
            assert '404' in result['error']

    def test_returns_failure_on_url_error(self, handler_module):
        """Returns failure dict on URLError."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection refused')
            trigger_fn = getattr(handler_module, '_trigger_api_workflow')
            result = trigger_fn('test-token')
            assert result['success'] is False

    def test_uses_correct_workflow_file(self, handler_module):
        """Uses api_common_routing.yml as workflow file."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 204
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response
            trigger_fn = getattr(handler_module, '_trigger_api_workflow')
            trigger_fn('test-token')
            call_args = mock_urlopen.call_args[0][0]
            assert 'api_common_routing.yml' in call_args.full_url


class TestIsResourceInManagedVpcErrorHandling:
    """Tests for _is_resource_in_managed_vpc error handling."""

    def test_returns_false_on_client_error(self, handler_module):
        """Returns False when EC2 API call fails."""
        from botocore.exceptions import ClientError
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_subnets.side_effect = ClientError(
                {'Error': {'Code': 'InvalidSubnetID.NotFound'}},
                'DescribeSubnets'
            )
            check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
            result = check_fn('subnet-nonexistent', 'AWS::EC2::Subnet')
            assert result is False

    def test_security_group_returns_false_when_empty(self, handler_module):
        """Returns False when security group not found."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_security_groups.return_value = {
                'SecurityGroups': []
            }
            check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
            result = check_fn('sg-nonexistent', 'AWS::EC2::SecurityGroup')
            assert result is False

    def test_security_group_excludes_default_group(self, handler_module):
        """Returns False for default security group in managed VPC."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-12345678', 'GroupName': 'default'}]
            }
            check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
            result = check_fn('sg-default', 'AWS::EC2::SecurityGroup')
            assert result is False

    def test_security_group_in_managed_vpc(self, handler_module):
        """Returns True for non-default security group in managed VPC."""
        with patch.object(
            handler_module, 'get_ec2_client'
        ) as mock_get_ec2:
            mock_client = mock_get_ec2.return_value
            mock_client.describe_security_groups.return_value = {
                'SecurityGroups': [{'VpcId': 'vpc-12345678', 'GroupName': 'my-sg'}]
            }
            check_fn = getattr(handler_module, '_is_resource_in_managed_vpc')
            result = check_fn('sg-123', 'AWS::EC2::SecurityGroup')
            assert result is True


class TestGetGithubTokenErrorHandling:
    """Tests for _get_github_token error handling."""

    def test_returns_empty_on_client_error(self, handler_module):
        """Returns empty string when SSM API call fails."""
        from botocore.exceptions import ClientError
        with patch.object(
            handler_module, 'get_ssm_client'
        ) as mock_get_ssm:
            mock_client = mock_get_ssm.return_value
            mock_client.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}},
                'GetParameter'
            )
            get_token_fn = getattr(handler_module, '_get_github_token')
            result = get_token_fn()
            assert result == ''


class TestSendNotificationErrorHandling:
    """Tests for _send_notification error handling."""

    def test_handles_sns_publish_error(self, handler_module):
        """Handles error when SNS publish fails."""
        from botocore.exceptions import ClientError
        with patch.object(
            handler_module, 'get_sns_client'
        ) as mock_get_sns:
            mock_client = mock_get_sns.return_value
            mock_client.publish.side_effect = ClientError(
                {'Error': {'Code': 'InvalidParameterValue'}},
                'Publish'
            )
            send_fn = getattr(handler_module, '_send_notification')
            result = send_fn('Test Subject', 'Test Message')
            assert result is None


class TestFormatDriftDetailsEdgeCases:
    """Tests for _format_drift_details edge cases."""

    def test_handles_missing_fields(self, handler_module):
        """Handles event with missing fields gracefully."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn({})
        assert result['rule_name'] == 'Unknown'

    def test_handles_empty_event(self, handler_module):
        """Handles completely empty event."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn({})
        assert result['resource_type'] == 'Unknown'

    def test_handles_partial_event(self, handler_module):
        """Handles event with only some fields."""
        format_fn = getattr(handler_module, '_format_drift_details')
        result = format_fn({'configRuleName': 'test-rule'})
        assert result['rule_name'] == 'test-rule'


class TestExtractEventFromSqsEdgeCases:
    """Tests for _extract_event_from_sqs edge cases."""

    def test_handles_empty_records_list(self, handler_module):
        """Handles event with empty Records list."""
        extract_fn = getattr(handler_module, '_extract_event_from_sqs')
        result = extract_fn({'Records': []})
        assert result == {'Records': []}

    def test_handles_malformed_body(self, handler_module):
        """Handles SQS record with empty body."""
        extract_fn = getattr(handler_module, '_extract_event_from_sqs')
        result = extract_fn({'Records': [{'body': '{}'}]})
        assert result == {}
