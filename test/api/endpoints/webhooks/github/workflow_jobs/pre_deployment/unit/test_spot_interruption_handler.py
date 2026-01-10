"""Unit tests for spot_interruption_handler Lambda."""
import json
from unittest.mock import MagicMock, patch

import pytest

from .conftest import load_lambda_module


@pytest.fixture(name="spot_module")
def spot_module_fixture():
    """Load spot_interruption_handler module for testing."""
    env_vars = {
        'ECS_CLUSTER': 'test-cluster',
    }
    with patch.dict('os.environ', env_vars):
        with patch('common.aws_clients.get_ecs_client'):
            with patch('common.aws_clients.get_ec2_client'):
                module = load_lambda_module(
                    "spot_interruption_handler.py", "spot_interruption_handler"
                )
                yield module


class TestGetWorkflowRunStatus:
    """Tests for _get_workflow_run_status function."""

    def test_returns_status_from_github_api(self, spot_module):
        """Test that status is returned from GitHub API."""
        with patch.object(spot_module, 'github_api_request', return_value={"status": "in_progress"}):
            result = spot_module._get_workflow_run_status("token", "org/repo", 12345)
            assert result == "in_progress"

    def test_returns_unknown_on_http_error(self, spot_module):
        """Test that unknown is returned on HTTP error."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )):
            result = spot_module._get_workflow_run_status("token", "org/repo", 12345)
            assert result == "unknown"

    def test_returns_unknown_when_status_missing(self, spot_module):
        """Test that unknown is returned when status is missing."""
        with patch.object(spot_module, 'github_api_request', return_value={}):
            result = spot_module._get_workflow_run_status("token", "org/repo", 12345)
            assert result == "unknown"


class TestCancelWorkflowRun:
    """Tests for _cancel_workflow_run function."""

    def test_returns_true_on_successful_cancel(self, spot_module):
        """Test that True is returned on successful cancel."""
        with patch.object(spot_module, 'github_api_request', return_value={}):
            result = spot_module._cancel_workflow_run("token", "org/repo", 12345)
            assert result is True

    def test_returns_true_on_202_error(self, spot_module):
        """Test that True is returned on 202 HTTP error (accepted)."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=202, msg="Accepted", hdrs={}, fp=None
        )):
            result = spot_module._cancel_workflow_run("token", "org/repo", 12345)
            assert result is True

    def test_returns_false_on_other_http_error(self, spot_module):
        """Test that False is returned on other HTTP errors."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=None
        )):
            result = spot_module._cancel_workflow_run("token", "org/repo", 12345)
            assert result is False


class TestCreateCheckRunAnnotation:
    """Tests for _create_check_run_annotation function."""

    def test_returns_true_on_successful_creation(self, spot_module):
        """Test that True is returned on successful creation."""
        with patch.object(spot_module, 'github_api_request', return_value={}):
            result = spot_module._create_check_run_annotation(
                "token", "org/repo", "sha123", "Title", "Summary"
            )
            assert result is True

    def test_returns_true_on_201_error(self, spot_module):
        """Test that True is returned on 201 HTTP error (created)."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=201, msg="Created", hdrs={}, fp=None
        )):
            result = spot_module._create_check_run_annotation(
                "token", "org/repo", "sha123", "Title", "Summary"
            )
            assert result is True

    def test_returns_false_on_other_http_error(self, spot_module):
        """Test that False is returned on other HTTP errors."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=None
        )):
            result = spot_module._create_check_run_annotation(
                "token", "org/repo", "sha123", "Title", "Summary"
            )
            assert result is False


class TestWaitForWorkflowCompletion:
    """Tests for _wait_for_workflow_completion function."""

    def test_returns_true_when_completed(self, spot_module):
        """Test that True is returned when workflow completes."""
        with patch.object(spot_module, 'github_api_request', return_value={"status": "completed"}):
            result = spot_module._wait_for_workflow_completion("token", "org/repo", 12345, timeout_seconds=1)
            assert result is True

    def test_returns_false_on_timeout(self, spot_module):
        """Test that False is returned on timeout."""
        with patch.object(spot_module, 'github_api_request', return_value={"status": "in_progress"}):
            with patch('time.sleep'):
                result = spot_module._wait_for_workflow_completion("token", "org/repo", 12345, timeout_seconds=0)
                assert result is False

    def test_handles_http_errors_during_polling(self, spot_module):
        """Test that HTTP errors are handled during polling and continues to next iteration."""
        import urllib.error
        call_count = [0]
        def mock_api_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise urllib.error.HTTPError(url="", code=500, msg="Server Error", hdrs={}, fp=None)
            return {"status": "completed"}
        with patch.object(spot_module, 'github_api_request', side_effect=mock_api_request):
            with patch('time.sleep'):
                result = spot_module._wait_for_workflow_completion("token", "org/repo", 12345, timeout_seconds=60)
                assert result is True
                assert call_count[0] == 2


class TestGetWorkflowInfoFromRun:
    """Tests for _get_workflow_info_from_run function."""

    def test_returns_workflow_info(self, spot_module):
        """Test that workflow info is returned."""
        with patch.object(spot_module, 'github_api_request', return_value={
            "workflow_id": 999,
            "head_sha": "abc123"
        }):
            result = spot_module._get_workflow_info_from_run("token", "org/repo", 12345)
            assert result["workflowId"] == "999"
            assert result["headSha"] == "abc123"

    def test_returns_empty_on_http_error(self, spot_module):
        """Test that empty values are returned on HTTP error."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )):
            result = spot_module._get_workflow_info_from_run("token", "org/repo", 12345)
            assert result["workflowId"] == ""
            assert result["headSha"] == ""


class TestDispatchWorkflow:
    """Tests for _dispatch_workflow function."""

    def test_returns_true_on_successful_dispatch(self, spot_module):
        """Test that True is returned on successful dispatch."""
        with patch.object(spot_module, 'github_api_request', return_value={}):
            result = spot_module._dispatch_workflow("token", "org/repo", "999", "main", "reason")
            assert result is True

    def test_returns_true_on_204_error(self, spot_module):
        """Test that True is returned on 204 HTTP error."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=204, msg="No Content", hdrs={}, fp=None
        )):
            result = spot_module._dispatch_workflow("token", "org/repo", "999", "main", "reason")
            assert result is True

    def test_returns_false_on_other_http_error(self, spot_module):
        """Test that False is returned on other HTTP errors."""
        import urllib.error
        with patch.object(spot_module, 'github_api_request', side_effect=urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=None
        )):
            result = spot_module._dispatch_workflow("token", "org/repo", "999", "main", "reason")
            assert result is False


class TestIsSpotInterruption:
    """Tests for _is_spot_interruption function."""

    def test_returns_true_for_spot_interruption_code(self, spot_module):
        """Test that True is returned for SpotInterruption stop code."""
        result = spot_module._is_spot_interruption("SpotInterruption", "any reason")
        assert result is True

    def test_returns_true_for_capacity_in_reason(self, spot_module):
        """Test that True is returned when capacity is in reason."""
        result = spot_module._is_spot_interruption("EssentialContainerExited", "capacity reclaimed")
        assert result is True

    def test_returns_false_for_normal_stop(self, spot_module):
        """Test that False is returned for normal stop."""
        result = spot_module._is_spot_interruption("EssentialContainerExited", "Container exited normally")
        assert result is False


class TestPrepareWorkflowRecovery:
    """Tests for _prepare_workflow_recovery function."""

    def test_returns_workflow_info_on_success(self, spot_module):
        """Test that workflow info is returned on success."""
        with patch.object(spot_module, '_get_workflow_info_from_run', return_value={
            "workflowId": "999",
            "headSha": "abc123"
        }):
            with patch.object(spot_module, '_cancel_workflow_run', return_value=True):
                workflow_id, head_sha, error = spot_module._prepare_workflow_recovery(
                    "token", "org/repo", 12345
                )
                assert workflow_id == "999"
                assert head_sha == "abc123"
                assert error is None

    def test_returns_error_when_workflow_id_missing(self, spot_module):
        """Test that error is returned when workflow ID is missing."""
        with patch.object(spot_module, '_get_workflow_info_from_run', return_value={
            "workflowId": "",
            "headSha": ""
        }):
            workflow_id, head_sha, error = spot_module._prepare_workflow_recovery(
                "token", "org/repo", 12345
            )
            assert error is not None
            assert error["statusCode"] == 500

    def test_returns_error_when_cancel_fails(self, spot_module):
        """Test that error is returned when cancel fails."""
        with patch.object(spot_module, '_get_workflow_info_from_run', return_value={
            "workflowId": "999",
            "headSha": "abc123"
        }):
            with patch.object(spot_module, '_cancel_workflow_run', return_value=False):
                workflow_id, head_sha, error = spot_module._prepare_workflow_recovery(
                    "token", "org/repo", 12345
                )
                assert error is not None
                assert error["statusCode"] == 500


class TestRecoverFromSpotInterruption:
    """Tests for _recover_from_spot_interruption function."""

    def test_returns_success_on_recovery(self, spot_module):
        """Test that success is returned on recovery."""
        with patch.object(spot_module, '_prepare_workflow_recovery', return_value=("999", "abc123", None)):
            with patch.object(spot_module, '_create_check_run_annotation', return_value=True):
                with patch.object(spot_module, '_wait_for_workflow_completion', return_value=True):
                    with patch.object(spot_module, '_dispatch_workflow', return_value=True):
                        result = spot_module._recover_from_spot_interruption(
                            "token", "org/repo", 12345, "i-123"
                        )
                        assert result["statusCode"] == 200

    def test_returns_error_on_prepare_failure(self, spot_module):
        """Test that error is returned on prepare failure."""
        with patch.object(spot_module, '_prepare_workflow_recovery', return_value=(
            "", "", {"statusCode": 500, "body": "error"}
        )):
            result = spot_module._recover_from_spot_interruption("token", "org/repo", 12345, "i-123")
            assert result["statusCode"] == 500

    def test_returns_error_on_dispatch_failure(self, spot_module):
        """Test that error is returned on dispatch failure."""
        with patch.object(spot_module, '_prepare_workflow_recovery', return_value=("999", "abc123", None)):
            with patch.object(spot_module, '_create_check_run_annotation', return_value=True):
                with patch.object(spot_module, '_wait_for_workflow_completion', return_value=True):
                    with patch.object(spot_module, '_dispatch_workflow', return_value=False):
                        result = spot_module._recover_from_spot_interruption(
                            "token", "org/repo", 12345, "i-123"
                        )
                        assert result["statusCode"] == 500


class TestRecoverFromEcsSpotInterruption:
    """Tests for _recover_from_ecs_spot_interruption function."""

    def test_returns_success_on_recovery(self, spot_module):
        """Test that success is returned on ECS recovery."""
        with patch.object(spot_module, '_prepare_workflow_recovery', return_value=("999", "abc123", None)):
            with patch.object(spot_module, '_create_check_run_annotation', return_value=True):
                with patch.object(spot_module, '_wait_for_workflow_completion', return_value=True):
                    with patch.object(spot_module, '_dispatch_workflow', return_value=True):
                        result = spot_module._recover_from_ecs_spot_interruption(
                            "token", "org/repo", 12345, "arn:task/cluster/task123"
                        )
                        assert result["statusCode"] == 200

    def test_extracts_task_id_from_arn(self, spot_module):
        """Test that task ID is extracted from ARN for annotation."""
        check_run_args = []
        def capture_check_run(*args, **kwargs):
            check_run_args.append(args)
            return True
        with patch.object(spot_module, '_prepare_workflow_recovery', return_value=("999", "abc123", None)):
            with patch.object(spot_module, '_create_check_run_annotation', side_effect=capture_check_run):
                with patch.object(spot_module, '_wait_for_workflow_completion', return_value=True):
                    with patch.object(spot_module, '_dispatch_workflow', return_value=True):
                        spot_module._recover_from_ecs_spot_interruption(
                            "token", "org/repo", 12345, "arn:aws:ecs:region:123:task/cluster/abc123"
                        )
                        # Check that the summary contains the task ID
                        summary = check_run_args[0][4]
                        assert "abc123" in summary

    def test_returns_error_on_prepare_failure(self, spot_module):
        """Test that error is returned when prepare fails."""
        with patch.object(spot_module, '_prepare_workflow_recovery', return_value=(
            "", "", {"statusCode": 500, "body": "Failed to get workflow info"}
        )):
            result = spot_module._recover_from_ecs_spot_interruption(
                "token", "org/repo", 12345, "arn:task/cluster/task123"
            )
            assert result["statusCode"] == 500

    def test_returns_error_on_dispatch_failure(self, spot_module):
        """Test that error is returned when dispatch fails."""
        with patch.object(spot_module, '_prepare_workflow_recovery', return_value=("999", "abc123", None)):
            with patch.object(spot_module, '_create_check_run_annotation', return_value=True):
                with patch.object(spot_module, '_wait_for_workflow_completion', return_value=True):
                    with patch.object(spot_module, '_dispatch_workflow', return_value=False):
                        result = spot_module._recover_from_ecs_spot_interruption(
                            "token", "org/repo", 12345, "arn:task/cluster/task123"
                        )
                        assert result["statusCode"] == 500


class TestTriggerEcsRecovery:
    """Tests for _trigger_ecs_recovery function."""

    def test_returns_error_when_no_token(self, spot_module):
        """Test that error is returned when no GitHub token."""
        with patch.object(spot_module, 'get_github_token', return_value=None):
            result = spot_module._trigger_ecs_recovery("org/repo", 12345, "arn:task")
            assert result["statusCode"] == 500

    def test_skips_inactive_workflow(self, spot_module):
        """Test that inactive workflow is skipped."""
        with patch.object(spot_module, 'get_github_token', return_value="token"):
            with patch.object(spot_module, '_get_workflow_run_status', return_value="completed"):
                result = spot_module._trigger_ecs_recovery("org/repo", 12345, "arn:task")
                assert result["statusCode"] == 200
                assert "not active" in result["body"]

    def test_initiates_recovery_for_active_workflow(self, spot_module):
        """Test that recovery is initiated for active workflow."""
        with patch.object(spot_module, 'get_github_token', return_value="token"):
            with patch.object(spot_module, '_get_workflow_run_status', return_value="in_progress"):
                with patch.object(spot_module, '_recover_from_ecs_spot_interruption', return_value={
                    "statusCode": 200, "body": "success"
                }):
                    result = spot_module._trigger_ecs_recovery("org/repo", 12345, "arn:task")
                    assert result["statusCode"] == 200


class TestGetEcsTaskTags:
    """Tests for _get_ecs_task_tags function."""

    def test_returns_tags_from_task(self, spot_module):
        """Test that tags are returned from task."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.return_value = {
            "tasks": [{
                "tags": [
                    {"key": "RunId", "value": "12345"},
                    {"key": "GitHubRepo", "value": "org/repo"}
                ]
            }]
        }
        with patch.object(spot_module, 'get_ecs_client', return_value=mock_ecs):
            result = spot_module._get_ecs_task_tags("arn:task")
            assert result["RunId"] == "12345"
            assert result["GitHubRepo"] == "org/repo"

    def test_returns_empty_dict_on_error(self, spot_module):
        """Test that empty dict is returned on error."""
        from botocore.exceptions import ClientError
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "DescribeTasks"
        )
        with patch.object(spot_module, 'get_ecs_client', return_value=mock_ecs):
            result = spot_module._get_ecs_task_tags("arn:task")
            assert result == {}

    def test_returns_empty_dict_when_no_tasks(self, spot_module):
        """Test that empty dict is returned when no tasks."""
        mock_ecs = MagicMock()
        mock_ecs.describe_tasks.return_value = {"tasks": []}
        with patch.object(spot_module, 'get_ecs_client', return_value=mock_ecs):
            result = spot_module._get_ecs_task_tags("arn:task")
            assert result == {}


class TestHandleEcsTaskStopped:
    """Tests for _handle_ecs_task_stopped function."""

    def test_skips_when_no_run_id(self, spot_module):
        """Test that event is skipped when no run_id in tags."""
        event = {"detail": {"taskArn": "arn:task", "stopCode": "SpotInterruption", "stoppedReason": ""}}
        with patch.object(spot_module, '_get_ecs_task_tags', return_value={}):
            result = spot_module._handle_ecs_task_stopped(event)
            assert result["statusCode"] == 200
            assert "No run_id" in result["body"]

    def test_skips_non_spot_interruption(self, spot_module):
        """Test that non-spot interruption is skipped."""
        event = {"detail": {"taskArn": "arn:task", "stopCode": "UserInitiated", "stoppedReason": "User stopped"}}
        with patch.object(spot_module, '_get_ecs_task_tags', return_value={"RunId": "12345"}):
            result = spot_module._handle_ecs_task_stopped(event)
            assert result["statusCode"] == 200
            assert "Not a spot interruption" in result["body"]

    def test_triggers_recovery_for_spot_interruption(self, spot_module):
        """Test that recovery is triggered for spot interruption."""
        event = {"detail": {"taskArn": "arn:task", "stopCode": "SpotInterruption", "stoppedReason": ""}}
        with patch.object(spot_module, '_get_ecs_task_tags', return_value={
            "RunId": "12345",
            "GitHubRepo": "org/repo"
        }):
            with patch.object(spot_module, '_trigger_ecs_recovery', return_value={
                "statusCode": 200, "body": "success"
            }):
                result = spot_module._handle_ecs_task_stopped(event)
                assert result["statusCode"] == 200


class TestGetEc2InstanceTags:
    """Tests for _get_ec2_instance_tags function."""

    def test_returns_tags_from_instance(self, spot_module):
        """Test that tags are returned from instance."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "Tags": [
                        {"Key": "RunId", "Value": "12345"},
                        {"Key": "GitHubRepo", "Value": "org/repo"}
                    ]
                }]
            }]
        }
        with patch.object(spot_module, 'get_ec2_client', return_value=mock_ec2):
            result = spot_module._get_ec2_instance_tags("i-123")
            assert result["RunId"] == "12345"
            assert result["GitHubRepo"] == "org/repo"

    def test_returns_empty_dict_on_error(self, spot_module):
        """Test that empty dict is returned on error."""
        from botocore.exceptions import ClientError
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "DescribeInstances"
        )
        with patch.object(spot_module, 'get_ec2_client', return_value=mock_ec2):
            result = spot_module._get_ec2_instance_tags("i-123")
            assert result == {}


class TestHandleEc2SpotInterruption:
    """Tests for _handle_ec2_spot_interruption function."""

    def test_returns_error_when_tags_unavailable(self, spot_module):
        """Test that error is returned when tags are unavailable."""
        event = {"detail": {"instance-id": "i-123"}}
        with patch.object(spot_module, '_get_ec2_instance_tags', return_value={}):
            result = spot_module._handle_ec2_spot_interruption(event)
            assert result["statusCode"] == 500

    def test_skips_when_no_run_id(self, spot_module):
        """Test that event is skipped when no run_id in tags."""
        event = {"detail": {"instance-id": "i-123"}}
        with patch.object(spot_module, '_get_ec2_instance_tags', return_value={"Name": "runner"}):
            result = spot_module._handle_ec2_spot_interruption(event)
            assert result["statusCode"] == 200
            assert "No run_id" in result["body"]

    def test_skips_inactive_workflow(self, spot_module):
        """Test that inactive workflow is skipped."""
        event = {"detail": {"instance-id": "i-123"}}
        with patch.object(spot_module, '_get_ec2_instance_tags', return_value={
            "RunId": "12345",
            "GitHubRepo": "org/repo"
        }):
            with patch.object(spot_module, 'get_github_token', return_value="token"):
                with patch.object(spot_module, '_get_workflow_run_status', return_value="completed"):
                    result = spot_module._handle_ec2_spot_interruption(event)
                    assert result["statusCode"] == 200
                    assert "not active" in result["body"]

    def test_returns_error_when_no_token(self, spot_module):
        """Test that error is returned when no GitHub token."""
        event = {"detail": {"instance-id": "i-123"}}
        with patch.object(spot_module, '_get_ec2_instance_tags', return_value={
            "RunId": "12345",
            "GitHubRepo": "org/repo"
        }):
            with patch.object(spot_module, 'get_github_token', return_value=None):
                result = spot_module._handle_ec2_spot_interruption(event)
                assert result["statusCode"] == 500

    def test_initiates_recovery_for_active_workflow(self, spot_module):
        """Test that recovery is initiated for active workflow."""
        event = {"detail": {"instance-id": "i-123"}}
        with patch.object(spot_module, '_get_ec2_instance_tags', return_value={
            "RunId": "12345",
            "GitHubRepo": "org/repo"
        }):
            with patch.object(spot_module, 'get_github_token', return_value="token"):
                with patch.object(spot_module, '_get_workflow_run_status', return_value="in_progress"):
                    with patch.object(spot_module, '_recover_from_spot_interruption', return_value={
                        "statusCode": 200, "body": "Recovery initiated"
                    }):
                        result = spot_module._handle_ec2_spot_interruption(event)
                        assert result["statusCode"] == 200


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_handles_ecs_task_stopped_event(self, spot_module, lambda_context):
        """Test that ECS task stopped event is handled."""
        event = {
            "source": "aws.ecs",
            "detail-type": "ECS Task State Change",
            "detail": {"lastStatus": "STOPPED", "taskArn": "arn:task", "stopCode": "", "stoppedReason": ""}
        }
        with patch.object(spot_module, '_handle_ecs_task_stopped', return_value={"statusCode": 200}):
            result = spot_module.lambda_handler(event, lambda_context)
            assert result["statusCode"] == 200

    def test_handles_ec2_spot_interruption_event(self, spot_module, lambda_context):
        """Test that EC2 spot interruption event is handled."""
        event = {
            "source": "aws.ec2",
            "detail-type": "EC2 Spot Instance Interruption Warning",
            "detail": {"instance-id": "i-123"}
        }
        with patch.object(spot_module, '_handle_ec2_spot_interruption', return_value={"statusCode": 200}):
            result = spot_module.lambda_handler(event, lambda_context)
            assert result["statusCode"] == 200

    def test_ignores_non_stopped_ecs_events(self, spot_module, lambda_context):
        """Test that non-STOPPED ECS events are ignored."""
        event = {
            "source": "aws.ecs",
            "detail-type": "ECS Task State Change",
            "detail": {"lastStatus": "RUNNING"}
        }
        result = spot_module.lambda_handler(event, lambda_context)
        assert result["statusCode"] == 200
        assert "ignored" in result["body"].lower()

    def test_ignores_unrelated_events(self, spot_module, lambda_context):
        """Test that unrelated events are ignored."""
        event = {
            "source": "aws.s3",
            "detail-type": "S3 Object Created"
        }
        result = spot_module.lambda_handler(event, lambda_context)
        assert result["statusCode"] == 200
        assert "ignored" in result["body"].lower()
