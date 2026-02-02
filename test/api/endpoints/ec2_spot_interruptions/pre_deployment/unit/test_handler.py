"""Unit tests for the EC2 spot interruptions handler."""
# pylint: disable=duplicate-code
import json
from unittest.mock import MagicMock, patch

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

    def test_handle_ec2_spot_interruption_our_runner_processes_retry(self, handler_module):
        """Processes retry request when instance is our runner."""
        event = {"detail": {"instance-id": "i-abc123"}}

        mock_response = {
            "statusCode": 200,
            "body": json.dumps({"message": "Workflow retry dispatched", "retried": True}),
        }

        with patch.object(
            handler_module,
            '_get_ec2_instance_tags',
            return_value={"RunId": "12345", "GitHubRepo": "org/repo"}
        ):
            with patch.object(handler_module, '_process_retry_request', return_value=mock_response):
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

    def test_lambda_handler_ignores_non_ec2_events(
        self, handler_module, lambda_context
    ):
        """Ignores non-EC2 events."""
        event = {
            "source": "aws.s3",
            "detail-type": "Object Created",
            "detail": {},
        }

        result = handler_module.lambda_handler(event, lambda_context)

        body = json.loads(result["body"])
        assert result["statusCode"] == 200 and "ignored" in body["message"].lower()
