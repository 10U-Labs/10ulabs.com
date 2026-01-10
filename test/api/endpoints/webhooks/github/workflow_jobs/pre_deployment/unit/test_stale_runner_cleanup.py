"""Unit tests for stale_runner_cleanup Lambda."""
import time
import urllib.error
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from .conftest import load_lambda_module


@pytest.fixture(name="cleanup_module")
def cleanup_module_fixture():
    """Load stale_runner_cleanup module for testing."""
    env_vars = {
        'GITHUB_REPO': 'test-org/test-repo',
        'ECS_CLUSTER_ARN': 'arn:aws:ecs:us-east-2:123456789:cluster/test',
        'EC2_MANAGED_BY_TAG': 'test-managed-by',
    }
    with patch.dict('os.environ', env_vars):
        with patch('common.aws_clients.get_ssm_client'):
            with patch('common.aws_clients.get_ec2_client'):
                with patch('common.aws_clients.get_ecs_client'):
                    module = load_lambda_module(
                        "stale_runner_cleanup.py", "stale_runner_cleanup"
                    )
                    yield module


@contextmanager
def cleanup_test_context(
    module: Any,
    ecs_tasks: list[dict[str, Any]],
    ec2_instances: list[dict[str, Any]],
    is_active: bool
) -> Iterator[dict[str, MagicMock]]:
    """Context manager for cleanup tests with common mock setup."""
    with patch.object(module, 'get_orphaned_ecs_tasks', return_value=ecs_tasks):
        with patch.object(module, 'get_orphaned_ec2_instances',
                          return_value=ec2_instances):
            with patch.object(module, 'is_job_active',
                              return_value=is_active) as mock_active:
                with patch.object(module, 'terminate_ecs_task',
                                  return_value=True) as mock_terminate_ecs:
                    with patch.object(module, 'terminate_ec2_instance',
                                      return_value=True) as mock_terminate_ec2:
                        yield {
                            'is_active': mock_active,
                            'terminate_ecs': mock_terminate_ecs,
                            'terminate_ec2': mock_terminate_ec2
                        }


class TestIsJobActive:
    """Tests for is_job_active function."""

    def test_returns_true_when_job_is_in_progress(self, cleanup_module):
        """Test that in-progress jobs are correctly identified as active."""
        with patch.object(
            cleanup_module,
            'github_api_request',
            return_value={"status": "in_progress"}
        ):
            result = cleanup_module.is_job_active(
                "test-token", "test-org/test-repo", "12345"
            )
            assert result is True

    def test_returns_true_when_job_is_queued(self, cleanup_module):
        """Test that queued jobs are correctly identified as active."""
        with patch.object(
            cleanup_module,
            'github_api_request',
            return_value={"status": "queued"}
        ):
            result = cleanup_module.is_job_active(
                "test-token", "test-org/test-repo", "12345"
            )
            assert result is True

    def test_returns_false_when_job_is_completed(self, cleanup_module):
        """Test that completed jobs are correctly identified as inactive."""
        with patch.object(
            cleanup_module,
            'github_api_request',
            return_value={"status": "completed"}
        ):
            result = cleanup_module.is_job_active(
                "test-token", "test-org/test-repo", "12345"
            )
            assert result is False

    def test_returns_false_when_job_not_found(self, cleanup_module):
        """Test that 404 errors return False (job not active)."""
        error = urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )
        with patch.object(
            cleanup_module,
            'github_api_request',
            side_effect=error
        ):
            result = cleanup_module.is_job_active(
                "test-token", "test-org/test-repo", "12345"
            )
            assert result is False

    def test_returns_true_when_api_fails(self, cleanup_module):
        """Test that non-404 API failures default to active (safe behavior)."""
        error = urllib.error.HTTPError(
            url="", code=500, msg="Server Error", hdrs={}, fp=None
        )
        with patch.object(
            cleanup_module,
            'github_api_request',
            side_effect=error
        ):
            result = cleanup_module.is_job_active(
                "test-token", "test-org/test-repo", "12345"
            )
            assert result is True

    def test_returns_false_when_job_id_empty(self, cleanup_module):
        """Test that empty job_id returns False."""
        result = cleanup_module.is_job_active(
            "test-token", "test-org/test-repo", ""
        )
        assert result is False

    def test_returns_false_when_status_field_missing(self, cleanup_module):
        """Test that missing status field defaults to False."""
        with patch.object(
            cleanup_module,
            'github_api_request',
            return_value={}
        ):
            result = cleanup_module.is_job_active(
                "test-token", "test-org/test-repo", "12345"
            )
            assert result is False


class TestCleanupOrphanedResourcesSkipsActiveJobs:
    """Tests that cleanup skips resources with active jobs."""

    def test_active_job_ecs_task_checks_job_status(self, cleanup_module):
        """Test that job status check is called for ECS tasks."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [mock_task], [],
                                  is_active=True) as mocks:
            cleanup_module.cleanup_orphaned_resources("test-token")
            mocks['is_active'].assert_called_once_with(
                "test-token", "test-org/test-repo", "12345"
            )
        assert True  # Explicit pass

    def test_active_job_ecs_task_is_not_terminated(self, cleanup_module):
        """Test that ECS tasks with active jobs are not terminated."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [mock_task], [],
                                  is_active=True) as mocks:
            cleanup_module.cleanup_orphaned_resources("test-token")
            mocks['terminate_ecs'].assert_not_called()
        assert True  # Explicit pass

    def test_active_job_ecs_task_returns_skipped_count(self, cleanup_module):
        """Test that ECS tasks with active jobs are counted as skipped."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [mock_task], [],
                                  is_active=True):
            result = cleanup_module.cleanup_orphaned_resources("test-token")
            assert (result["ecs_skipped"], result["ecs_cleaned"]) == (1, 0)

    def test_inactive_job_ecs_task_is_terminated(self, cleanup_module):
        """Test that ECS tasks with inactive jobs are terminated."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [mock_task], [],
                                  is_active=False) as mocks:
            cleanup_module.cleanup_orphaned_resources("test-token")
            mocks['terminate_ecs'].assert_called_once()
        assert True  # Explicit pass

    def test_inactive_job_ecs_task_returns_cleaned_count(self, cleanup_module):
        """Test that ECS tasks with inactive jobs are counted as cleaned."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [mock_task], [],
                                  is_active=False):
            result = cleanup_module.cleanup_orphaned_resources("test-token")
            assert (result["ecs_cleaned"], result["ecs_skipped"]) == (1, 0)

    def test_active_job_ec2_instance_checks_job_status(self, cleanup_module):
        """Test that job status check is called for EC2 instances."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [], [mock_instance],
                                  is_active=True) as mocks:
            cleanup_module.cleanup_orphaned_resources("test-token")
            mocks['is_active'].assert_called_once_with(
                "test-token", "test-org/test-repo", "12345"
            )
        assert True  # Explicit pass

    def test_active_job_ec2_instance_is_not_terminated(self, cleanup_module):
        """Test that EC2 instances with active jobs are not terminated."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [], [mock_instance],
                                  is_active=True) as mocks:
            cleanup_module.cleanup_orphaned_resources("test-token")
            mocks['terminate_ec2'].assert_not_called()
        assert True  # Explicit pass

    def test_active_job_ec2_instance_returns_skipped_count(self, cleanup_module):
        """Test that EC2 instances with active jobs are counted as skipped."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [], [mock_instance],
                                  is_active=True):
            result = cleanup_module.cleanup_orphaned_resources("test-token")
            assert (result["ec2_skipped"], result["ec2_cleaned"]) == (1, 0)

    def test_inactive_job_ec2_instance_is_terminated(self, cleanup_module):
        """Test that EC2 instances with inactive jobs are terminated."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [], [mock_instance],
                                  is_active=False) as mocks:
            cleanup_module.cleanup_orphaned_resources("test-token")
            mocks['terminate_ec2'].assert_called_once_with("i-1234567890abcdef0")
        assert True  # Explicit pass

    def test_inactive_job_ec2_instance_returns_cleaned_count(self, cleanup_module):
        """Test that EC2 instances with inactive jobs are counted as cleaned."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "job_id": "12345",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(cleanup_module, [], [mock_instance],
                                  is_active=False):
            result = cleanup_module.cleanup_orphaned_resources("test-token")
            assert (result["ec2_cleaned"], result["ec2_skipped"]) == (1, 0)


class TestGetAllGithubRunners:
    """Tests for get_all_github_runners function."""

    def test_returns_runners_single_page(self, cleanup_module):
        """Test that runners are returned for single page response."""
        mock_runners = [{"id": 1, "name": "runner-1"}, {"id": 2, "name": "runner-2"}]
        with patch.object(
            cleanup_module,
            'github_api_request',
            return_value={"runners": mock_runners}
        ):
            result = cleanup_module.get_all_github_runners(
                "test-token", "test-org/test-repo"
            )
            assert result == mock_runners

    def test_returns_runners_multiple_pages(self, cleanup_module):
        """Test pagination when there are more than 100 runners."""
        page1_runners = [{"id": i, "name": f"runner-{i}"} for i in range(100)]
        page2_runners = [{"id": 100, "name": "runner-100"}]

        call_count = [0]

        def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"runners": page1_runners}
            return {"runners": page2_runners}

        with patch.object(cleanup_module, 'github_api_request', side_effect=mock_request):
            result = cleanup_module.get_all_github_runners(
                "test-token", "test-org/test-repo"
            )
            assert len(result) == 101
            assert call_count[0] == 2

    def test_returns_none_on_http_error(self, cleanup_module):
        """Test that HTTPError returns None."""
        error = urllib.error.HTTPError(
            url="", code=500, msg="Server Error", hdrs={}, fp=None
        )
        with patch.object(cleanup_module, 'github_api_request', side_effect=error):
            result = cleanup_module.get_all_github_runners(
                "test-token", "test-org/test-repo"
            )
            assert result is None

    def test_returns_empty_list_when_no_runners(self, cleanup_module):
        """Test that empty list is returned when no runners exist."""
        with patch.object(
            cleanup_module,
            'github_api_request',
            return_value={"runners": []}
        ):
            result = cleanup_module.get_all_github_runners(
                "test-token", "test-org/test-repo"
            )
            assert result == []


class TestDeleteGithubRunnerById:
    """Tests for delete_github_runner_by_id function."""

    def test_returns_true_on_success(self, cleanup_module):
        """Test that successful deletion returns True."""
        with patch.object(cleanup_module, 'github_api_request', return_value=None):
            result = cleanup_module.delete_github_runner_by_id(
                "test-token", "test-org/test-repo", 123, "runner-1"
            )
            assert result is True

    def test_returns_true_on_204_response(self, cleanup_module):
        """Test that 204 response (No Content) returns True."""
        error = urllib.error.HTTPError(
            url="", code=204, msg="No Content", hdrs={}, fp=None
        )
        with patch.object(cleanup_module, 'github_api_request', side_effect=error):
            result = cleanup_module.delete_github_runner_by_id(
                "test-token", "test-org/test-repo", 123, "runner-1"
            )
            assert result is True

    def test_returns_false_on_error(self, cleanup_module):
        """Test that other HTTP errors return False."""
        error = urllib.error.HTTPError(
            url="", code=500, msg="Server Error", hdrs={}, fp=None
        )
        with patch.object(cleanup_module, 'github_api_request', side_effect=error):
            result = cleanup_module.delete_github_runner_by_id(
                "test-token", "test-org/test-repo", 123, "runner-1"
            )
            assert result is False


class TestTerminateEcsTask:
    """Tests for terminate_ecs_task function."""

    def test_returns_true_on_success(self, cleanup_module):
        """Test that successful termination returns True."""
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            with patch.object(cleanup_module, 'stop_ecs_task', return_value=True):
                result = cleanup_module.terminate_ecs_task("arn:aws:ecs:test:task")
                assert result is True

    def test_returns_false_when_no_cluster(self, cleanup_module):
        """Test that missing cluster returns False."""
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value=None):
            result = cleanup_module.terminate_ecs_task("arn:aws:ecs:test:task")
            assert result is False


class TestIsOrphanedEcsTask:
    """Tests for is_orphaned_ecs_task function."""

    def test_returns_none_when_wrong_type(self, cleanup_module):
        """Test that tasks with wrong Type tag return None."""
        task = {
            "tags": [
                {"key": "Type", "value": "other-type"},
                {"key": "ManagedBy", "value": "ecs-runner-api"},
            ],
            "startedAt": datetime.now(timezone.utc),
        }
        result = cleanup_module.is_orphaned_ecs_task(task, time.time())
        assert result is None

    def test_returns_none_when_wrong_managed_by(self, cleanup_module):
        """Test that tasks with wrong ManagedBy tag return None."""
        task = {
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "other-manager"},
            ],
            "startedAt": datetime.now(timezone.utc),
        }
        result = cleanup_module.is_orphaned_ecs_task(task, time.time())
        assert result is None

    def test_returns_none_when_no_started_at(self, cleanup_module):
        """Test that tasks without startedAt return None."""
        task = {
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "ecs-runner-api"},
            ],
        }
        result = cleanup_module.is_orphaned_ecs_task(task, time.time())
        assert result is None

    def test_returns_none_when_too_young(self, cleanup_module):
        """Test that young tasks return None."""
        current_time = time.time()
        task = {
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "ecs-runner-api"},
            ],
            "startedAt": datetime.fromtimestamp(current_time - 60, tz=timezone.utc),
            "taskArn": "arn:aws:ecs:test:task/abc",
        }
        result = cleanup_module.is_orphaned_ecs_task(task, current_time)
        assert result is None

    def test_returns_orphan_info_for_old_task(self, cleanup_module):
        """Test that old tasks return orphan info."""
        current_time = time.time()
        # Use 610 seconds to avoid timing edge cases
        task = {
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "ecs-runner-api"},
                {"key": "GitHubJobId", "value": "12345"},
                {"key": "GitHubRepo", "value": "test-org/test-repo"},
            ],
            "startedAt": datetime.fromtimestamp(current_time - 610, tz=timezone.utc),
            "taskArn": "arn:aws:ecs:test:task/abc",
        }
        result = cleanup_module.is_orphaned_ecs_task(task, current_time)
        assert result is not None
        assert result["task_arn"] == "arn:aws:ecs:test:task/abc"
        assert result["job_id"] == "12345"
        assert result["github_repo"] == "test-org/test-repo"
        assert result["age_seconds"] >= 600


class TestGetOrphanedEcsTasks:
    """Tests for get_orphaned_ecs_tasks function."""

    def test_returns_empty_when_no_cluster(self, cleanup_module):
        """Test that missing cluster returns empty list."""
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value=None):
            result = cleanup_module.get_orphaned_ecs_tasks()
            assert result == []

    def test_returns_empty_when_no_tasks(self, cleanup_module):
        """Test that no running tasks returns empty list."""
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            with patch.object(cleanup_module, 'list_running_task_arns', return_value=[]):
                result = cleanup_module.get_orphaned_ecs_tasks()
                assert result == []

    def test_returns_orphaned_tasks(self, cleanup_module):
        """Test that orphaned tasks are returned."""
        current_time = time.time()
        mock_task = {
            "tags": [
                {"key": "Type", "value": "workflow-runner"},
                {"key": "ManagedBy", "value": "ecs-runner-api"},
                {"key": "GitHubJobId", "value": "12345"},
            ],
            "startedAt": datetime.fromtimestamp(current_time - 600, tz=timezone.utc),
            "taskArn": "arn:aws:ecs:test:task/abc",
        }
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            with patch.object(cleanup_module, 'list_running_task_arns', return_value=['arn:test']):
                with patch.object(cleanup_module, 'describe_tasks_with_tags', return_value=[mock_task]):
                    result = cleanup_module.get_orphaned_ecs_tasks()
                    assert len(result) == 1
                    assert result[0]["task_arn"] == "arn:aws:ecs:test:task/abc"

    def test_handles_client_error(self, cleanup_module):
        """Test that ClientError is handled gracefully."""
        error = ClientError({"Error": {"Code": "500", "Message": "Error"}}, "ListTasks")
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            with patch.object(cleanup_module, 'list_running_task_arns', side_effect=error):
                result = cleanup_module.get_orphaned_ecs_tasks()
                assert result == []


class TestGetOrphanedEc2Instances:
    """Tests for get_orphaned_ec2_instances function."""

    def test_returns_empty_when_no_tag_configured(self, cleanup_module):
        """Test that missing EC2_MANAGED_BY_TAG returns empty list."""
        with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': ''}):
            result = cleanup_module.get_orphaned_ec2_instances()
            assert result == []

    def test_returns_orphaned_instances(self, cleanup_module):
        """Test that orphaned instances are returned."""
        current_time = time.time()
        mock_response = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-1234567890abcdef0",
                    "LaunchTime": datetime.fromtimestamp(current_time - 600, tz=timezone.utc),
                    "Tags": [
                        {"Key": "GitHubJobId", "Value": "12345"},
                        {"Key": "GitHubRepo", "Value": "test-org/test-repo"},
                    ],
                }]
            }]
        }
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = mock_response

        with patch.object(cleanup_module, 'get_ec2_client', return_value=mock_ec2):
            result = cleanup_module.get_orphaned_ec2_instances()
            assert len(result) == 1
            assert result[0]["instance_id"] == "i-1234567890abcdef0"

    def test_skips_young_instances(self, cleanup_module):
        """Test that young instances are skipped."""
        current_time = time.time()
        mock_response = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-1234567890abcdef0",
                    "LaunchTime": datetime.fromtimestamp(current_time - 60, tz=timezone.utc),
                    "Tags": [],
                }]
            }]
        }
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = mock_response

        with patch.object(cleanup_module, 'get_ec2_client', return_value=mock_ec2):
            result = cleanup_module.get_orphaned_ec2_instances()
            assert result == []

    def test_handles_client_error(self, cleanup_module):
        """Test that ClientError is handled gracefully."""
        error = ClientError({"Error": {"Code": "500", "Message": "Error"}}, "DescribeInstances")
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = error

        with patch.object(cleanup_module, 'get_ec2_client', return_value=mock_ec2):
            result = cleanup_module.get_orphaned_ec2_instances()
            assert result == []


class TestExtractRunIdFromRunnerName:
    """Tests for extract_run_id_from_runner_name function."""

    def test_extracts_fargate_run_id(self, cleanup_module):
        """Test extraction from fargate runner name."""
        result = cleanup_module.extract_run_id_from_runner_name("fargate-runner-12345")
        assert result == "12345"

    def test_extracts_ec2_run_id(self, cleanup_module):
        """Test extraction from ec2 runner name."""
        result = cleanup_module.extract_run_id_from_runner_name("ec2-runner-67890")
        assert result == "67890"

    def test_returns_empty_for_unknown_format(self, cleanup_module):
        """Test that unknown formats return empty string."""
        result = cleanup_module.extract_run_id_from_runner_name("other-runner-name")
        assert result == ""


class TestHasRunningEc2ByName:
    """Tests for has_running_ec2_by_name function."""

    def test_returns_true_when_instance_exists(self, cleanup_module):
        """Test that True is returned when instance exists."""
        mock_response = {
            "Reservations": [{"Instances": [{"InstanceId": "i-123"}]}]
        }
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = mock_response

        with patch.object(cleanup_module, 'get_ec2_client', return_value=mock_ec2):
            result = cleanup_module.has_running_ec2_by_name("runner-name")
            assert result is True

    def test_returns_false_when_no_instance(self, cleanup_module):
        """Test that False is returned when no instance exists."""
        mock_response = {"Reservations": []}
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = mock_response

        with patch.object(cleanup_module, 'get_ec2_client', return_value=mock_ec2):
            result = cleanup_module.has_running_ec2_by_name("runner-name")
            assert result is False

    def test_returns_false_when_no_tag_configured(self, cleanup_module):
        """Test that False is returned when EC2_MANAGED_BY_TAG is not set."""
        with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': ''}):
            result = cleanup_module.has_running_ec2_by_name("runner-name")
            assert result is False

    def test_handles_client_error(self, cleanup_module):
        """Test that ClientError returns False."""
        error = ClientError({"Error": {"Code": "500", "Message": "Error"}}, "DescribeInstances")
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = error

        with patch.object(cleanup_module, 'get_ec2_client', return_value=mock_ec2):
            result = cleanup_module.has_running_ec2_by_name("runner-name")
            assert result is False


class TestHasRunningEcsTaskByName:
    """Tests for has_running_ecs_task_by_name function."""

    def test_returns_true_when_task_exists(self, cleanup_module):
        """Test that True is returned when matching task exists."""
        mock_task = {"tags": [{"key": "RunId", "value": "12345"}]}
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            with patch.object(cleanup_module, 'list_running_task_arns', return_value=['arn:test']):
                with patch.object(cleanup_module, 'describe_tasks_with_tags', return_value=[mock_task]):
                    with patch.object(cleanup_module, 'extract_task_tags',
                                      return_value={"RunId": "12345"}):
                        result = cleanup_module.has_running_ecs_task_by_name("fargate-runner-12345")
                        assert result is True

    def test_returns_false_when_no_matching_task(self, cleanup_module):
        """Test that False is returned when no matching task."""
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            with patch.object(cleanup_module, 'list_running_task_arns', return_value=['arn:test']):
                with patch.object(cleanup_module, 'describe_tasks_with_tags', return_value=[]):
                    result = cleanup_module.has_running_ecs_task_by_name("fargate-runner-12345")
                    assert result is False

    def test_returns_false_when_no_cluster(self, cleanup_module):
        """Test that False is returned when no cluster configured."""
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value=None):
            result = cleanup_module.has_running_ecs_task_by_name("fargate-runner-12345")
            assert result is False

    def test_returns_false_when_no_run_id(self, cleanup_module):
        """Test that False is returned when run_id cannot be extracted."""
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            result = cleanup_module.has_running_ecs_task_by_name("unknown-runner-name")
            assert result is False

    def test_handles_client_error(self, cleanup_module):
        """Test that ClientError returns False."""
        error = ClientError({"Error": {"Code": "500", "Message": "Error"}}, "ListTasks")
        with patch.object(cleanup_module, 'get_cluster_from_env', return_value='test-cluster'):
            with patch.object(cleanup_module, 'list_running_task_arns', side_effect=error):
                result = cleanup_module.has_running_ecs_task_by_name("fargate-runner-12345")
                assert result is False


class TestRunnerHasInfrastructure:
    """Tests for runner_has_infrastructure function."""

    def test_returns_true_when_ec2_exists(self, cleanup_module):
        """Test that True is returned when EC2 exists."""
        with patch.object(cleanup_module, 'has_running_ec2_by_name', return_value=True):
            result = cleanup_module.runner_has_infrastructure("ec2-runner-123")
            assert result is True

    def test_returns_true_when_ecs_exists(self, cleanup_module):
        """Test that True is returned when ECS exists."""
        with patch.object(cleanup_module, 'has_running_ec2_by_name', return_value=False):
            with patch.object(cleanup_module, 'has_running_ecs_task_by_name', return_value=True):
                result = cleanup_module.runner_has_infrastructure("fargate-runner-123")
                assert result is True

    def test_returns_false_when_no_infrastructure(self, cleanup_module):
        """Test that False is returned when neither exists."""
        with patch.object(cleanup_module, 'has_running_ec2_by_name', return_value=False):
            with patch.object(cleanup_module, 'has_running_ecs_task_by_name', return_value=False):
                result = cleanup_module.runner_has_infrastructure("runner-123")
                assert result is False


class TestCleanupOrphanedGithubRunners:
    """Tests for cleanup_orphaned_github_runners function."""

    def test_returns_error_when_no_github_repo(self, cleanup_module):
        """Test that error is returned when GITHUB_REPO not set."""
        with patch.dict('os.environ', {'GITHUB_REPO': ''}):
            result = cleanup_module.cleanup_orphaned_github_runners("test-token")
            assert result["errors"] == 1
            assert result["github_cleaned"] == 0

    def test_returns_error_when_no_token(self, cleanup_module):
        """Test that error is returned when token is empty."""
        result = cleanup_module.cleanup_orphaned_github_runners("")
        assert result["errors"] == 1

    def test_returns_error_when_api_fails(self, cleanup_module):
        """Test that error is returned when API returns None."""
        with patch.object(cleanup_module, 'get_all_github_runners', return_value=None):
            result = cleanup_module.cleanup_orphaned_github_runners("test-token")
            assert result["errors"] == 1

    def test_skips_online_runners(self, cleanup_module):
        """Test that online runners are skipped."""
        runners = [{"id": 1, "name": "runner-1", "status": "online"}]
        with patch.object(cleanup_module, 'get_all_github_runners', return_value=runners):
            with patch.object(cleanup_module, 'delete_github_runner_by_id') as mock_delete:
                result = cleanup_module.cleanup_orphaned_github_runners("test-token")
                mock_delete.assert_not_called()
                assert result["github_cleaned"] == 0

    def test_skips_runners_with_infrastructure(self, cleanup_module):
        """Test that runners with infrastructure are skipped."""
        runners = [{"id": 1, "name": "runner-1", "status": "offline"}]
        with patch.object(cleanup_module, 'get_all_github_runners', return_value=runners):
            with patch.object(cleanup_module, 'runner_has_infrastructure', return_value=True):
                with patch.object(cleanup_module, 'delete_github_runner_by_id') as mock_delete:
                    result = cleanup_module.cleanup_orphaned_github_runners("test-token")
                    mock_delete.assert_not_called()
                    assert result["github_cleaned"] == 0

    def test_deletes_orphaned_runners(self, cleanup_module):
        """Test that orphaned runners are deleted."""
        runners = [{"id": 1, "name": "runner-1", "status": "offline"}]
        with patch.object(cleanup_module, 'get_all_github_runners', return_value=runners):
            with patch.object(cleanup_module, 'runner_has_infrastructure', return_value=False):
                with patch.object(cleanup_module, 'delete_github_runner_by_id', return_value=True):
                    result = cleanup_module.cleanup_orphaned_github_runners("test-token")
                    assert result["github_cleaned"] == 1
                    assert result["errors"] == 0

    def test_counts_delete_errors(self, cleanup_module):
        """Test that delete errors are counted."""
        runners = [{"id": 1, "name": "runner-1", "status": "offline"}]
        with patch.object(cleanup_module, 'get_all_github_runners', return_value=runners):
            with patch.object(cleanup_module, 'runner_has_infrastructure', return_value=False):
                with patch.object(cleanup_module, 'delete_github_runner_by_id', return_value=False):
                    result = cleanup_module.cleanup_orphaned_github_runners("test-token")
                    assert result["github_cleaned"] == 0
                    assert result["errors"] == 1

    def test_skips_runners_without_name_or_id(self, cleanup_module):
        """Test that runners without name or id are skipped (line 307)."""
        runners = [
            {"id": None, "name": "runner-1", "status": "offline"},  # Missing id
            {"id": 2, "name": "", "status": "offline"},  # Empty name
            {"id": 3, "name": None, "status": "offline"},  # Null name
            {"status": "offline"},  # Missing both name and id
        ]
        with patch.object(cleanup_module, 'get_all_github_runners', return_value=runners):
            with patch.object(cleanup_module, 'runner_has_infrastructure') as mock_has_infra:
                with patch.object(cleanup_module, 'delete_github_runner_by_id') as mock_delete:
                    result = cleanup_module.cleanup_orphaned_github_runners("test-token")
                    # None of these should have checked for infrastructure or deleted
                    mock_has_infra.assert_not_called()
                    mock_delete.assert_not_called()
                    assert result["github_cleaned"] == 0
                    assert result["errors"] == 0


class TestCleanupOrphanedResourcesErrors:
    """Tests for error handling in cleanup_orphaned_resources."""

    def test_counts_ecs_termination_errors(self, cleanup_module):
        """Test that ECS termination errors are counted."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "job_id": "",
            "github_repo": "",
        }
        with patch.object(cleanup_module, 'get_orphaned_ecs_tasks', return_value=[mock_task]):
            with patch.object(cleanup_module, 'get_orphaned_ec2_instances', return_value=[]):
                with patch.object(cleanup_module, 'terminate_ecs_task', return_value=False):
                    result = cleanup_module.cleanup_orphaned_resources("test-token")
                    assert result["errors"] == 1

    def test_counts_ec2_termination_errors(self, cleanup_module):
        """Test that EC2 termination errors are counted."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "job_id": "",
            "github_repo": "",
        }
        with patch.object(cleanup_module, 'get_orphaned_ecs_tasks', return_value=[]):
            with patch.object(cleanup_module, 'get_orphaned_ec2_instances', return_value=[mock_instance]):
                with patch.object(cleanup_module, 'terminate_ec2_instance', return_value=False):
                    result = cleanup_module.cleanup_orphaned_resources("test-token")
                    assert result["errors"] == 1


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_returns_200_with_cleanup_counts(self, cleanup_module):
        """Test that lambda handler returns 200 with cleanup counts."""
        orphan_result = {
            "ecs_cleaned": 1, "ecs_skipped": 0,
            "ec2_cleaned": 2, "ec2_skipped": 1,
            "errors": 0
        }
        github_result = {"github_cleaned": 1, "errors": 0}

        with patch.object(cleanup_module, 'get_github_token', return_value="test-token"):
            with patch.object(cleanup_module, 'cleanup_orphaned_resources', return_value=orphan_result):
                with patch.object(cleanup_module, 'cleanup_orphaned_github_runners', return_value=github_result):
                    result = cleanup_module.lambda_handler({}, None)
                    assert result["statusCode"] == 200
                    import json
                    body = json.loads(result["body"])
                    assert body["orphaned_ecs_cleaned"] == 1
                    assert body["orphaned_ec2_cleaned"] == 2
                    assert body["orphaned_github_cleaned"] == 1
                    assert body["errors"] == 0

    def test_aggregates_errors(self, cleanup_module):
        """Test that errors from both cleanups are aggregated."""
        orphan_result = {
            "ecs_cleaned": 0, "ecs_skipped": 0,
            "ec2_cleaned": 0, "ec2_skipped": 0,
            "errors": 2
        }
        github_result = {"github_cleaned": 0, "errors": 3}

        with patch.object(cleanup_module, 'get_github_token', return_value="test-token"):
            with patch.object(cleanup_module, 'cleanup_orphaned_resources', return_value=orphan_result):
                with patch.object(cleanup_module, 'cleanup_orphaned_github_runners', return_value=github_result):
                    result = cleanup_module.lambda_handler({}, None)
                    import json
                    body = json.loads(result["body"])
                    assert body["errors"] == 5
