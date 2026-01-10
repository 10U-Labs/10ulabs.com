"""Unit tests for drift_recovery Lambda."""
import json
from unittest.mock import MagicMock, patch

import pytest

from .conftest import load_lambda_module


@pytest.fixture(name="drift_module")
def drift_module_fixture():
    """Load drift_recovery module for testing."""
    env_vars = {
        'MANAGED_VPC_ID': 'vpc-12345',
        'GITHUB_TOKEN_PARAMETER_NAME': '/test/github-token',
        'GITHUB_REPO': 'test-org/test-repo',
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-2:123456789:test-topic',
    }
    with patch.dict('os.environ', env_vars):
        with patch('common.aws_clients.get_ec2_client'):
            with patch('common.aws_clients.get_sns_client'):
                with patch('common.aws_clients.get_ssm_client'):
                    module = load_lambda_module(
                        "drift_recovery.py", "drift_recovery"
                    )
                    yield module


class TestIsResourceInManagedVpc:
    """Tests for _is_resource_in_managed_vpc function."""

    def test_returns_true_when_no_vpc_configured(self, drift_module):
        """Test that True is returned when no managed VPC is configured."""
        with patch.dict('os.environ', {'MANAGED_VPC_ID': ''}):
            result = drift_module._is_resource_in_managed_vpc("resource-123", "AWS::EC2::Instance")
            assert result is True

    def test_returns_true_when_vpc_matches(self, drift_module):
        """Test that True is returned when VPC resource ID matches."""
        result = drift_module._is_resource_in_managed_vpc("vpc-12345", "AWS::EC2::VPC")
        assert result is True

    def test_returns_false_when_vpc_does_not_match(self, drift_module):
        """Test that False is returned when VPC resource ID does not match."""
        result = drift_module._is_resource_in_managed_vpc("vpc-99999", "AWS::EC2::VPC")
        assert result is False

    def test_checks_subnet_vpc_membership(self, drift_module):
        """Test that subnet VPC membership is checked."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            "Subnets": [{"VpcId": "vpc-12345"}]
        }
        with patch.object(drift_module, 'get_ec2_client', return_value=mock_ec2):
            result = drift_module._is_resource_in_managed_vpc("subnet-123", "AWS::EC2::Subnet")
            assert result is True

    def test_returns_false_when_subnet_not_in_vpc(self, drift_module):
        """Test that False is returned when subnet is not in managed VPC."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            "Subnets": [{"VpcId": "vpc-99999"}]
        }
        with patch.object(drift_module, 'get_ec2_client', return_value=mock_ec2):
            result = drift_module._is_resource_in_managed_vpc("subnet-123", "AWS::EC2::Subnet")
            assert result is False

    def test_returns_false_when_subnet_not_found(self, drift_module):
        """Test that False is returned when subnet is not found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {"Subnets": []}
        with patch.object(drift_module, 'get_ec2_client', return_value=mock_ec2):
            result = drift_module._is_resource_in_managed_vpc("subnet-missing", "AWS::EC2::Subnet")
            assert result is False

    def test_checks_security_group_vpc_membership(self, drift_module):
        """Test that security group VPC membership is checked."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [{"VpcId": "vpc-12345", "GroupName": "test-sg"}]
        }
        with patch.object(drift_module, 'get_ec2_client', return_value=mock_ec2):
            result = drift_module._is_resource_in_managed_vpc("sg-123", "AWS::EC2::SecurityGroup")
            assert result is True

    def test_excludes_default_security_group(self, drift_module):
        """Test that default security group is excluded."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [{"VpcId": "vpc-12345", "GroupName": "default"}]
        }
        with patch.object(drift_module, 'get_ec2_client', return_value=mock_ec2):
            result = drift_module._is_resource_in_managed_vpc("sg-default", "AWS::EC2::SecurityGroup")
            assert result is False

    def test_returns_false_when_security_group_not_found(self, drift_module):
        """Test that False is returned when security group is not found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {"SecurityGroups": []}
        with patch.object(drift_module, 'get_ec2_client', return_value=mock_ec2):
            result = drift_module._is_resource_in_managed_vpc("sg-missing", "AWS::EC2::SecurityGroup")
            assert result is False

    def test_returns_false_on_client_error(self, drift_module):
        """Test that False is returned on client error."""
        from botocore.exceptions import ClientError
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "DescribeSubnets"
        )
        with patch.object(drift_module, 'get_ec2_client', return_value=mock_ec2):
            result = drift_module._is_resource_in_managed_vpc("subnet-123", "AWS::EC2::Subnet")
            assert result is False


class TestGetGithubToken:
    """Tests for _get_github_token function."""

    def test_returns_empty_when_param_name_not_set(self, drift_module):
        """Test that empty string is returned when param name is not set."""
        with patch.dict('os.environ', {'GITHUB_TOKEN_PARAMETER_NAME': ''}):
            result = drift_module._get_github_token()
            assert result == ""

    def test_returns_token_from_ssm(self, drift_module):
        """Test that token is retrieved from SSM."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "github-token"}}
        with patch.object(drift_module, 'get_ssm_client', return_value=mock_ssm):
            result = drift_module._get_github_token()
            assert result == "github-token"

    def test_returns_empty_on_client_error(self, drift_module):
        """Test that empty string is returned on client error."""
        from botocore.exceptions import ClientError
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "GetParameter"
        )
        with patch.object(drift_module, 'get_ssm_client', return_value=mock_ssm):
            result = drift_module._get_github_token()
            assert result == ""


class TestTriggerApiWorkflow:
    """Tests for _trigger_api_workflow function."""

    def test_returns_success_on_204_response(self, drift_module):
        """Test that success is returned on 204 response."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = drift_module._trigger_api_workflow("github-token")
            assert result["success"] is True

    def test_returns_error_on_non_204_response(self, drift_module):
        """Test that error is returned on non-204 response."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = drift_module._trigger_api_workflow("github-token")
            assert result["success"] is False

    def test_returns_error_on_http_error(self, drift_module):
        """Test that error is returned on HTTP error."""
        import urllib.error
        with patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=None
        )):
            result = drift_module._trigger_api_workflow("github-token")
            assert result["success"] is False
            assert "403" in result["error"]

    def test_returns_error_on_url_error(self, drift_module):
        """Test that error is returned on URL error."""
        import urllib.error
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Network error")):
            result = drift_module._trigger_api_workflow("github-token")
            assert result["success"] is False


class TestSendNotification:
    """Tests for _send_notification function."""

    def test_sends_notification_to_sns(self, drift_module):
        """Test that notification is sent to SNS."""
        mock_sns = MagicMock()
        with patch.object(drift_module, 'get_sns_client', return_value=mock_sns):
            drift_module._send_notification("Test Subject", "Test message")
            mock_sns.publish.assert_called_once()

    def test_skips_when_topic_not_configured(self, drift_module):
        """Test that notification is skipped when topic is not configured."""
        mock_sns = MagicMock()
        with patch.dict('os.environ', {'SNS_TOPIC_ARN': ''}):
            with patch.object(drift_module, 'get_sns_client', return_value=mock_sns):
                drift_module._send_notification("Subject", "Message")
                mock_sns.publish.assert_not_called()

    def test_handles_client_error_gracefully(self, drift_module):
        """Test that client error is handled gracefully."""
        from botocore.exceptions import ClientError
        mock_sns = MagicMock()
        mock_sns.publish.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "Publish"
        )
        with patch.object(drift_module, 'get_sns_client', return_value=mock_sns):
            # Should not raise
            drift_module._send_notification("Subject", "Message")


class TestExtractEventFromSqs:
    """Tests for _extract_event_from_sqs function."""

    def test_extracts_event_from_sqs_record(self, drift_module):
        """Test that event is extracted from SQS record."""
        sqs_event = {
            "Records": [{"body": json.dumps({"configRuleName": "test-rule"})}]
        }
        result = drift_module._extract_event_from_sqs(sqs_event)
        assert result["configRuleName"] == "test-rule"

    def test_returns_original_event_when_no_records(self, drift_module):
        """Test that original event is returned when no records."""
        event = {"configRuleName": "direct-event"}
        result = drift_module._extract_event_from_sqs(event)
        assert result["configRuleName"] == "direct-event"


class TestFormatDriftDetails:
    """Tests for _format_drift_details function."""

    def test_formats_all_drift_details(self, drift_module):
        """Test that all drift details are formatted."""
        trigger_event = {
            "configRuleName": "test-rule",
            "resourceType": "AWS::EC2::Instance",
            "resourceId": "i-12345",
            "awsRegion": "us-east-2"
        }
        result = drift_module._format_drift_details(trigger_event)
        assert result["rule_name"] == "test-rule"
        assert result["resource_type"] == "AWS::EC2::Instance"
        assert result["resource_id"] == "i-12345"
        assert result["aws_region"] == "us-east-2"

    def test_includes_summary(self, drift_module):
        """Test that summary is included in result."""
        trigger_event = {
            "configRuleName": "rule",
            "resourceType": "AWS::EC2::Instance",
            "resourceId": "i-123",
            "awsRegion": "us-west-2"
        }
        result = drift_module._format_drift_details(trigger_event)
        assert "AWS::EC2::Instance" in result["summary"]
        assert "i-123" in result["summary"]

    def test_handles_missing_fields(self, drift_module):
        """Test that missing fields default to Unknown."""
        trigger_event = {}
        result = drift_module._format_drift_details(trigger_event)
        assert result["rule_name"] == "Unknown"
        assert result["resource_type"] == "Unknown"


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_skips_resource_not_in_managed_vpc(self, drift_module, lambda_context):
        """Test that resource not in managed VPC is skipped."""
        event = {
            "Records": [{"body": json.dumps({
                "configRuleName": "rule",
                "resourceType": "AWS::EC2::VPC",
                "resourceId": "vpc-99999",
                "awsRegion": "us-east-2"
            })}]
        }
        with patch.object(drift_module, '_is_resource_in_managed_vpc', return_value=False):
            result = drift_module.lambda_handler(event, lambda_context)
            assert result["statusCode"] == 200
            assert "not in managed VPC" in result["body"]

    def test_returns_error_when_token_unavailable(self, drift_module, lambda_context):
        """Test that error is returned when token is unavailable."""
        event = {
            "Records": [{"body": json.dumps({
                "configRuleName": "rule",
                "resourceType": "AWS::EC2::Instance",
                "resourceId": "i-123",
                "awsRegion": "us-east-2"
            })}]
        }
        with patch.object(drift_module, '_is_resource_in_managed_vpc', return_value=True):
            with patch.object(drift_module, '_get_github_token', return_value=""):
                with patch.object(drift_module, '_send_notification'):
                    result = drift_module.lambda_handler(event, lambda_context)
                    assert result["statusCode"] == 500

    def test_triggers_workflow_and_sends_notification(self, drift_module, lambda_context):
        """Test that workflow is triggered and notification is sent."""
        event = {
            "Records": [{"body": json.dumps({
                "configRuleName": "rule",
                "resourceType": "AWS::EC2::Instance",
                "resourceId": "i-123",
                "awsRegion": "us-east-2"
            })}]
        }
        with patch.object(drift_module, '_is_resource_in_managed_vpc', return_value=True):
            with patch.object(drift_module, '_get_github_token', return_value="token"):
                with patch.object(drift_module, '_trigger_api_workflow', return_value={"success": True}):
                    with patch.object(drift_module, '_send_notification') as mock_notify:
                        result = drift_module.lambda_handler(event, lambda_context)
                        assert result["statusCode"] == 200
                        mock_notify.assert_called_once()
                        # Check notification is for success
                        call_args = mock_notify.call_args[0]
                        assert "Triggered" in call_args[0]

    def test_sends_failure_notification_on_workflow_error(self, drift_module, lambda_context):
        """Test that failure notification is sent when workflow fails."""
        event = {
            "Records": [{"body": json.dumps({
                "configRuleName": "rule",
                "resourceType": "AWS::EC2::Instance",
                "resourceId": "i-123",
                "awsRegion": "us-east-2"
            })}]
        }
        with patch.object(drift_module, '_is_resource_in_managed_vpc', return_value=True):
            with patch.object(drift_module, '_get_github_token', return_value="token"):
                with patch.object(drift_module, '_trigger_api_workflow', return_value={"success": False, "error": "API error"}):
                    with patch.object(drift_module, '_send_notification') as mock_notify:
                        result = drift_module.lambda_handler(event, lambda_context)
                        assert result["statusCode"] == 500
                        call_args = mock_notify.call_args[0]
                        assert "FAILED" in call_args[0]
