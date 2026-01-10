"""Unit tests for the runners cleanup handler."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestIsJobActive:
    """Tests for _is_job_active function."""

    def test_is_job_active_empty_job_id_returns_false(self, handler_module):
        """Returns False when job_id is empty."""
        result = handler_module._is_job_active("token", "org/repo", "")

        assert result is False

    def test_is_job_active_queued_returns_true(self, handler_module):
        """Returns True when job status is queued."""
        with patch.object(
            handler_module,
            '_github_api_request',
            return_value={"status": "queued"}
        ):
            result = handler_module._is_job_active("token", "org/repo", "12345")

        assert result is True

    def test_is_job_active_in_progress_returns_true(self, handler_module):
        """Returns True when job status is in_progress."""
        with patch.object(
            handler_module,
            '_github_api_request',
            return_value={"status": "in_progress"}
        ):
            result = handler_module._is_job_active("token", "org/repo", "12345")

        assert result is True

    def test_is_job_active_completed_returns_false(self, handler_module):
        """Returns False when job status is completed."""
        with patch.object(
            handler_module,
            '_github_api_request',
            return_value={"status": "completed"}
        ):
            result = handler_module._is_job_active("token", "org/repo", "12345")

        assert result is False

    def test_is_job_active_404_returns_false(self, handler_module):
        """Returns False when job is not found."""
        import urllib.error
        with patch.object(
            handler_module,
            '_github_api_request',
            side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)
        ):
            result = handler_module._is_job_active("token", "org/repo", "12345")

        assert result is False


class TestIsOrphanedEcsTask:
    """Tests for _is_orphaned_ecs_task function."""

    def test_is_orphaned_ecs_task_wrong_type_returns_none(self, handler_module):
        """Returns None when task type is not workflow-runner."""
        task = {
            "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
            "tags": [{"key": "Type", "value": "other"}],
        }

        result = handler_module._is_orphaned_ecs_task(task, 1000000)

        assert result is None

    def test_is_orphaned_ecs_task_wrong_managed_by_returns_none(self, handler_module):
        """Returns None when ManagedBy tag is not ecs-runner-api."""
        task = {
            "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "other"},
            ],
        }

        result = handler_module._is_orphaned_ecs_task(task, 1000000)

        assert result is None

    def test_is_orphaned_ecs_task_too_young_returns_none(self, handler_module):
        """Returns None when task is younger than threshold."""
        now = datetime.now(timezone.utc)
        task = {
            "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "ecs-runner-api"},
            ],
            "startedAt": now,
        }

        result = handler_module._is_orphaned_ecs_task(task, now.timestamp())

        assert result is None

    def test_is_orphaned_ecs_task_old_task_returns_info(self, handler_module):
        """Returns orphan info when task is older than threshold."""
        now = datetime.now(timezone.utc)
        old_time = datetime.fromtimestamp(now.timestamp() - 600, timezone.utc)
        task = {
            "taskArn": "arn:aws:ecs:us-east-2:123456789012:task/cluster/task123",
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "ecs-runner-api"},
                {"key": "GitHubJobId", "value": "12345"},
                {"key": "GitHubRepo", "value": "org/repo"},
            ],
            "startedAt": old_time,
        }

        result = handler_module._is_orphaned_ecs_task(task, now.timestamp())

        assert result is not None
        assert result["task_arn"] == task["taskArn"]
        assert result["job_id"] == "12345"


class TestExtractRunIdFromRunnerName:
    """Tests for _extract_run_id_from_runner_name function."""

    def test_extract_run_id_fargate_runner(self, handler_module):
        """Extracts run ID from fargate-runner- prefix."""
        result = handler_module._extract_run_id_from_runner_name("fargate-runner-12345")

        assert result == "12345"

    def test_extract_run_id_ec2_runner(self, handler_module):
        """Extracts run ID from ec2-runner- prefix."""
        result = handler_module._extract_run_id_from_runner_name("ec2-runner-67890")

        assert result == "67890"

    def test_extract_run_id_unknown_prefix(self, handler_module):
        """Returns empty string for unknown prefix."""
        result = handler_module._extract_run_id_from_runner_name("other-runner-12345")

        assert result == ""


class TestRunCleanup:
    """Tests for _run_cleanup function."""

    def test_run_cleanup_returns_result_dict(self, handler_module):
        """Returns result dictionary with cleanup counts."""
        with patch.object(handler_module, '_get_github_token', return_value=''):
            with patch.object(
                handler_module, '_cleanup_orphaned_resources',
                return_value={"ecs_cleaned": 0, "ecs_skipped": 0, "ec2_cleaned": 0, "ec2_skipped": 0, "errors": 0}
            ):
                with patch.object(
                    handler_module, '_cleanup_orphaned_github_runners',
                    return_value={"github_cleaned": 0, "errors": 0}
                ):
                    result = handler_module._run_cleanup()

        assert "orphaned_ecs_cleaned" in result
        assert "orphaned_ec2_cleaned" in result
        assert "orphaned_github_cleaned" in result
        assert "errors" in result


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_lambda_handler_scheduled_event_runs_cleanup(
        self, handler_module, lambda_context
    ):
        """Runs cleanup for scheduled event."""
        event = {"source": "scheduled"}

        with patch.object(
            handler_module, '_run_cleanup',
            return_value={"orphaned_ecs_cleaned": 0, "errors": 0}
        ):
            result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200

    def test_lambda_handler_sqs_event_processes_records(
        self, handler_module, lambda_context
    ):
        """Processes SQS records."""
        event = {
            "Records": [
                {"body": json.dumps({"trigger": "manual"})}
            ]
        }

        with patch.object(
            handler_module, '_run_cleanup',
            return_value={"orphaned_ecs_cleaned": 0, "errors": 0}
        ):
            result = handler_module.lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        assert "results" in json.loads(result["body"])
