"""Unit tests for stale_runner_cleanup Lambda."""
from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest

from .conftest import load_lambda_module


@pytest.fixture
def stale_runner_cleanup():
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
    is_busy: bool
) -> Iterator[dict[str, MagicMock]]:
    """Context manager for cleanup tests with common mock setup."""
    with patch.object(module, '_get_orphaned_ecs_tasks', return_value=ecs_tasks):
        with patch.object(module, '_get_orphaned_ec2_instances',
                          return_value=ec2_instances):
            with patch.object(module, '_is_runner_busy',
                              return_value=is_busy) as mock_busy:
                with patch.object(module, '_terminate_ecs_task',
                                  return_value=True) as mock_terminate_ecs:
                    with patch.object(module, 'terminate_ec2_instance',
                                      return_value=True) as mock_terminate_ec2:
                        with patch.object(module, '_delete_github_runner',
                                          return_value=True):
                            yield {
                                'is_busy': mock_busy,
                                'terminate_ecs': mock_terminate_ecs,
                                'terminate_ec2': mock_terminate_ec2
                            }


class TestIsRunnerBusy:
    """Tests for _is_runner_busy function."""

    def test_returns_true_when_runner_is_busy(self, stale_runner_cleanup):
        """Test that busy runners are correctly identified."""
        mock_runners = [
            {"name": "fargate-runner-123", "busy": True},
            {"name": "fargate-runner-456", "busy": False},
        ]
        with patch.object(
            stale_runner_cleanup,
            '_get_all_github_runners',
            return_value=mock_runners
        ):
            result = stale_runner_cleanup._is_runner_busy(
                "test-token", "test-org/test-repo", "fargate-runner-123"
            )
            assert result is True

    def test_returns_false_when_runner_is_not_busy(self, stale_runner_cleanup):
        """Test that idle runners are correctly identified."""
        mock_runners = [
            {"name": "fargate-runner-123", "busy": True},
            {"name": "fargate-runner-456", "busy": False},
        ]
        with patch.object(
            stale_runner_cleanup,
            '_get_all_github_runners',
            return_value=mock_runners
        ):
            result = stale_runner_cleanup._is_runner_busy(
                "test-token", "test-org/test-repo", "fargate-runner-456"
            )
            assert result is False

    def test_returns_false_when_runner_not_found(self, stale_runner_cleanup):
        """Test that non-existent runners return False."""
        mock_runners = [
            {"name": "fargate-runner-123", "busy": True},
        ]
        with patch.object(
            stale_runner_cleanup,
            '_get_all_github_runners',
            return_value=mock_runners
        ):
            result = stale_runner_cleanup._is_runner_busy(
                "test-token", "test-org/test-repo", "fargate-runner-999"
            )
            assert result is False

    def test_returns_true_when_api_fails(self, stale_runner_cleanup):
        """Test that API failures default to busy (safe behavior)."""
        with patch.object(
            stale_runner_cleanup,
            '_get_all_github_runners',
            return_value=None
        ):
            result = stale_runner_cleanup._is_runner_busy(
                "test-token", "test-org/test-repo", "fargate-runner-123"
            )
            assert result is True

    def test_returns_false_when_busy_field_missing(self, stale_runner_cleanup):
        """Test that missing busy field defaults to False."""
        mock_runners = [
            {"name": "fargate-runner-123"},
        ]
        with patch.object(
            stale_runner_cleanup,
            '_get_all_github_runners',
            return_value=mock_runners
        ):
            result = stale_runner_cleanup._is_runner_busy(
                "test-token", "test-org/test-repo", "fargate-runner-123"
            )
            assert result is False


class TestCleanupOrphanedResourcesSkipsBusy:
    """Tests that cleanup skips busy runners."""

    def test_busy_ecs_task_checks_runner_status(self, stale_runner_cleanup):
        """Test that busy check is called for ECS tasks."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "runner_name": "fargate-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [mock_task], [],
                                  is_busy=True) as mocks:
            stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            mocks['is_busy'].assert_called_once_with(
                "test-token", "test-org/test-repo", "fargate-runner-123"
            )

    def test_busy_ecs_task_is_not_terminated(self, stale_runner_cleanup):
        """Test that busy ECS tasks are not terminated."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "runner_name": "fargate-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [mock_task], [],
                                  is_busy=True) as mocks:
            stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            mocks['terminate_ecs'].assert_not_called()

    def test_busy_ecs_task_returns_skipped_count(self, stale_runner_cleanup):
        """Test that busy ECS tasks are counted as skipped."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "runner_name": "fargate-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [mock_task], [],
                                  is_busy=True):
            result = stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            assert (result["ecs_skipped"], result["ecs_cleaned"]) == (1, 0)

    def test_idle_ecs_task_is_terminated(self, stale_runner_cleanup):
        """Test that idle ECS tasks are terminated."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "runner_name": "fargate-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [mock_task], [],
                                  is_busy=False) as mocks:
            stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            mocks['terminate_ecs'].assert_called_once()

    def test_idle_ecs_task_returns_cleaned_count(self, stale_runner_cleanup):
        """Test that idle ECS tasks are counted as cleaned."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "runner_name": "fargate-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [mock_task], [],
                                  is_busy=False):
            result = stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            assert (result["ecs_cleaned"], result["ecs_skipped"]) == (1, 0)

    def test_busy_ec2_instance_checks_runner_status(self, stale_runner_cleanup):
        """Test that busy check is called for EC2 instances."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "runner_name": "ec2-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [], [mock_instance],
                                  is_busy=True) as mocks:
            stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            mocks['is_busy'].assert_called_once_with(
                "test-token", "test-org/test-repo", "ec2-runner-123"
            )

    def test_busy_ec2_instance_is_not_terminated(self, stale_runner_cleanup):
        """Test that busy EC2 instances are not terminated."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "runner_name": "ec2-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [], [mock_instance],
                                  is_busy=True) as mocks:
            stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            mocks['terminate_ec2'].assert_not_called()

    def test_busy_ec2_instance_returns_skipped_count(self, stale_runner_cleanup):
        """Test that busy EC2 instances are counted as skipped."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "runner_name": "ec2-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [], [mock_instance],
                                  is_busy=True):
            result = stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            assert (result["ec2_skipped"], result["ec2_cleaned"]) == (1, 0)

    def test_idle_ec2_instance_is_terminated(self, stale_runner_cleanup):
        """Test that idle EC2 instances are terminated with correct ID."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "runner_name": "ec2-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [], [mock_instance],
                                  is_busy=False) as mocks:
            stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            mocks['terminate_ec2'].assert_called_once_with("i-1234567890abcdef0")

    def test_idle_ec2_instance_returns_cleaned_count(self, stale_runner_cleanup):
        """Test that idle EC2 instances are counted as cleaned."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "runner_name": "ec2-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with cleanup_test_context(stale_runner_cleanup, [], [mock_instance],
                                  is_busy=False):
            result = stale_runner_cleanup._cleanup_orphaned_resources("test-token")
            assert (result["ec2_cleaned"], result["ec2_skipped"]) == (1, 0)
