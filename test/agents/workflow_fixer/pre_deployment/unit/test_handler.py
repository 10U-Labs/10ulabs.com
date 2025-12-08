"""Unit tests for workflow_fixer webhook handler logic.

These tests verify the pure logic functions without making AWS or GitHub API calls.
"""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# Import the handler module directly from its file path
# Path: test/agents/workflow_fixer/pre_deployment/unit/test_handler.py
# parents[5] = repo root (10ulabs.com)
HANDLER_PATH = (
    Path(__file__).resolve().parents[5]
    / "src"
    / "agents"
    / "workflow_fixer"
    / "webhook-lambda"
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


class TestShouldSkipEvent:
    """Tests for _should_skip_event function."""

    def test_skips_non_completed_action(self):
        """Should skip events that are not 'completed'."""
        payload = {
            "action": "requested",
            "workflow_run": {"conclusion": "failure"},
        }
        should_skip, reason = _should_skip_event(payload)
        assert should_skip is True
        assert "non-completed" in reason.lower()

    def test_skips_in_progress_action(self):
        """Should skip in_progress events."""
        payload = {
            "action": "in_progress",
            "workflow_run": {"conclusion": None},
        }
        should_skip, reason = _should_skip_event(payload)
        assert should_skip is True
        assert "non-completed" in reason.lower()

    def test_skips_successful_workflow(self):
        """Should skip workflows that completed successfully."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "success"},
        }
        should_skip, reason = _should_skip_event(payload)
        assert should_skip is True
        assert "success" in reason.lower()

    def test_skips_cancelled_workflow(self):
        """Should skip cancelled workflows."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "cancelled"},
        }
        should_skip, reason = _should_skip_event(payload)
        assert should_skip is True
        assert "cancelled" in reason.lower()

    def test_skips_workflow_fixer_workflow(self):
        """Should skip workflow-fixer workflows to avoid loops."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "Deploying Workflow-Fixer Agent",
                "conclusion": "failure",
            },
        }
        should_skip, reason = _should_skip_event(payload)
        assert should_skip is True
        assert "workflow-fixer" in reason.lower()

    def test_skips_workflow_fixer_case_insensitive(self):
        """Should skip workflow-fixer workflows regardless of case."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "WORKFLOW-FIXER Deploy",
                "conclusion": "failure",
            },
        }
        should_skip, reason = _should_skip_event(payload)
        assert should_skip is True
        assert "workflow-fixer" in reason.lower()

    def test_does_not_skip_failed_workflow(self):
        """Should NOT skip failed workflows (this is what we want to process)."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "name": "CI Build",
                "conclusion": "failure",
            },
        }
        should_skip, reason = _should_skip_event(payload)
        assert should_skip is False
        assert reason == ""

    def test_handles_missing_workflow_run(self):
        """Should handle missing workflow_run key gracefully."""
        payload = {"action": "completed"}
        should_skip, reason = _should_skip_event(payload)
        # Should skip because conclusion is None
        assert should_skip is True

    def test_handles_empty_payload(self):
        """Should handle empty payload gracefully."""
        payload = {}
        should_skip, reason = _should_skip_event(payload)
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


class TestBuildAgentPayload:
    """Tests for _build_agent_payload function."""

    def test_builds_payload_from_webhook(self):
        """Should build agent payload from webhook event."""
        payload = {
            "workflow_run": {
                "id": 12345,
                "name": "CI Build",
                "path": ".github/workflows/ci.yml",
                "head_sha": "abc123",
                "head_branch": "main",
            },
            "repository": {
                "name": "my-repo",
                "owner": {"login": "my-org"},
            },
        }
        github_token = "ghp_test123"

        result = _build_agent_payload(payload, github_token)

        assert result["github_token"] == "ghp_test123"
        assert result["owner"] == "my-org"
        assert result["repo"] == "my-repo"
        assert result["run_id"] == 12345
        assert result["workflow_name"] == "CI Build"
        assert result["workflow_path"] == ".github/workflows/ci.yml"
        assert result["head_sha"] == "abc123"
        assert result["head_branch"] == "main"

    def test_handles_missing_optional_fields(self):
        """Should handle missing optional fields gracefully."""
        payload = {
            "workflow_run": {"id": 12345},
            "repository": {"name": "repo", "owner": {"login": "org"}},
        }
        github_token = "ghp_test123"

        result = _build_agent_payload(payload, github_token)

        assert result["run_id"] == 12345
        assert result["workflow_name"] is None
        assert result["workflow_path"] == ""
        assert result["head_sha"] is None
        assert result["head_branch"] is None


class TestBuildAgentPayloadFromRun:
    """Tests for _build_agent_payload_from_run function."""

    def test_builds_payload_from_run_object(self):
        """Should build agent payload from workflow run object."""
        run = {
            "id": 12345,
            "name": "CI Build",
            "path": ".github/workflows/ci.yml",
            "head_sha": "abc123",
            "head_branch": "main",
        }
        github_token = "ghp_test123"

        result = _build_agent_payload_from_run(run, github_token)

        assert result["github_token"] == "ghp_test123"
        assert result["owner"] == "10U-Labs-LLC"  # Default from handler
        assert result["repo"] == "10ulabs.com"    # Default from handler
        assert result["run_id"] == 12345
        assert result["workflow_name"] == "CI Build"
        assert result["workflow_path"] == ".github/workflows/ci.yml"
        assert result["head_sha"] == "abc123"
        assert result["head_branch"] == "main"

    def test_handles_missing_fields(self):
        """Should handle missing fields gracefully."""
        run = {"id": 12345}
        github_token = "ghp_test123"

        result = _build_agent_payload_from_run(run, github_token)

        assert result["run_id"] == 12345
        assert result["workflow_name"] is None
        assert result["workflow_path"] == ""


class TestLambdaHandlerModes:
    """Tests for lambda_handler mode detection."""

    @patch("handler.get_github_pat")
    @patch("handler._handle_scheduled_scan")
    def test_detects_scheduled_event_by_source(self, mock_scan, mock_pat):
        """Should detect scheduled event by aws.events source."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_scan.return_value = {"statusCode": 200, "body": "{}"}

        event = {"source": "aws.events"}
        lambda_handler(event, None)

        mock_scan.assert_called_once_with("ghp_test")

    @patch("handler.get_github_pat")
    @patch("handler._handle_scheduled_scan")
    def test_detects_scheduled_event_by_detail_type(self, mock_scan, mock_pat):
        """Should detect scheduled event by detail-type."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_scan.return_value = {"statusCode": 200, "body": "{}"}

        event = {"detail-type": "Scheduled Event"}
        lambda_handler(event, None)

        mock_scan.assert_called_once_with("ghp_test")

    @patch("handler.get_github_pat")
    @patch("handler._handle_webhook_event")
    def test_defaults_to_webhook_mode(self, mock_webhook, mock_pat):
        """Should default to webhook mode for regular events."""
        from handler import lambda_handler

        mock_pat.return_value = "ghp_test"
        mock_webhook.return_value = {"statusCode": 200, "body": "{}"}

        event = {"body": "{}"}
        lambda_handler(event, None)

        mock_webhook.assert_called_once()
