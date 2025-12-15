"""Unit tests for troubleshooter_of_workflows webhook handler logic.

These tests verify the pure logic functions without making AWS or GitHub API calls.
"""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# Mock github_auth module before importing handler (it's provided by Lambda layer at runtime)
mock_github_auth = MagicMock()
mock_github_auth.get_github_token = MagicMock(return_value="mock_token")
sys.modules["github_auth"] = mock_github_auth

# Import the handler module directly from its file path
# Path: test/api/endpoints/agents/troubleshooter_of_workflows/pre_deployment/unit/test_handler.py
# parents[7] = repo root (10ulabs.com)
HANDLER_PATH = (
    Path(__file__).resolve().parents[7]
    / "src"
    / "api"
    / "endpoints"
    / "agents"
    / "troubleshooter_of_workflows"
    / "lambda"
    / "handler.py"
)
spec = importlib.util.spec_from_file_location("handler", HANDLER_PATH)
handler = importlib.util.module_from_spec(spec)
sys.modules["handler"] = handler
spec.loader.exec_module(handler)

_should_skip_event = handler._should_skip_event
_parse_webhook_payload = handler._parse_webhook_payload
_build_agent_payload = handler._build_agent_payload
_build_agent_payload_from_run = handler._build_agent_payload_from_run
_is_scheduled_event = handler._is_scheduled_event
_handle_scheduled_scan = handler._handle_scheduled_scan


class TestHandleScheduledScanTestModeReturnValue:
    """Tests for _handle_scheduled_scan test_mode return value."""

    def test_test_mode_returns_status_code_200(self):
        """Should return status code 200 when test_mode=True."""
        result = _handle_scheduled_scan("fake_token", test_mode=True)
        assert result["statusCode"] == 200

    def test_test_mode_returns_mode_scheduled(self):
        """Should return mode=scheduled when test_mode=True."""
        result = _handle_scheduled_scan("fake_token", test_mode=True)
        body = json.loads(result["body"])
        assert body["mode"] == "scheduled"

    def test_test_mode_returns_processed_zero(self):
        """Should return processed=0 when test_mode=True."""
        result = _handle_scheduled_scan("fake_token", test_mode=True)
        body = json.loads(result["body"])
        assert body["processed"] == 0

    def test_test_mode_returns_test_mode_true(self):
        """Should return test_mode=True in body when test_mode=True."""
        result = _handle_scheduled_scan("fake_token", test_mode=True)
        body = json.loads(result["body"])
        assert body["test_mode"] is True


class TestHandleScheduledScanTestModeNoApiCalls:
    """Tests for _handle_scheduled_scan test_mode not calling APIs."""

    def test_test_mode_does_not_call_github_api_returns_200(self):
        """Should return 200 without calling GitHub API when test_mode=True."""
        result = _handle_scheduled_scan("invalid_token_that_would_fail", test_mode=True)
        assert result["statusCode"] == 200

    def test_test_mode_does_not_call_github_api_returns_test_mode(self):
        """Should return test_mode=True without calling GitHub API."""
        result = _handle_scheduled_scan("invalid_token_that_would_fail", test_mode=True)
        body = json.loads(result["body"])
        assert body["test_mode"] is True


class TestShouldSkipEventNonCompleted:
    """Tests for _should_skip_event with non-completed actions."""

    def test_skips_non_completed_action(self):
        """Should skip events that are not 'completed'."""
        payload = {
            "action": "requested",
            "workflow_run": {"conclusion": "failure"},
        }
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True

    def test_skips_non_completed_action_reason(self):
        """Should include 'non-completed' in skip reason."""
        payload = {
            "action": "requested",
            "workflow_run": {"conclusion": "failure"},
        }
        _, reason = _should_skip_event(payload)
        assert "non-completed" in reason.lower()

    def test_skips_in_progress_action(self):
        """Should skip in_progress events."""
        payload = {
            "action": "in_progress",
            "workflow_run": {"conclusion": None},
        }
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True

    def test_skips_in_progress_action_reason(self):
        """Should include 'non-completed' in skip reason for in_progress."""
        payload = {
            "action": "in_progress",
            "workflow_run": {"conclusion": None},
        }
        _, reason = _should_skip_event(payload)
        assert "non-completed" in reason.lower()


class TestShouldSkipEventConclusions:
    """Tests for _should_skip_event with various conclusions."""

    def test_skips_successful_workflow(self):
        """Should skip workflows that completed successfully."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "success"},
        }
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True

    def test_skips_successful_workflow_reason(self):
        """Should include 'success' in skip reason."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "success"},
        }
        _, reason = _should_skip_event(payload)
        assert "success" in reason.lower()

    def test_skips_cancelled_workflow(self):
        """Should skip cancelled workflows."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "cancelled"},
        }
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True

    def test_skips_cancelled_workflow_reason(self):
        """Should include 'cancelled' in skip reason."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "cancelled"},
        }
        _, reason = _should_skip_event(payload)
        assert "cancelled" in reason.lower()


class TestShouldSkipEventTroubleshooter:
    """Tests for _should_skip_event with troubleshooter-of-workflows workflows."""

    def test_skips_troubleshooter_of_workflows_workflow(self):
        """Should skip troubleshooter-of-workflows workflows to avoid loops."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "Deploying Troubleshooter-of-Workflows Agent",
                "conclusion": "failure",
            },
        }
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True

    def test_skips_troubleshooter_of_workflows_workflow_reason(self):
        """Should include 'troubleshooter-of-workflows' in skip reason."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "Deploying Troubleshooter-of-Workflows Agent",
                "conclusion": "failure",
            },
        }
        _, reason = _should_skip_event(payload)
        assert "troubleshooter-of-workflows" in reason.lower()

    def test_skips_troubleshooter_of_workflows_case_insensitive(self):
        """Should skip troubleshooter-of-workflows workflows regardless of case."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "TROUBLESHOOTER-OF-WORKFLOWS Deploy",
                "conclusion": "failure",
            },
        }
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True

    def test_skips_troubleshooter_of_workflows_case_insensitive_reason(self):
        """Should include 'troubleshooter-of-workflows' in skip reason regardless of case."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "TROUBLESHOOTER-OF-WORKFLOWS Deploy",
                "conclusion": "failure",
            },
        }
        _, reason = _should_skip_event(payload)
        assert "troubleshooter-of-workflows" in reason.lower()


class TestShouldSkipEventFailedWorkflow:
    """Tests for _should_skip_event with failed workflows."""

    def test_does_not_skip_failed_workflow(self):
        """Should NOT skip failed workflows (this is what we want to process)."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "CI Build",
                "conclusion": "failure",
            },
        }
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is False

    def test_does_not_skip_failed_workflow_empty_reason(self):
        """Should return empty reason for failed workflows."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "CI Build",
                "conclusion": "failure",
            },
        }
        _, reason = _should_skip_event(payload)
        assert reason == ""


class TestShouldSkipEventEdgeCases:
    """Tests for _should_skip_event edge cases."""

    def test_handles_missing_workflow_run(self):
        """Should handle missing workflow_run key gracefully."""
        payload = {"action": "completed"}
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True

    def test_handles_empty_payload(self):
        """Should handle empty payload gracefully."""
        payload = {}
        should_skip, _ = _should_skip_event(payload)
        assert should_skip is True


class TestParseWebhookPayload:
    """Tests for _parse_webhook_payload function."""

    def test_parses_string_body(self):
        """Should parse JSON string body."""
        event = {"body": '{"action": "completed"}'}
        result = _parse_webhook_payload(event)
        assert result == {"action": "completed"}

    def test_parses_dict_body(self):
        """Should return dict body as-is."""
        event = {"body": {"action": "completed"}}
        result = _parse_webhook_payload(event)
        assert result == {"action": "completed"}

    def test_handles_missing_body(self):
        """Should return empty dict for missing body."""
        event = {}
        result = _parse_webhook_payload(event)
        assert result == {}

    def test_handles_empty_string_body(self):
        """Should return empty dict for empty string body."""
        event = {"body": ""}
        result = _parse_webhook_payload(event)
        assert result == {}

    def test_handles_null_body(self):
        """Should return empty dict for null body."""
        event = {"body": None}
        result = _parse_webhook_payload(event)
        assert result == {}


class TestBuildAgentPayloadGithubToken:
    """Tests for _build_agent_payload github_token field."""

    def test_builds_payload_github_token(self):
        """Should include github_token in payload."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["github_token"] == "ghp_test123"


class TestBuildAgentPayloadRepository:
    """Tests for _build_agent_payload repository fields."""

    def test_builds_payload_owner(self):
        """Should include owner in payload."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["owner"] == "my-org"

    def test_builds_payload_repo(self):
        """Should include repo in payload."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["repo"] == "my-repo"


class TestBuildAgentPayloadWorkflowRun:
    """Tests for _build_agent_payload workflow_run fields."""

    def test_builds_payload_run_id(self):
        """Should include run_id in payload."""
        payload = {
            "workflow_run": {"id": 12345, "name": "CI Build"},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["run_id"] == 12345

    def test_builds_payload_workflow_name(self):
        """Should include workflow_name in payload."""
        payload = {
            "workflow_run": {"id": 12345, "name": "CI Build"},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["workflow_name"] == "CI Build"

    def test_builds_payload_workflow_path(self):
        """Should include workflow_path in payload."""
        payload = {
            "workflow_run": {"id": 12345, "path": ".github/workflows/ci.yml"},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["workflow_path"] == ".github/workflows/ci.yml"

    def test_builds_payload_head_sha(self):
        """Should include head_sha in payload."""
        payload = {
            "workflow_run": {"id": 12345, "head_sha": "abc123"},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["head_sha"] == "abc123"

    def test_builds_payload_head_branch(self):
        """Should include head_branch in payload."""
        payload = {
            "workflow_run": {"id": 12345, "head_branch": "main"},
            "repository": {"name": "my-repo", "owner": {"login": "my-org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["head_branch"] == "main"


class TestBuildAgentPayloadMissingFields:
    """Tests for _build_agent_payload with missing optional fields."""

    def test_handles_missing_run_id(self):
        """Should include run_id even when minimal fields provided."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "repo", "owner": {"login": "org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["run_id"] == 12345

    def test_handles_missing_workflow_name(self):
        """Should handle missing workflow_name gracefully."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "repo", "owner": {"login": "org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["workflow_name"] is None

    def test_handles_missing_workflow_path(self):
        """Should handle missing workflow_path gracefully."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "repo", "owner": {"login": "org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["workflow_path"] == ""

    def test_handles_missing_head_sha(self):
        """Should handle missing head_sha gracefully."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "repo", "owner": {"login": "org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["head_sha"] is None

    def test_handles_missing_head_branch(self):
        """Should handle missing head_branch gracefully."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "repo", "owner": {"login": "org"}},
        }
        result = _build_agent_payload(payload, "ghp_test123")
        assert result["head_branch"] is None


class TestBuildAgentPayloadFromRunBasicFields:
    """Tests for _build_agent_payload_from_run basic fields."""

    def test_builds_payload_github_token(self):
        """Should include github_token in payload."""
        run = {"id": 12345}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["github_token"] == "ghp_test123"

    def test_builds_payload_owner(self):
        """Should include default owner in payload."""
        run = {"id": 12345}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["owner"] == "10U-Labs-LLC"

    def test_builds_payload_repo(self):
        """Should include default repo in payload."""
        run = {"id": 12345}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["repo"] == "10ulabs.com"

    def test_builds_payload_run_id(self):
        """Should include run_id in payload."""
        run = {"id": 12345}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["run_id"] == 12345


class TestBuildAgentPayloadFromRunWorkflowFields:
    """Tests for _build_agent_payload_from_run workflow fields."""

    def test_builds_payload_workflow_name(self):
        """Should include workflow_name in payload."""
        run = {"id": 12345, "name": "CI Build"}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["workflow_name"] == "CI Build"

    def test_builds_payload_workflow_path(self):
        """Should include workflow_path in payload."""
        run = {"id": 12345, "path": ".github/workflows/ci.yml"}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["workflow_path"] == ".github/workflows/ci.yml"

    def test_builds_payload_head_sha(self):
        """Should include head_sha in payload."""
        run = {"id": 12345, "head_sha": "abc123"}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["head_sha"] == "abc123"

    def test_builds_payload_head_branch(self):
        """Should include head_branch in payload."""
        run = {"id": 12345, "head_branch": "main"}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["head_branch"] == "main"


class TestBuildAgentPayloadFromRunMissingFields:
    """Tests for _build_agent_payload_from_run with missing fields."""

    def test_handles_missing_workflow_name(self):
        """Should handle missing workflow_name gracefully."""
        run = {"id": 12345}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["workflow_name"] is None

    def test_handles_missing_workflow_path(self):
        """Should handle missing workflow_path gracefully."""
        run = {"id": 12345}
        result = _build_agent_payload_from_run(run, "ghp_test123")
        assert result["workflow_path"] == ""


class TestIsScheduledEvent:
    """Tests for _is_scheduled_event function."""

    def test_detects_direct_eventbridge_by_source(self):
        """Should detect direct EventBridge invocation by source."""
        event = {"source": "aws.events"}
        assert _is_scheduled_event(event) is True

    def test_detects_direct_eventbridge_by_detail_type(self):
        """Should detect direct EventBridge invocation by detail-type."""
        event = {"detail-type": "Scheduled Event"}
        assert _is_scheduled_event(event) is True

    def test_detects_eventbridge_via_http_body_source(self):
        """Should detect EventBridge event in HTTP body by source."""
        event = {"body": json.dumps({"source": "aws.events"})}
        assert _is_scheduled_event(event) is True

    def test_detects_eventbridge_via_http_body_detail_type(self):
        """Should detect EventBridge event in HTTP body by detail-type."""
        event = {"body": json.dumps({"detail-type": "Scheduled Event"})}
        assert _is_scheduled_event(event) is True

    def test_detects_eventbridge_via_http_body_both_fields(self):
        """Should detect EventBridge event in HTTP body with both fields."""
        event = {
            "body": json.dumps({
                "source": "aws.events",
                "detail-type": "Scheduled Event",
            })
        }
        assert _is_scheduled_event(event) is True

    def test_returns_false_for_webhook_event(self):
        """Should return False for GitHub webhook events."""
        event = {
            "body": json.dumps({
                "action": "completed",
                "workflow_run": {"conclusion": "failure"},
            })
        }
        assert _is_scheduled_event(event) is False

    def test_returns_false_for_empty_event(self):
        """Should return False for empty event."""
        assert _is_scheduled_event({}) is False

    def test_returns_false_for_empty_body(self):
        """Should return False for empty body."""
        event = {"body": ""}
        assert _is_scheduled_event(event) is False


class TestLambdaHandlerModes:
    """Tests for lambda_handler mode detection."""

    @patch("handler.get_github_token")
    @patch("handler._handle_scheduled_scan")
    def test_detects_scheduled_event_by_source(self, mock_scan, mock_pat):
        """Should detect scheduled event by aws.events source."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_scan.return_value = {"statusCode": 200, "body": "{}"}

        event = {"source": "aws.events"}
        lambda_handler(event, None)

        mock_scan.assert_called_once_with("ghp_test", test_mode=False)

    @patch("handler.get_github_token")
    @patch("handler._handle_scheduled_scan")
    def test_detects_scheduled_event_by_detail_type(self, mock_scan, mock_pat):
        """Should detect scheduled event by detail-type."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_scan.return_value = {"statusCode": 200, "body": "{}"}

        event = {"detail-type": "Scheduled Event"}
        lambda_handler(event, None)

        mock_scan.assert_called_once_with("ghp_test", test_mode=False)

    @patch("handler.get_github_token")
    @patch("handler._handle_scheduled_scan")
    def test_detects_scheduled_event_via_http_body(self, mock_scan, mock_pat):
        """Should detect scheduled event via HTTP body (Lambda function URL)."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_scan.return_value = {"statusCode": 200, "body": "{}"}

        event = {"body": json.dumps({"source": "aws.events", "detail-type": "Scheduled Event"})}
        lambda_handler(event, None)

        mock_scan.assert_called_once_with("ghp_test", test_mode=False)

    @patch("handler.get_github_token")
    @patch("handler._handle_scheduled_scan")
    def test_passes_test_mode_from_body(self, mock_scan, mock_pat):
        """Should pass test_mode=True from HTTP body to scheduled scan."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_scan.return_value = {"statusCode": 200, "body": "{}"}

        event = {"body": json.dumps({
            "source": "aws.events",
            "detail-type": "Scheduled Event",
            "test_mode": True,
        })}
        lambda_handler(event, None)

        mock_scan.assert_called_once_with("ghp_test", test_mode=True)

    @patch("handler.get_github_token")
    @patch("handler._handle_scheduled_scan")
    def test_passes_test_mode_from_event(self, mock_scan, mock_pat):
        """Should pass test_mode=True from event directly."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_scan.return_value = {"statusCode": 200, "body": "{}"}

        event = {"source": "aws.events", "test_mode": True}
        lambda_handler(event, None)

        mock_scan.assert_called_once_with("ghp_test", test_mode=True)

    @patch("handler.get_github_token")
    @patch("handler._handle_webhook_event")
    def test_defaults_to_webhook_mode(self, mock_webhook, mock_pat):
        """Should default to webhook mode for regular events."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_webhook.return_value = {"statusCode": 200, "body": "{}"}

        event = {"body": "{}"}
        lambda_handler(event, None)

        mock_webhook.assert_called_once()
