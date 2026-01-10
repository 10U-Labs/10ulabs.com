"""Unit tests for runner_terminator Lambda."""
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from .conftest import load_lambda_module


@pytest.fixture(name="terminator_module")
def terminator_module_fixture():
    """Load runner_terminator module for testing."""
    env_vars = {
        'ECS_CLUSTER_ARN': 'arn:aws:ecs:us-east-2:123456789:cluster/test-cluster',
        'EC2_MANAGED_BY_TAG': 'test-managed-by',
    }
    with patch.dict('os.environ', env_vars):
        with patch('common.aws_clients.get_ec2_client'):
            with patch('common.aws_clients.get_ecs_client'):
                module = load_lambda_module(
                    "runner_terminator.py", "runner_terminator"
                )
                yield module


class TestFindEcsTaskByRunId:
    """Tests for _find_ecs_task_by_run_id function."""

    def test_returns_none_when_cluster_not_set(self, terminator_module):
        """Test that None is returned when cluster is not configured."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value=None):
            result = terminator_module._find_ecs_task_by_run_id(12345)
            assert result is None

    def test_returns_none_when_run_id_is_empty(self, terminator_module):
        """Test that None is returned when run_id is empty."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            result = terminator_module._find_ecs_task_by_run_id("")
            assert result is None

    def test_returns_none_when_no_tasks_found(self, terminator_module):
        """Test that None is returned when no tasks are running."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'list_running_task_arns', return_value=[]):
                result = terminator_module._find_ecs_task_by_run_id(12345)
                assert result is None

    def test_returns_task_when_run_id_matches(self, terminator_module):
        """Test that matching task is returned."""
        task_arn = "arn:aws:ecs:us-east-2:123:task/cluster/abc123"
        mock_task = {
            "taskArn": task_arn,
            "tags": [
                {"key": "RunId", "value": "12345"},
                {"key": "Name", "value": "test-runner"}
            ]
        }
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'list_running_task_arns', return_value=[task_arn]):
                with patch.object(terminator_module, 'describe_tasks_with_tags', return_value=[mock_task]):
                    with patch.object(terminator_module, 'extract_task_tags', return_value={"RunId": "12345", "Name": "test-runner"}):
                        result = terminator_module._find_ecs_task_by_run_id(12345)
                        assert result is not None
                        assert result["taskArn"] == task_arn
                        assert result["runnerName"] == "test-runner"

    def test_returns_none_when_run_id_does_not_match(self, terminator_module):
        """Test that None is returned when no task matches run_id."""
        task_arn = "arn:aws:ecs:us-east-2:123:task/cluster/abc123"
        mock_task = {"taskArn": task_arn, "tags": []}
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'list_running_task_arns', return_value=[task_arn]):
                with patch.object(terminator_module, 'describe_tasks_with_tags', return_value=[mock_task]):
                    with patch.object(terminator_module, 'extract_task_tags', return_value={"RunId": "99999"}):
                        result = terminator_module._find_ecs_task_by_run_id(12345)
                        assert result is None

    def test_returns_none_on_client_error(self, terminator_module):
        """Test that None is returned on client error."""
        from botocore.exceptions import ClientError
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'list_running_task_arns', side_effect=ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "ListTasks"
            )):
                result = terminator_module._find_ecs_task_by_run_id(12345)
                assert result is None


class TestFindEc2InstanceByRunId:
    """Tests for _find_ec2_instance_by_run_id function."""

    def test_returns_none_when_managed_by_tag_not_set(self, terminator_module):
        """Test that None is returned when managed by tag is not set."""
        with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': ''}):
            result = terminator_module._find_ec2_instance_by_run_id(12345)
            assert result is None

    def test_returns_none_when_run_id_is_empty(self, terminator_module):
        """Test that None is returned when run_id is empty."""
        result = terminator_module._find_ec2_instance_by_run_id("")
        assert result is None

    def test_returns_instance_when_found(self, terminator_module):
        """Test that matching instance is returned."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-1234567890",
                    "Tags": [
                        {"Key": "RunId", "Value": "12345"},
                        {"Key": "Name", "Value": "test-runner"}
                    ]
                }]
            }]
        }
        with patch.object(terminator_module, 'get_ec2_client', return_value=mock_ec2):
            result = terminator_module._find_ec2_instance_by_run_id(12345)
            assert result is not None
            assert result["instanceId"] == "i-1234567890"
            assert result["runnerName"] == "test-runner"

    def test_returns_none_when_no_instances_found(self, terminator_module):
        """Test that None is returned when no instances match."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {"Reservations": []}
        with patch.object(terminator_module, 'get_ec2_client', return_value=mock_ec2):
            result = terminator_module._find_ec2_instance_by_run_id(12345)
            assert result is None

    def test_returns_none_on_client_error(self, terminator_module):
        """Test that None is returned on client error."""
        from botocore.exceptions import ClientError
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "DescribeInstances"
        )
        with patch.object(terminator_module, 'get_ec2_client', return_value=mock_ec2):
            result = terminator_module._find_ec2_instance_by_run_id(12345)
            assert result is None


class TestStopEcsTaskWithMetrics:
    """Tests for _stop_ecs_task_with_metrics function."""

    def test_returns_false_when_cluster_not_configured(self, terminator_module):
        """Test that False is returned when cluster is not configured."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value=None):
            result = terminator_module._stop_ecs_task_with_metrics("task-arn", "reason")
            assert result is False

    def test_returns_true_on_successful_stop(self, terminator_module):
        """Test that True is returned on successful stop."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'stop_ecs_task', return_value=True):
                with patch.object(terminator_module, 'publish_metric'):
                    result = terminator_module._stop_ecs_task_with_metrics("task-arn", "reason")
                    assert result is True

    def test_publishes_success_metric_on_stop(self, terminator_module):
        """Test that success metric is published on stop."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'stop_ecs_task', return_value=True):
                with patch.object(terminator_module, 'publish_metric') as mock_pub:
                    terminator_module._stop_ecs_task_with_metrics("task-arn", "reason")
                    mock_pub.assert_called_once_with("RunnerTerminator", "EcsTasksStopped", 1, "Count")

    def test_returns_false_on_failed_stop(self, terminator_module):
        """Test that False is returned on failed stop."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'stop_ecs_task', return_value=False):
                with patch.object(terminator_module, 'publish_metric'):
                    result = terminator_module._stop_ecs_task_with_metrics("task-arn", "reason")
                    assert result is False

    def test_publishes_error_metric_on_failure(self, terminator_module):
        """Test that error metric is published on failure."""
        with patch.object(terminator_module, 'get_cluster_from_env', return_value="cluster"):
            with patch.object(terminator_module, 'stop_ecs_task', return_value=False):
                with patch.object(terminator_module, 'publish_metric') as mock_pub:
                    terminator_module._stop_ecs_task_with_metrics("task-arn", "reason")
                    mock_pub.assert_called_once_with("RunnerTerminator", "EcsStopErrors", 1, "Count")


class TestTerminateEc2InstanceWithMetrics:
    """Tests for _terminate_ec2_instance_with_metrics function."""

    def test_returns_true_on_successful_termination(self, terminator_module):
        """Test that True is returned on successful termination."""
        with patch.object(terminator_module, 'terminate_ec2_instance', return_value=True):
            with patch.object(terminator_module, 'publish_metric'):
                result = terminator_module._terminate_ec2_instance_with_metrics("i-123", "reason")
                assert result is True

    def test_publishes_success_metric_on_termination(self, terminator_module):
        """Test that success metric is published on termination."""
        with patch.object(terminator_module, 'terminate_ec2_instance', return_value=True):
            with patch.object(terminator_module, 'publish_metric') as mock_pub:
                terminator_module._terminate_ec2_instance_with_metrics("i-123", "reason")
                mock_pub.assert_called_once_with("RunnerTerminator", "Ec2InstancesTerminated", 1, "Count")

    def test_returns_false_on_failed_termination(self, terminator_module):
        """Test that False is returned on failed termination."""
        with patch.object(terminator_module, 'terminate_ec2_instance', return_value=False):
            with patch.object(terminator_module, 'publish_metric'):
                result = terminator_module._terminate_ec2_instance_with_metrics("i-123", "reason")
                assert result is False

    def test_publishes_error_metric_on_failure(self, terminator_module):
        """Test that error metric is published on failure."""
        with patch.object(terminator_module, 'terminate_ec2_instance', return_value=False):
            with patch.object(terminator_module, 'publish_metric') as mock_pub:
                terminator_module._terminate_ec2_instance_with_metrics("i-123", "reason")
                mock_pub.assert_called_once_with("RunnerTerminator", "Ec2TerminateErrors", 1, "Count")


class TestTerminateRunnerByRunId:
    """Tests for _terminate_runner_by_run_id function."""

    def test_stops_ecs_task_when_found(self, terminator_module):
        """Test that ECS task is stopped when found."""
        ecs_task = {"taskArn": "arn:task", "runnerName": "runner"}
        with patch.object(terminator_module, '_find_ecs_task_by_run_id', return_value=ecs_task):
            with patch.object(terminator_module, '_stop_ecs_task_with_metrics', return_value=True):
                result = terminator_module._terminate_runner_by_run_id(12345, "cancelled", 999)
                assert result["success"] is True
                assert result["type"] == "ecs"
                assert result["resourceId"] == "arn:task"

    def test_terminates_ec2_when_no_ecs_found(self, terminator_module):
        """Test that EC2 instance is terminated when no ECS task found."""
        ec2_instance = {"instanceId": "i-123", "runnerName": "runner"}
        with patch.object(terminator_module, '_find_ecs_task_by_run_id', return_value=None):
            with patch.object(terminator_module, '_find_ec2_instance_by_run_id', return_value=ec2_instance):
                with patch.object(terminator_module, '_terminate_ec2_instance_with_metrics', return_value=True):
                    result = terminator_module._terminate_runner_by_run_id(12345, "cancelled", 999)
                    assert result["success"] is True
                    assert result["type"] == "ec2"
                    assert result["resourceId"] == "i-123"

    def test_returns_success_when_no_runner_found(self, terminator_module):
        """Test that success is returned when no runner is found."""
        with patch.object(terminator_module, '_find_ecs_task_by_run_id', return_value=None):
            with patch.object(terminator_module, '_find_ec2_instance_by_run_id', return_value=None):
                with patch.object(terminator_module, 'publish_metric'):
                    result = terminator_module._terminate_runner_by_run_id(12345, "cancelled", 999)
                    assert result["success"] is True
                    assert result["type"] == "none"
                    assert result["resourceId"] is None

    def test_publishes_not_found_metric(self, terminator_module):
        """Test that RunnerNotFound metric is published when no runner found."""
        with patch.object(terminator_module, '_find_ecs_task_by_run_id', return_value=None):
            with patch.object(terminator_module, '_find_ec2_instance_by_run_id', return_value=None):
                with patch.object(terminator_module, 'publish_metric') as mock_pub:
                    terminator_module._terminate_runner_by_run_id(12345, "cancelled", 999)
                    mock_pub.assert_called_once_with("RunnerTerminator", "RunnerNotFound", 1, "Count")


class TestHandleCancellationMessage:
    """Tests for _handle_cancellation_message function."""

    def test_returns_skipped_when_no_run_id(self, terminator_module):
        """Test that message is skipped when no run_id."""
        message = {"body": json.dumps({"action": "cancelled", "job_id": 123})}
        result = terminator_module._handle_cancellation_message(message)
        assert result["success"] is True
        assert result["skipped"] is True

    def test_terminates_runner_when_run_id_present(self, terminator_module):
        """Test that runner is terminated when run_id is present."""
        message = {"body": json.dumps({
            "action": "cancelled",
            "job_id": 123,
            "run_id": 456
        })}
        with patch.object(terminator_module, '_terminate_runner_by_run_id', return_value={
            "success": True, "type": "ecs", "resourceId": "arn:task"
        }):
            result = terminator_module._handle_cancellation_message(message)
            assert result["success"] is True

    def test_returns_error_on_termination_failure(self, terminator_module):
        """Test that error is returned when termination fails."""
        message = {"body": json.dumps({
            "action": "cancelled",
            "job_id": 123,
            "run_id": 456
        })}
        with patch.object(terminator_module, '_terminate_runner_by_run_id', return_value={
            "success": False
        }):
            result = terminator_module._handle_cancellation_message(message)
            assert result["success"] is False

    def test_handles_json_decode_error(self, terminator_module):
        """Test that JSONDecodeError is handled gracefully."""
        message = {"body": "not valid json"}
        result = terminator_module._handle_cancellation_message(message)
        assert result["success"] is False

    def test_handles_missing_body_gracefully(self, terminator_module):
        """Test that missing body is handled gracefully with success=True."""
        message = {}  # Missing 'body' key, defaults to "{}"
        result = terminator_module._handle_cancellation_message(message)
        # No run_id in empty body, so returns success with skipped
        assert result["success"] is True
        assert result["skipped"] is True


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_returns_empty_response_when_no_records(self, terminator_module, lambda_context):
        """Test that empty response is returned when no records."""
        event = {"Records": []}
        with patch.object(terminator_module, 'get_sqs_records', return_value=None):
            with patch.object(terminator_module, 'empty_records_response', return_value={"statusCode": 200}):
                result = terminator_module.lambda_handler(event, lambda_context)
                assert result["statusCode"] == 200

    def test_processes_cancellation_messages(self, terminator_module, lambda_context):
        """Test that cancellation messages are processed."""
        message = {"body": json.dumps({
            "action": "cancelled",
            "job_id": 123,
            "run_id": 456
        })}
        event = {"Records": [message]}
        with patch.object(terminator_module, 'get_sqs_records', return_value=[message]):
            with patch.object(terminator_module, '_handle_cancellation_message', return_value={"success": True}):
                with patch.object(terminator_module, 'publish_metric'):
                    with patch.object(terminator_module, 'count_results', return_value=(1, 0)):
                        result = terminator_module.lambda_handler(event, lambda_context)
                        assert result["statusCode"] == 200
                        body = json.loads(result["body"])
                        assert body["success"] == 1

    def test_raises_runtime_error_on_failures(self, terminator_module, lambda_context):
        """Test that RuntimeError is raised when cancellations fail."""
        message = {"body": json.dumps({"action": "cancelled", "job_id": 123, "run_id": 456})}
        event = {"Records": [message]}
        with patch.object(terminator_module, 'get_sqs_records', return_value=[message]):
            with patch.object(terminator_module, '_handle_cancellation_message', return_value={"success": False}):
                with patch.object(terminator_module, 'publish_metric'):
                    with patch.object(terminator_module, 'count_results', return_value=(0, 1)):
                        with pytest.raises(RuntimeError, match="1 cancellation"):
                            terminator_module.lambda_handler(event, lambda_context)

    def test_publishes_processing_time_metric(self, terminator_module, lambda_context):
        """Test that processing time metric is published."""
        event = {"Records": []}
        with patch.object(terminator_module, 'get_sqs_records', return_value=[]):
            with patch.object(terminator_module, 'count_results', return_value=(0, 0)):
                with patch.object(terminator_module, 'publish_metric') as mock_pub:
                    terminator_module.lambda_handler(event, lambda_context)
                    calls = [call for call in mock_pub.call_args_list if "ProcessingTime" in str(call)]
                    assert len(calls) == 1
