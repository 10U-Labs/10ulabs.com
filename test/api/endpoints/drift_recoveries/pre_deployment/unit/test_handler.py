"""Unit tests for drift recoveries Lambda handler."""
from typing import Any, Dict
from unittest.mock import patch


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
