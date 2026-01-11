"""Unit tests for ecs_utils module."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from .conftest import load_lambda_module


@pytest.fixture(name="ecs_utils_module")
def ecs_utils_module_fixture():
    """Load ecs_utils module for testing."""
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        module = load_lambda_module("common/ecs_utils.py", "ecs_utils")
        yield module


class TestListRunningTaskArns:
    """Tests for list_running_task_arns function."""

    def test_lists_running_and_pending_tasks(self, ecs_utils_module):
        """Test that both RUNNING and PENDING tasks are listed."""
        mock_ecs = MagicMock()
        mock_paginator = MagicMock()

        # First call for RUNNING status
        running_pages = [{"taskArns": ["arn:task:1", "arn:task:2"]}]
        # Second call for PENDING status
        pending_pages = [{"taskArns": ["arn:task:3"]}]

        def paginate_side_effect(cluster, desiredStatus):
            if desiredStatus == "RUNNING":
                return iter(running_pages)
            return iter(pending_pages)

        mock_paginator.paginate = paginate_side_effect
        mock_ecs.get_paginator.return_value = mock_paginator

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.list_running_task_arns("test-cluster")
            assert len(result) == 3 and set(result) == {"arn:task:1", "arn:task:2", "arn:task:3"}

    def test_handles_empty_results(self, ecs_utils_module):
        """Test handling when no tasks found."""
        mock_ecs = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = iter([{"taskArns": []}])
        mock_ecs.get_paginator.return_value = mock_paginator

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.list_running_task_arns("test-cluster")
            assert result == []

    def test_handles_multiple_pages(self, ecs_utils_module):
        """Test handling pagination with multiple pages."""
        mock_ecs = MagicMock()
        mock_paginator = MagicMock()
        pages = [
            {"taskArns": ["arn:task:1", "arn:task:2"]},
            {"taskArns": ["arn:task:3", "arn:task:4"]},
        ]
        mock_paginator.paginate.return_value = iter(pages)
        mock_ecs.get_paginator.return_value = mock_paginator

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            # This will only get RUNNING tasks since we mock once
            result = ecs_utils_module.list_running_task_arns("test-cluster")
            assert len(result) >= 4


class TestDescribeTasksWithTags:
    """Tests for describe_tasks_with_tags function."""

    def test_describes_tasks_with_tags(self, ecs_utils_module):
        """Test successful task description with tags."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.return_value = {
            "tasks": [
                {"taskArn": "arn:task:1", "tags": [{"key": "Name", "value": "runner-1"}]},
                {"taskArn": "arn:task:2", "tags": []}
            ]
        }
        task_arns = ["arn:task:1", "arn:task:2"]

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.describe_tasks_with_tags("test-cluster", task_arns)
            assert len(result) == 2
            mock_ecs.describe_tasks.assert_called_once_with(
                cluster="test-cluster",
                tasks=task_arns,
                include=["TAGS"]
            )

    def test_handles_empty_task_list(self, ecs_utils_module):
        """Test handling empty task list."""
        mock_ecs = MagicMock()

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.describe_tasks_with_tags("test-cluster", [])
            assert result == []
            mock_ecs.describe_tasks.assert_not_called()

    def test_batches_tasks_in_groups_of_100(self, ecs_utils_module):
        """Test that tasks are batched in groups of 100."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.return_value = {"tasks": []}

        task_arns = [f"arn:task:{i}" for i in range(150)]

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            ecs_utils_module.describe_tasks_with_tags("test-cluster", task_arns)
            # First batch should have 100 tasks, second batch 50 tasks
            calls = mock_ecs.describe_tasks.call_args_list
            call_count_ok = mock_ecs.describe_tasks.call_count == 2
            first_batch_ok = len(calls[0].kwargs["tasks"]) == 100
            second_batch_ok = len(calls[1].kwargs["tasks"]) == 50
            assert call_count_ok and first_batch_ok and second_batch_ok


class TestExtractTaskTags:
    """Tests for extract_task_tags function."""

    def test_extracts_tags_from_task(self, ecs_utils_module):
        """Test extracting tags from task dictionary."""
        task = {
            "taskArn": "arn:task:1",
            "tags": [
                {"key": "Name", "value": "runner-1"},
                {"key": "Environment", "value": "prod"}
            ]
        }
        result = ecs_utils_module.extract_task_tags(task)
        assert result == {"Name": "runner-1", "Environment": "prod"}

    def test_returns_empty_dict_when_no_tags(self, ecs_utils_module):
        """Test returns empty dict when task has no tags."""
        task = {"taskArn": "arn:task:1"}
        result = ecs_utils_module.extract_task_tags(task)
        assert result == {}

    def test_returns_empty_dict_when_tags_empty(self, ecs_utils_module):
        """Test returns empty dict when tags list is empty."""
        task = {"taskArn": "arn:task:1", "tags": []}
        result = ecs_utils_module.extract_task_tags(task)
        assert result == {}


class TestStopEcsTask:
    """Tests for stop_ecs_task function."""

    def test_stops_task_successfully(self, ecs_utils_module):
        """Test successful task stop."""
        mock_ecs = MagicMock()

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.stop_ecs_task(
                "test-cluster", "arn:task:1", "Cleanup"
            )
            assert result is True
            mock_ecs.stop_task.assert_called_once_with(
                cluster="test-cluster",
                task="arn:task:1",
                reason="Cleanup"
            )

    def test_returns_true_when_task_not_found(self, ecs_utils_module):
        """Test returns True when task not found."""
        mock_ecs = MagicMock()
        mock_ecs.stop_task.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "TaskNotFound"}},
            "StopTask"
        )

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.stop_ecs_task(
                "test-cluster", "arn:task:nonexistent", "Cleanup"
            )
            assert result is True

    def test_returns_true_when_task_not_found_in_message(self, ecs_utils_module):
        """Test returns True when TaskNotFound is in error message."""
        mock_ecs = MagicMock()
        mock_ecs.stop_task.side_effect = ClientError(
            {"Error": {"Code": "OtherError", "Message": "TaskNotFound: task does not exist"}},
            "StopTask"
        )

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.stop_ecs_task(
                "test-cluster", "arn:task:nonexistent", "Cleanup"
            )
            assert result is True

    def test_returns_false_on_other_client_error(self, ecs_utils_module):
        """Test returns False on other ClientError."""
        mock_ecs = MagicMock()
        mock_ecs.stop_task.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "StopTask"
        )

        with patch.object(ecs_utils_module, 'get_ecs_client', return_value=mock_ecs):
            result = ecs_utils_module.stop_ecs_task(
                "test-cluster", "arn:task:1", "Cleanup"
            )
            assert result is False


class TestGetClusterFromEnv:
    """Tests for get_cluster_from_env function."""

    def test_returns_cluster_from_env(self, ecs_utils_module):
        """Test returns cluster from environment variable."""
        with patch.dict('os.environ', {'ECS_CLUSTER': 'my-cluster'}):
            result = ecs_utils_module.get_cluster_from_env()
            assert result == "my-cluster"

    def test_returns_empty_string_when_not_set(self, ecs_utils_module):
        """Test returns empty string when env var not set."""
        with patch.dict('os.environ', {}, clear=True):
            result = ecs_utils_module.get_cluster_from_env()
            assert result == ""
