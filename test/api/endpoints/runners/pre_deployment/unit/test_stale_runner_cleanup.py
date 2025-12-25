"""Unit tests for stale_runner_cleanup Lambda."""
# pylint: disable=redefined-outer-name,protected-access
from unittest.mock import patch

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

    def test_skips_busy_ecs_task(self, stale_runner_cleanup):
        """Test that busy ECS tasks are not terminated."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "runner_name": "fargate-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with patch.object(
            stale_runner_cleanup,
            '_get_orphaned_ecs_tasks',
            return_value=[mock_task]
        ):
            with patch.object(
                stale_runner_cleanup,
                '_get_orphaned_ec2_instances',
                return_value=[]
            ):
                with patch.object(
                    stale_runner_cleanup,
                    '_is_runner_busy',
                    return_value=True
                ) as mock_busy:
                    with patch.object(
                        stale_runner_cleanup,
                        '_terminate_ecs_task'
                    ) as mock_terminate:
                        result = stale_runner_cleanup._cleanup_orphaned_resources(
                            "test-token"
                        )
                        mock_busy.assert_called_once_with(
                            "test-token", "test-org/test-repo", "fargate-runner-123"
                        )
                        mock_terminate.assert_not_called()
                        assert result["ecs_skipped"] == 1
                        assert result["ecs_cleaned"] == 0

    def test_terminates_idle_ecs_task(self, stale_runner_cleanup):
        """Test that idle ECS tasks are terminated."""
        mock_task = {
            "task_arn": "arn:aws:ecs:us-east-2:123:task/test/abc",
            "age_seconds": 600,
            "runner_name": "fargate-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with patch.object(
            stale_runner_cleanup,
            '_get_orphaned_ecs_tasks',
            return_value=[mock_task]
        ):
            with patch.object(
                stale_runner_cleanup,
                '_get_orphaned_ec2_instances',
                return_value=[]
            ):
                with patch.object(
                    stale_runner_cleanup,
                    '_is_runner_busy',
                    return_value=False
                ):
                    with patch.object(
                        stale_runner_cleanup,
                        '_terminate_ecs_task',
                        return_value=True
                    ) as mock_terminate:
                        with patch.object(
                            stale_runner_cleanup,
                            '_delete_github_runner',
                            return_value=True
                        ):
                            result = stale_runner_cleanup._cleanup_orphaned_resources(
                                "test-token"
                            )
                            mock_terminate.assert_called_once()
                            assert result["ecs_cleaned"] == 1
                            assert result["ecs_skipped"] == 0

    def test_skips_busy_ec2_instance(self, stale_runner_cleanup):
        """Test that busy EC2 instances are not terminated."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "runner_name": "ec2-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with patch.object(
            stale_runner_cleanup,
            '_get_orphaned_ecs_tasks',
            return_value=[]
        ):
            with patch.object(
                stale_runner_cleanup,
                '_get_orphaned_ec2_instances',
                return_value=[mock_instance]
            ):
                with patch.object(
                    stale_runner_cleanup,
                    '_is_runner_busy',
                    return_value=True
                ) as mock_busy:
                    with patch.object(
                        stale_runner_cleanup,
                        'terminate_ec2_instance'
                    ) as mock_terminate:
                        result = stale_runner_cleanup._cleanup_orphaned_resources(
                            "test-token"
                        )
                        mock_busy.assert_called_once_with(
                            "test-token", "test-org/test-repo", "ec2-runner-123"
                        )
                        mock_terminate.assert_not_called()
                        assert result["ec2_skipped"] == 1
                        assert result["ec2_cleaned"] == 0

    def test_terminates_idle_ec2_instance(self, stale_runner_cleanup):
        """Test that idle EC2 instances are terminated."""
        mock_instance = {
            "instance_id": "i-1234567890abcdef0",
            "age_seconds": 600,
            "runner_name": "ec2-runner-123",
            "github_repo": "test-org/test-repo",
        }
        with patch.object(
            stale_runner_cleanup,
            '_get_orphaned_ecs_tasks',
            return_value=[]
        ):
            with patch.object(
                stale_runner_cleanup,
                '_get_orphaned_ec2_instances',
                return_value=[mock_instance]
            ):
                with patch.object(
                    stale_runner_cleanup,
                    '_is_runner_busy',
                    return_value=False
                ):
                    with patch.object(
                        stale_runner_cleanup,
                        'terminate_ec2_instance',
                        return_value=True
                    ) as mock_terminate:
                        with patch.object(
                            stale_runner_cleanup,
                            '_delete_github_runner',
                            return_value=True
                        ):
                            result = stale_runner_cleanup._cleanup_orphaned_resources(
                                "test-token"
                            )
                            mock_terminate.assert_called_once_with(
                                "i-1234567890abcdef0"
                            )
                            assert result["ec2_cleaned"] == 1
                            assert result["ec2_skipped"] == 0
