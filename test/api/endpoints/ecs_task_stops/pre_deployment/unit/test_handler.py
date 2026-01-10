"""Unit tests for the ECS task stops handler."""
import json
from unittest.mock import MagicMock, patch

import pytest


class TestIsSpotInterruption:
    """Tests for _is_spot_interruption function."""

    def test_is_spot_interruption_with_spot_code_returns_true(self, handler_module):
        """Returns True when stopCode contains SpotInterruption."""
        result = handler_module._is_spot_interruption("SpotInterruption", "")

        assert result is True

    def test_is_spot_interruption_with_capacity_reason_returns_true(self, handler_module):
        """Returns True when stoppedReason contains capacity."""
        result = handler_module._is_spot_interruption("", "Insufficient capacity")

        assert result is True

    def test_is_spot_interruption_normal_stop_returns_false(self, handler_module):
        """Returns False for normal task stops."""
        result = handler_module._is_spot_interruption("TaskCompleted", "Container exited")

        assert result is False


class TestGetEcsTaskTags:
    """Tests for _get_ecs_task_tags function."""

    def test_get_ecs_task_tags_returns_tags(self, handler_module):
        """Returns tags from ECS describe_tasks response."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.return_value = {
            "tasks": [{
                "tags": [
                    {"key": "RunId", "value": "12345"},
                    {"key": "GitHubRepo", "value": "org/repo"},
                ]
            }]
        }

        with patch.object(handler_module, '_get_ecs_client', return_value=mock_ecs):
            result = handler_module._get_ecs_task_tags(
                "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "arn:aws:ecs:us-east-2:123456789012:cluster/cluster"
            )

        assert result["RunId"] == "12345"
        assert result["GitHubRepo"] == "org/repo"

    def test_get_ecs_task_tags_no_tasks_returns_empty(self, handler_module):
        """Returns empty dict when no tasks found."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.return_value = {"tasks": []}

        with patch.object(handler_module, '_get_ecs_client', return_value=mock_ecs):
            result = handler_module._get_ecs_task_tags(
                "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "arn:aws:ecs:us-east-2:123456789012:cluster/cluster"
            )

        assert result == {}

    def test_get_ecs_task_tags_client_error_returns_empty(self, handler_module):
        """Returns empty dict on ClientError."""
        from botocore.exceptions import ClientError
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.side_effect = ClientError(
            {"Error": {"Code": "TaskNotFoundException"}},
            "DescribeTasks"
        )

        with patch.object(handler_module, '_get_ecs_client', return_value=mock_ecs):
            result = handler_module._get_ecs_task_tags(
                "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "arn:aws:ecs:us-east-2:123456789012:cluster/cluster"
            )

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
                resource_type="ecs",
                resource_id="arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
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
                resource_type="ecs",
                resource_id="arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
            )

        assert result is False


class TestHandleEcsTaskStopped:
    """Tests for _handle_ecs_task_stopped function."""

    def test_handle_ecs_task_stopped_no_task_arn_returns_400(self, handler_module):
        """Returns 400 when taskArn is missing."""
        event = {"detail": {}}

        result = handler_module._handle_ecs_task_stopped(event)

        assert result["statusCode"] == 400

    def test_handle_ecs_task_stopped_not_spot_returns_200(self, handler_module):
        """Returns 200 with handled=False when not a spot interruption."""
        event = {
            "detail": {
                "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "clusterArn": "arn:aws:ecs:us-east-2:123456789012:cluster/cluster",
                "stopCode": "TaskCompleted",
                "stoppedReason": "Container exited normally",
            }
        }

        result = handler_module._handle_ecs_task_stopped(event)

        assert result["statusCode"] == 200
        assert json.loads(result["body"])["handled"] is False

    def test_handle_ecs_task_stopped_no_tags_returns_200(self, handler_module):
        """Returns 200 with handled=False when no tags found."""
        event = {
            "detail": {
                "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "clusterArn": "arn:aws:ecs:us-east-2:123456789012:cluster/cluster",
                "stopCode": "SpotInterruption",
                "stoppedReason": "Spot capacity reclaimed",
            }
        }

        with patch.object(handler_module, '_get_ecs_task_tags', return_value={}):
            result = handler_module._handle_ecs_task_stopped(event)

        assert result["statusCode"] == 200
        assert json.loads(result["body"])["handled"] is False

    def test_handle_ecs_task_stopped_our_runner_sends_retry(self, handler_module):
        """Sends retry request when task is our runner."""
        event = {
            "detail": {
                "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "clusterArn": "arn:aws:ecs:us-east-2:123456789012:cluster/cluster",
                "stopCode": "SpotInterruption",
                "stoppedReason": "Spot capacity reclaimed",
            }
        }

        with patch.object(
            handler_module,
            '_get_ecs_task_tags',
            return_value={"RunId": "12345", "GitHubRepo": "org/repo"}
        ):
            with patch.object(handler_module, '_send_retry_request', return_value=True):
                result = handler_module._handle_ecs_task_stopped(event)

        assert result["statusCode"] == 200
        assert json.loads(result["body"])["handled"] is True


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_lambda_handler_ecs_task_stopped_event_handles(
        self, handler_module, lambda_context
    ):
        """Handles ECS task stopped event."""
        event = {
            "source": "aws.ecs",
            "detail-type": "ECS Task State Change",
            "detail": {
                "lastStatus": "STOPPED",
                "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "clusterArn": "arn:aws:ecs:us-east-2:123456789012:cluster/cluster",
                "stopCode": "TaskCompleted",
                "stoppedReason": "Normal exit",
            },
        }

        result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200

    def test_lambda_handler_sqs_event_processes_records(
        self, handler_module, lambda_context
    ):
        """Processes SQS records containing EventBridge events."""
        event = {
            "Records": [{
                "body": json.dumps({
                    "source": "aws.ecs",
                    "detail-type": "ECS Task State Change",
                    "detail": {
                        "lastStatus": "STOPPED",
                        "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                        "clusterArn": "arn:aws:ecs:us-east-2:123456789012:cluster/cluster",
                        "stopCode": "TaskCompleted",
                        "stoppedReason": "Normal exit",
                    },
                })
            }]
        }

        result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        assert "results" in json.loads(result["body"])

    def test_lambda_handler_ignores_non_stopped_events(
        self, handler_module, lambda_context
    ):
        """Ignores non-stopped task events."""
        event = {
            "source": "aws.ecs",
            "detail-type": "ECS Task State Change",
            "detail": {
                "lastStatus": "RUNNING",
                "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
            },
        }

        result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        assert "ignored" in json.loads(result["body"])["message"].lower()
