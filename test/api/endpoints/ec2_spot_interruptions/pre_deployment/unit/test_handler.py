"""Unit tests for the EC2 spot interruptions handler."""
import json
from unittest.mock import MagicMock, patch

import pytest


class TestGetEc2InstanceTags:
    """Tests for _get_ec2_instance_tags function."""

    def test_get_ec2_instance_tags_returns_tags(self, handler_module):
        """Returns tags from EC2 describe_instances response."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "Tags": [
                        {"Key": "RunId", "Value": "12345"},
                        {"Key": "GitHubRepo", "Value": "org/repo"},
                    ]
                }]
            }]
        }

        with patch.object(handler_module, '_get_ec2_client', return_value=mock_ec2):
            result = handler_module._get_ec2_instance_tags("i-abc123")

        assert result["RunId"] == "12345"
        assert result["GitHubRepo"] == "org/repo"

    def test_get_ec2_instance_tags_no_reservations_returns_empty(self, handler_module):
        """Returns empty dict when no reservations found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {"Reservations": []}

        with patch.object(handler_module, '_get_ec2_client', return_value=mock_ec2):
            result = handler_module._get_ec2_instance_tags("i-abc123")

        assert result == {}

    def test_get_ec2_instance_tags_client_error_returns_empty(self, handler_module):
        """Returns empty dict on ClientError."""
        from botocore.exceptions import ClientError
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound"}},
            "DescribeInstances"
        )

        with patch.object(handler_module, '_get_ec2_client', return_value=mock_ec2):
            result = handler_module._get_ec2_instance_tags("i-abc123")

        assert result == {}


class TestSendRetryRequest:
    """Tests for _send_retry_request function."""

    def test_send_retry_request_success_returns_true(self, handler_module):
        """Returns True when SQS send succeeds."""
        mock_sqs = MagicMock()

        with patch.object(handler_module, '_get_sqs_client', return_value=mock_sqs):
            result = handler_module._send_retry_request(
                run_id=12345,
                github_repo="org/repo",
                reason="test reason",
                resource_type="ec2",
                resource_id="i-abc123",
            )

        assert result is True
        mock_sqs.send_message.assert_called_once()

    def test_send_retry_request_no_queue_url_returns_false(self, handler_module):
        """Returns False when queue URL not set."""
        with patch.dict('os.environ', {'RETRIES_QUEUE_URL': ''}):
            result = handler_module._send_retry_request(
                run_id=12345,
                github_repo="org/repo",
                reason="test reason",
                resource_type="ec2",
                resource_id="i-abc123",
            )

        assert result is False

    def test_send_retry_request_client_error_returns_false(self, handler_module):
        """Returns False on ClientError."""
        from botocore.exceptions import ClientError
        mock_sqs = MagicMock()
        mock_sqs.send_message.side_effect = ClientError(
            {"Error": {"Code": "InvalidQueueUrl"}},
            "SendMessage"
        )

        with patch.object(handler_module, '_get_sqs_client', return_value=mock_sqs):
            result = handler_module._send_retry_request(
                run_id=12345,
                github_repo="org/repo",
                reason="test reason",
                resource_type="ec2",
                resource_id="i-abc123",
            )

        assert result is False


class TestHandleEc2SpotInterruption:
    """Tests for _handle_ec2_spot_interruption function."""

    def test_handle_ec2_spot_interruption_no_instance_id_returns_400(self, handler_module):
        """Returns 400 when instance-id is missing."""
        event = {"detail": {}}

        result = handler_module._handle_ec2_spot_interruption(event)

        assert result["statusCode"] == 400

    def test_handle_ec2_spot_interruption_no_tags_returns_200(self, handler_module):
        """Returns 200 with handled=False when no tags found."""
        event = {"detail": {"instance-id": "i-abc123"}}

        with patch.object(handler_module, '_get_ec2_instance_tags', return_value={}):
            result = handler_module._handle_ec2_spot_interruption(event)

        assert result["statusCode"] == 200
        assert json.loads(result["body"])["handled"] is False

    def test_handle_ec2_spot_interruption_not_our_runner_returns_200(self, handler_module):
        """Returns 200 with handled=False when not our runner."""
        event = {"detail": {"instance-id": "i-abc123"}}

        with patch.object(
            handler_module,
            '_get_ec2_instance_tags',
            return_value={"Name": "some-other-instance"}
        ):
            result = handler_module._handle_ec2_spot_interruption(event)

        assert result["statusCode"] == 200
        assert json.loads(result["body"])["handled"] is False

    def test_handle_ec2_spot_interruption_our_runner_sends_retry(self, handler_module):
        """Sends retry request when instance is our runner."""
        event = {"detail": {"instance-id": "i-abc123"}}

        with patch.object(
            handler_module,
            '_get_ec2_instance_tags',
            return_value={"RunId": "12345", "GitHubRepo": "org/repo"}
        ):
            with patch.object(handler_module, '_send_retry_request', return_value=True):
                result = handler_module._handle_ec2_spot_interruption(event)

        assert result["statusCode"] == 200
        assert json.loads(result["body"])["handled"] is True


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_lambda_handler_ec2_spot_event_handles_interruption(
        self, handler_module, lambda_context
    ):
        """Handles EC2 spot interruption event."""
        event = {
            "source": "aws.ec2",
            "detail-type": "EC2 Spot Instance Interruption Warning",
            "detail": {"instance-id": "i-abc123"},
        }

        with patch.object(handler_module, '_get_ec2_instance_tags', return_value={}):
            result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200

    def test_lambda_handler_sqs_event_processes_records(
        self, handler_module, lambda_context
    ):
        """Processes SQS records containing EventBridge events."""
        event = {
            "Records": [{
                "body": json.dumps({
                    "source": "aws.ec2",
                    "detail-type": "EC2 Spot Instance Interruption Warning",
                    "detail": {"instance-id": "i-abc123"},
                })
            }]
        }

        with patch.object(handler_module, '_get_ec2_instance_tags', return_value={}):
            result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        assert "results" in json.loads(result["body"])

    def test_lambda_handler_ignores_non_spot_events(
        self, handler_module, lambda_context
    ):
        """Ignores non-spot interruption events."""
        event = {
            "source": "aws.ec2",
            "detail-type": "EC2 Instance State-change Notification",
            "detail": {"instance-id": "i-abc123"},
        }

        result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        assert "ignored" in json.loads(result["body"])["message"].lower()
