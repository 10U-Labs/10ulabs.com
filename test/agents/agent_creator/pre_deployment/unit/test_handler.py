"""Unit tests for agent_creator webhook handler logic.

These tests verify the pure logic functions without making AWS API calls.
"""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# Import the handler module directly from its file path
# Path: test/agents/agent_creator/pre_deployment/unit/test_handler.py
# parents[5] = repo root (10ulabs.com)
HANDLER_PATH = (
    Path(__file__).resolve().parents[5]
    / "src"
    / "agents"
    / "agent_creator"
    / "webhook_lambda"
    / "handler.py"
)
spec = importlib.util.spec_from_file_location("handler", HANDLER_PATH)
handler = importlib.util.module_from_spec(spec)
sys.modules["handler"] = handler
spec.loader.exec_module(handler)


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    @patch("handler.invoke_agent")
    def test_handles_direct_invocation(self, mock_invoke):
        """Should handle direct Lambda invocation with request in event."""
        from handler import lambda_handler

        mock_invoke.return_value = {"status": "success"}

        event = {"request": "Create a new agent"}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["result"]["status"] == "success"
        mock_invoke.assert_called_once_with({"request": "Create a new agent"})

    @patch("handler.invoke_agent")
    def test_handles_http_invocation(self, mock_invoke):
        """Should handle HTTP invocation with request in body."""
        from handler import lambda_handler

        mock_invoke.return_value = {"status": "success"}

        event = {"body": json.dumps({"request": "Create a new agent"})}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["result"]["status"] == "success"

    @patch("handler.invoke_agent")
    def test_handles_http_with_dict_body(self, mock_invoke):
        """Should handle HTTP invocation with dict body (API Gateway v2)."""
        from handler import lambda_handler

        mock_invoke.return_value = {"status": "success"}

        event = {"body": {"request": "Create a new agent"}}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 200

    def test_returns_400_for_missing_request(self):
        """Should return 400 when no request is provided."""
        from handler import lambda_handler

        event = {"body": "{}"}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "error" in body
        assert "No request provided" in body["error"]

    def test_returns_400_for_empty_request(self):
        """Should return 400 when request is empty."""
        from handler import lambda_handler

        event = {"body": json.dumps({"request": ""})}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 400

    def test_handles_empty_body(self):
        """Should handle empty body gracefully (returns 500 for JSON parse error)."""
        from handler import lambda_handler

        event = {"body": ""}
        result = lambda_handler(event, None)

        # Empty string causes JSONDecodeError which is caught and returns 500
        assert result["statusCode"] == 500

    @patch("handler.invoke_agent")
    def test_handles_agent_error(self, mock_invoke):
        """Should handle errors from agent invocation."""
        from handler import lambda_handler
        from botocore.exceptions import ClientError

        mock_invoke.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Agent error"}},
            "invoke_agent_runtime"
        )

        event = {"request": "Create a new agent"}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "error" in body


class TestInvokeAgent:
    """Tests for invoke_agent function."""

    @patch("handler.boto3.client")
    @patch.dict("os.environ", {"AGENT_RUNTIME_ARN": "arn:aws:bedrock:us-east-2:123:agent/test"})
    def test_invokes_bedrock_agent(self, mock_boto):
        """Should invoke the Bedrock agent with correct payload."""
        from handler import invoke_agent

        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke_agent_runtime.return_value = {
            "response": [b'{"status": "done"}']
        }

        result = invoke_agent({"request": "test"})

        mock_client.invoke_agent_runtime.assert_called_once()
        call_kwargs = mock_client.invoke_agent_runtime.call_args[1]
        assert call_kwargs["agentRuntimeArn"] == "arn:aws:bedrock:us-east-2:123:agent/test"
        assert call_kwargs["contentType"] == "application/json"

    @patch("handler.boto3.client")
    @patch.dict("os.environ", {}, clear=True)
    def test_raises_error_for_missing_agent_arn(self, mock_boto):
        """Should raise ValueError when AGENT_RUNTIME_ARN is not set."""
        from handler import invoke_agent

        with pytest.raises(ValueError, match="AGENT_RUNTIME_ARN"):
            invoke_agent({"request": "test"})
