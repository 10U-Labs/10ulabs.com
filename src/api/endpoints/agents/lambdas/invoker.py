"""
Invoker Lambda - Handles direct agent invocations from SQS.

Single responsibility: Process direct agent invocation requests with a specific
agent_type parameter, invoking the appropriate agent.

Trigger: SQS (invoke_ingress) <- API Gateway

Note: github_auth and agent_utils are Lambda layers. Stubs provided for type checking.
"""

import json
import logging
from typing import Any

try:
    from agent_utils import invoke_agent, handle_recommendation, process_sqs_records
    from github_auth import get_github_token
except ImportError:
    # Stubs for when Lambda layer is not available (linting/testing)
    from typing import Callable

    def invoke_agent(agent_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Stub."""
        raise NotImplementedError("agent_utils layer not available")

    def handle_recommendation(
        result: dict[str, Any], github_token: str
    ) -> dict[str, Any]:
        """Stub."""
        raise NotImplementedError("agent_utils layer not available")

    def process_sqs_records(
        event: dict[str, Any],
        github_token: str,
        processor: Callable[[dict[str, Any], str], dict[str, Any]],
    ) -> dict[str, Any]:
        """Stub."""
        raise NotImplementedError("agent_utils layer not available")

    def get_github_token() -> str:
        """Stub."""
        raise NotImplementedError("github_auth layer not available")


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _process_invocation(payload: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Process a direct agent invocation."""
    agent_type = payload.get("agent_type")

    if not agent_type:
        return {"status": "error", "error": "agent_type is required for direct invocation"}

    if "github_token" not in payload:
        payload["github_token"] = github_token

    logger.info("Direct invocation of agent: %s", agent_type)
    result = invoke_agent(agent_type, payload)
    result = handle_recommendation(result, github_token)

    return {"status": "processed", "agent_type": agent_type, "result": result}


def _process_record(body: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Process a single SQS record body."""
    payload = body.get("body", body)
    if isinstance(payload, str):
        payload = json.loads(payload)
    return _process_invocation(payload, github_token)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for SQS direct invocation events."""
    return process_sqs_records(event, get_github_token(), _process_record)
