"""Unit tests for the EC2 spot interruptions handler."""
import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError


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
            get_tags = getattr(handler_module, '_get_ec2_instance_tags')
            result = get_tags("i-abc123")

        assert (result["RunId"], result["GitHubRepo"]) == ("12345", "org/repo")

    def test_get_ec2_instance_tags_no_reservations_returns_empty(self, handler_module):
        """Returns empty dict when no reservations found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {"Reservations": []}

        with patch.object(handler_module, '_get_ec2_client', return_value=mock_ec2):
            get_tags = getattr(handler_module, '_get_ec2_instance_tags')
            result = get_tags("i-abc123")

        assert result == {}

    def test_get_ec2_instance_tags_client_error_returns_empty(self, handler_module):
        """Returns empty dict on ClientError."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound"}},
            "DescribeInstances"
        )

        with patch.object(handler_module, '_get_ec2_client', return_value=mock_ec2):
            get_tags = getattr(handler_module, '_get_ec2_instance_tags')
            result = get_tags("i-abc123")

        assert result == {}


class TestSendRetryRequest:
    """Tests for _send_retry_request function."""

    @pytest.mark.parametrize("side_effect,expected", [
        (None, True),
        (ClientError({"Error": {"Code": "InvalidQueueUrl"}}, "SendMessage"), False),
    ])
    def test_send_retry_request_with_sqs_client(
        self, handler_module, side_effect, expected
    ):
        """Returns expected result based on SQS send outcome."""
        mock_sqs = MagicMock()
        if side_effect:
            mock_sqs.send_message.side_effect = side_effect

        with patch.object(handler_module, '_get_sqs_client', return_value=mock_sqs):
            send_retry = getattr(handler_module, '_send_retry_request')
            result = send_retry(
                run_id=12345,
                github_repo="org/repo",
                reason="test reason",
                resource_type="ec2",
                resource_id="i-abc123",
            )

        assert result is expected

    def test_send_retry_request_no_queue_url_returns_false(self, handler_module):
        """Returns False when queue URL not set."""
        with patch.dict('os.environ', {'RETRIES_QUEUE_URL': ''}):
            send_retry = getattr(handler_module, '_send_retry_request')
            result = send_retry(
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

        handle_fn = getattr(handler_module, '_handle_ec2_spot_interruption')
        result = handle_fn(event)

        assert result["statusCode"] == 400

    def test_handle_ec2_spot_interruption_no_tags_returns_200(self, handler_module):
        """Returns 200 with handled=False when no tags found."""
        event = {"detail": {"instance-id": "i-abc123"}}

        with patch.object(handler_module, '_get_ec2_instance_tags', return_value={}):
            handle_fn = getattr(handler_module, '_handle_ec2_spot_interruption')
            result = handle_fn(event)

        assert (result["statusCode"], json.loads(result["body"])["handled"]) == (200, False)

    def test_handle_ec2_spot_interruption_not_our_runner_returns_200(self, handler_module):
        """Returns 200 with handled=False when not our runner."""
        event = {"detail": {"instance-id": "i-abc123"}}

        with patch.object(
            handler_module,
            '_get_ec2_instance_tags',
            return_value={"Name": "some-other-instance"}
        ):
            handle_fn = getattr(handler_module, '_handle_ec2_spot_interruption')
            result = handle_fn(event)

        assert (result["statusCode"], json.loads(result["body"])["handled"]) == (200, False)

    def test_handle_ec2_spot_interruption_our_runner_sends_retry(self, handler_module):
        """Sends retry request when instance is our runner."""
        event = {"detail": {"instance-id": "i-abc123"}}

        with patch.object(
            handler_module,
            '_get_ec2_instance_tags',
            return_value={"RunId": "12345", "GitHubRepo": "org/repo"}
        ):
            with patch.object(handler_module, '_send_retry_request', return_value=True):
                handle_fn = getattr(handler_module, '_handle_ec2_spot_interruption')
                result = handle_fn(event)

        body = json.loads(result["body"])
        assert (result["statusCode"], body["handled"]) == (200, True)


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

        body = json.loads(result["body"])
        assert result["statusCode"] == 200 and "results" in body

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

        body = json.loads(result["body"])
        assert result["statusCode"] == 200 and "ignored" in body["message"].lower()
