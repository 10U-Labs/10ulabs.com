"""Unit tests for stale_runner_cleanup Lambda."""
import urllib.error
from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest

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
