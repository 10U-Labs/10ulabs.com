"""Unit tests for the ECS task stops handler."""
import json
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


class TestIsSpotInterruption:
    """Tests for _is_spot_interruption function."""

    def test_is_spot_interruption_with_spot_code_returns_true(self, handler_module):
        """Returns True when stopCode contains SpotInterruption."""
        is_spot = getattr(handler_module, '_is_spot_interruption')
        result = is_spot("SpotInterruption", "")

        assert result is True

    def test_is_spot_interruption_with_capacity_reason_returns_true(self, handler_module):
        """Returns True when stoppedReason contains capacity."""
        is_spot = getattr(handler_module, '_is_spot_interruption')
        result = is_spot("", "Insufficient capacity")

        assert result is True

    def test_is_spot_interruption_normal_stop_returns_false(self, handler_module):
        """Returns False for normal task stops."""
        is_spot = getattr(handler_module, '_is_spot_interruption')
        result = is_spot("TaskCompleted", "Container exited")

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
            get_tags = getattr(handler_module, '_get_ecs_task_tags')
            result = get_tags(
                "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "arn:aws:ecs:us-east-2:123456789012:cluster/cluster"
            )

        assert (result["RunId"], result["GitHubRepo"]) == ("12345", "org/repo")

    def test_get_ecs_task_tags_no_tasks_returns_empty(self, handler_module):
        """Returns empty dict when no tasks found."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.return_value = {"tasks": []}

        with patch.object(handler_module, '_get_ecs_client', return_value=mock_ecs):
            get_tags = getattr(handler_module, '_get_ecs_task_tags')
            result = get_tags(
                "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "arn:aws:ecs:us-east-2:123456789012:cluster/cluster"
            )

        assert result == {}

    def test_get_ecs_task_tags_client_error_returns_empty(self, handler_module):
        """Returns empty dict on ClientError."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.side_effect = ClientError(
            {"Error": {"Code": "TaskNotFoundException"}},
            "DescribeTasks"
        )

        with patch.object(handler_module, '_get_ecs_client', return_value=mock_ecs):
            get_tags = getattr(handler_module, '_get_ecs_task_tags')
            result = get_tags(
                "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
                "arn:aws:ecs:us-east-2:123456789012:cluster/cluster"
            )

        assert result == {}


ECS_TASK_ARN_SAMPLE = "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123"


class TestSendRetryRequestEcs:
    """Tests for _send_retry_request function in ECS context."""

    def test_sqs_send_succeeds_returns_true(self, handler_module):
        """SQS send_message success returns True."""
        sqs_mock = MagicMock()
        sqs_mock.send_message.return_value = {"MessageId": "msg-123"}

        with patch.object(handler_module, '_get_sqs_client', return_value=sqs_mock):
            fn = getattr(handler_module, '_send_retry_request')
            success = fn(
                run_id=12345, github_repo="org/repo", reason="test reason",
                resource_type="ecs", resource_id=ECS_TASK_ARN_SAMPLE,
            )

        assert success is True
        assert sqs_mock.send_message.call_count == 1

    def test_empty_queue_url_returns_false(self, handler_module):
        """Empty RETRIES_QUEUE_URL environment variable returns False."""
        with patch.dict('os.environ', {'RETRIES_QUEUE_URL': ''}):
            fn = getattr(handler_module, '_send_retry_request')
            success = fn(
                run_id=12345, github_repo="org/repo", reason="test reason",
                resource_type="ecs", resource_id=ECS_TASK_ARN_SAMPLE,
            )

        assert success is False


class TestHandleEcsTaskStopped:
    """Tests for _handle_ecs_task_stopped function."""

    def test_handle_ecs_task_stopped_no_task_arn_returns_400(self, handler_module):
        """Returns 400 when taskArn is missing."""
        event = {"detail": {}}

        handle_fn = getattr(handler_module, '_handle_ecs_task_stopped')
        result = handle_fn(event)

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

        handle_fn = getattr(handler_module, '_handle_ecs_task_stopped')
        result = handle_fn(event)

        assert (result["statusCode"], json.loads(result["body"])["handled"]) == (200, False)

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
            handle_fn = getattr(handler_module, '_handle_ecs_task_stopped')
            result = handle_fn(event)

        assert (result["statusCode"], json.loads(result["body"])["handled"]) == (200, False)

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
                handle_fn = getattr(handler_module, '_handle_ecs_task_stopped')
                result = handle_fn(event)

        body = json.loads(result["body"])
        assert (result["statusCode"], body["handled"]) == (200, True)


class TestEcsLambdaHandler:
    """Tests for ECS task stops lambda_handler function."""

    def test_ecs_task_stopped_event_returns_200(self, handler_module, lambda_context):
        """ECS task stopped event returns 200 status code."""
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

        response = handler_module.lambda_handler(event, lambda_context)

        assert response["statusCode"] == 200

    def test_sqs_wrapped_event_returns_results(self, handler_module, lambda_context):
        """SQS-wrapped EventBridge events return results array."""
        sqs_event = {
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

        response = handler_module.lambda_handler(sqs_event, lambda_context)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "results" in body

    def test_non_stopped_task_ignored(self, handler_module, lambda_context):
        """Non-stopped task events are ignored with appropriate message."""
        event = {
            "source": "aws.ecs",
            "detail-type": "ECS Task State Change",
            "detail": {
                "lastStatus": "RUNNING",
                "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
            },
        }

        response = handler_module.lambda_handler(event, lambda_context)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "ignored" in body["message"].lower()
