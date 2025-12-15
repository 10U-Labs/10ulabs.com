"""Unit tests for agents webhook Lambda handler."""
import json
from unittest.mock import patch, MagicMock

from test.api.endpoints.agents.pre_deployment.unit.conftest import (
    assert_response_status,
    parse_response_body,
)


def create_webhook_event(
    action: str = "completed",
    conclusion: str = "failure",
    workflow_name: str = "Test Workflow",
    run_id: int = 12345,
) -> dict:
    """Create a webhook event for testing."""
    return {
        "body": json.dumps({
            "action": action,
            "workflow_run": {
                "id": run_id,
                "name": workflow_name,
                "conclusion": conclusion,
                "head_sha": "abc123",
                "head_branch": "main",
                "path": ".github/workflows/test.yml",
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-owner"},
            },
        }),
    }


def create_scheduled_event(test_mode: bool = False) -> dict:
    """Create a scheduled EventBridge event for testing."""
    return {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "body": json.dumps({"test_mode": test_mode}),
    }


def create_direct_invocation_event(agent_type: str, **kwargs) -> dict:
    """Create a direct agent invocation event for testing."""
    payload = {"agent_type": agent_type, **kwargs}
    return {"body": json.dumps(payload)}


class TestParseWebhookPayload:
    """Tests for _parse_webhook_payload function."""

    def test_parse_webhook_payload_with_json_string_returns_dict(self, agents_handler):
        """Test parsing JSON string body returns dict."""
        event = {"body": '{"key": "value"}'}
        result = agents_handler._parse_webhook_payload(event)
        assert result == {"key": "value"}

    def test_parse_webhook_payload_with_none_body_returns_empty_dict(
        self, agents_handler
    ):
        """Test parsing None body returns empty dict."""
        event = {"body": None}
        result = agents_handler._parse_webhook_payload(event)
        assert result == {}

    def test_parse_webhook_payload_with_empty_string_returns_empty_dict(
        self, agents_handler
    ):
        """Test parsing empty string body returns empty dict."""
        event = {"body": ""}
        result = agents_handler._parse_webhook_payload(event)
        assert result == {}

    def test_parse_webhook_payload_with_dict_body_returns_dict(self, agents_handler):
        """Test parsing dict body returns dict."""
        event = {"body": {"key": "value"}}
        result = agents_handler._parse_webhook_payload(event)
        assert result == {"key": "value"}


class TestShouldSkipEvent:
    """Tests for _should_skip_event function."""

    def test_should_skip_event_with_non_completed_action_returns_true(
        self, agents_handler
    ):
        """Test non-completed action is skipped."""
        payload = {"action": "in_progress", "workflow_run": {"conclusion": "failure"}}
        should_skip, _ = agents_handler._should_skip_event(payload)
        assert should_skip is True

    def test_should_skip_event_with_non_completed_action_reason_mentions_non_completed(
        self, agents_handler
    ):
        """Test non-completed action reason mentions non-completed."""
        payload = {"action": "in_progress", "workflow_run": {"conclusion": "failure"}}
        _, reason = agents_handler._should_skip_event(payload)
        assert "non-completed" in reason

    def test_should_skip_event_with_success_conclusion_returns_true(
        self, agents_handler
    ):
        """Test successful workflow is skipped."""
        payload = {"action": "completed", "workflow_run": {"conclusion": "success"}}
        should_skip, _ = agents_handler._should_skip_event(payload)
        assert should_skip is True

    def test_should_skip_event_with_success_conclusion_reason_mentions_success(
        self, agents_handler
    ):
        """Test successful workflow reason mentions success."""
        payload = {"action": "completed", "workflow_run": {"conclusion": "success"}}
        _, reason = agents_handler._should_skip_event(payload)
        assert "success" in reason

    def test_should_skip_event_with_agent_workflow_returns_true(self, agents_handler):
        """Test agent workflow is skipped to prevent loops."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "failure", "name": "Agent Workflow"},
        }
        should_skip, _ = agents_handler._should_skip_event(payload)
        assert should_skip is True

    def test_should_skip_event_with_agent_workflow_reason_mentions_agent(
        self, agents_handler
    ):
        """Test agent workflow reason mentions agent."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "failure", "name": "Agent Workflow"},
        }
        _, reason = agents_handler._should_skip_event(payload)
        assert "agent" in reason.lower()

    def test_should_skip_event_with_failed_workflow_returns_false(self, agents_handler):
        """Test failed non-agent workflow is not skipped."""
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "failure", "name": "Build Workflow"},
        }
        should_skip, _ = agents_handler._should_skip_event(payload)
        assert should_skip is False


class TestIsScheduledEvent:
    """Tests for _is_scheduled_event function."""

    def test_is_scheduled_event_with_aws_events_source_returns_true(
        self, agents_handler
    ):
        """Test aws.events source is recognized as scheduled."""
        event = {"source": "aws.events"}
        assert agents_handler._is_scheduled_event(event) is True

    def test_is_scheduled_event_with_detail_type_returns_true(self, agents_handler):
        """Test detail-type presence is recognized as scheduled."""
        event = {"detail-type": "Scheduled Event"}
        assert agents_handler._is_scheduled_event(event) is True

    def test_is_scheduled_event_with_webhook_returns_false(self, agents_handler):
        """Test webhook event is not recognized as scheduled."""
        event = create_webhook_event()
        assert agents_handler._is_scheduled_event(event) is False


class TestIsDirectInvocation:
    """Tests for _is_direct_invocation function."""

    def test_is_direct_invocation_with_agent_type_returns_true(self, agents_handler):
        """Test agent_type in payload is recognized as direct invocation."""
        event = create_direct_invocation_event("troubleshooter_of_workflows")
        assert agents_handler._is_direct_invocation(event) is True

    def test_is_direct_invocation_with_workflow_run_returns_false(self, agents_handler):
        """Test webhook event is not recognized as direct invocation."""
        event = create_webhook_event()
        assert agents_handler._is_direct_invocation(event) is False


class TestBuildAgentPayload:
    """Tests for _build_agent_payload function."""

    def test_build_agent_payload_extracts_run_id(self, agents_handler):
        """Test run_id is extracted from payload."""
        payload = {
            "workflow_run": {
                "id": 12345,
                "name": "Test",
                "head_sha": "abc",
                "head_branch": "main",
            },
            "repository": {"name": "repo", "owner": {"login": "owner"}},
        }
        result = agents_handler._build_agent_payload(payload, "token")
        assert result["run_id"] == 12345

    def test_build_agent_payload_includes_github_token(self, agents_handler):
        """Test github_token is included in payload."""
        payload = {
            "workflow_run": {"id": 1, "name": "Test", "head_sha": "a", "head_branch": "b"},
            "repository": {"name": "repo", "owner": {"login": "owner"}},
        }
        result = agents_handler._build_agent_payload(payload, "test_token")
        assert result["github_token"] == "test_token"


class TestHandleRecommendation:
    """Tests for _handle_recommendation function."""

    def test_handle_recommendation_with_no_recommendation_returns_original(
        self, agents_handler
    ):
        """Test no recommendation returns original result."""
        result = {"status": "success"}
        output = agents_handler._handle_recommendation(result, "token")
        assert output == result

    def test_handle_recommendation_with_create_agent_calls_invoke_agent(
        self, agents_handler
    ):
        """Test create_agent recommendation calls invoke_agent."""
        result = {
            "status": "success",
            "recommendation": "create_agent",
            "create_agent_request": "Create an agent that does X",
        }
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"pr_url": "https://github.com/..."}
            agents_handler._handle_recommendation(result, "token")
            mock_invoke.assert_called_once()

    def test_handle_recommendation_with_create_agent_routes_to_creator(
        self, agents_handler
    ):
        """Test create_agent recommendation routes to creator_of_agents."""
        result = {
            "status": "success",
            "recommendation": "create_agent",
            "create_agent_request": "Create an agent that does X",
        }
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"pr_url": "https://github.com/..."}
            agents_handler._handle_recommendation(result, "token")
            call_args = mock_invoke.call_args
            assert call_args[0][0] == "creator_of_agents"

    def test_handle_recommendation_with_create_agent_returns_routed_to(
        self, agents_handler
    ):
        """Test create_agent recommendation includes routed_to in output."""
        result = {
            "status": "success",
            "recommendation": "create_agent",
            "create_agent_request": "Create an agent that does X",
        }
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"pr_url": "https://github.com/..."}
            output = agents_handler._handle_recommendation(result, "token")
            assert output["routed_to"] == "creator_of_agents"


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    def test_handler_with_scheduled_event_returns_200(self, agents_handler, lambda_context):
        """Test scheduled event returns 200."""
        event = create_scheduled_event(test_mode=True)
        response = agents_handler.lambda_handler(event, lambda_context)
        assert_response_status(response, 200)

    def test_handler_with_scheduled_event_in_test_mode_returns_test_mode_true(
        self, agents_handler, lambda_context
    ):
        """Test scheduled event in test mode returns test_mode true."""
        event = create_scheduled_event(test_mode=True)
        response = agents_handler.lambda_handler(event, lambda_context)
        body = parse_response_body(response)
        assert body.get("test_mode") is True

    def test_handler_with_skipped_webhook_returns_200(
        self, agents_handler, lambda_context
    ):
        """Test skipped webhook event returns 200."""
        event = create_webhook_event(action="in_progress")
        response = agents_handler.lambda_handler(event, lambda_context)
        assert_response_status(response, 200)

    def test_handler_with_empty_payload_returns_200(
        self, agents_handler, lambda_context
    ):
        """Test empty payload is treated as webhook and returns 200."""
        event = {"body": json.dumps({})}
        response = agents_handler.lambda_handler(event, lambda_context)
        assert_response_status(response, 200)

    def test_handler_with_failed_workflow_calls_invoke_agent(
        self, agents_handler, lambda_context
    ):
        """Test failed workflow calls invoke_agent."""
        event = create_webhook_event()
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"result": "success"}
            agents_handler.lambda_handler(event, lambda_context)
            mock_invoke.assert_called()

    def test_handler_with_failed_workflow_invokes_troubleshooter(
        self, agents_handler, lambda_context
    ):
        """Test failed workflow invokes troubleshooter_of_workflows agent."""
        event = create_webhook_event()
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"result": "success"}
            agents_handler.lambda_handler(event, lambda_context)
            call_args = mock_invoke.call_args
            assert call_args[0][0] == "troubleshooter_of_workflows"

    def test_handler_with_failed_workflow_returns_200(
        self, agents_handler, lambda_context
    ):
        """Test failed workflow returns 200."""
        event = create_webhook_event()
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"result": "success"}
            response = agents_handler.lambda_handler(event, lambda_context)
            assert_response_status(response, 200)

    def test_handler_with_direct_invocation_calls_invoke_agent(
        self, agents_handler, lambda_context
    ):
        """Test direct invocation calls invoke_agent."""
        event = create_direct_invocation_event("creator_of_agents", request="test")
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"result": "success"}
            agents_handler.lambda_handler(event, lambda_context)
            mock_invoke.assert_called()

    def test_handler_with_direct_invocation_invokes_specified_agent(
        self, agents_handler, lambda_context
    ):
        """Test direct invocation invokes specified agent."""
        event = create_direct_invocation_event("creator_of_agents", request="test")
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"result": "success"}
            agents_handler.lambda_handler(event, lambda_context)
            call_args = mock_invoke.call_args
            assert call_args[0][0] == "creator_of_agents"

    def test_handler_with_direct_invocation_returns_200(
        self, agents_handler, lambda_context
    ):
        """Test direct invocation returns 200."""
        event = create_direct_invocation_event("creator_of_agents", request="test")
        with patch.object(agents_handler, "invoke_agent") as mock_invoke:
            mock_invoke.return_value = {"result": "success"}
            response = agents_handler.lambda_handler(event, lambda_context)
            assert_response_status(response, 200)

    def test_handler_returns_error_on_exception(self, agents_handler, lambda_context):
        """Test handler returns 500 on exception."""
        event = create_webhook_event()
        with patch.object(
            agents_handler, "invoke_agent", side_effect=ValueError("Test error")
        ):
            response = agents_handler.lambda_handler(event, lambda_context)
            assert_response_status(response, 500)
