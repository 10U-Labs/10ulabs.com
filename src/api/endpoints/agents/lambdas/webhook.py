"""
Webhook Lambda - Processes GitHub workflow failure events from SQS.

Single responsibility: Handle incoming GitHub webhook events for workflow failures
and invoke the troubleshooter agent.

Trigger: SQS (webhook_ingress) <- API Gateway

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


def _parse_webhook_payload(body: str | dict[str, Any]) -> dict[str, Any]:
    """Parse the webhook payload."""
    if body is None or body == "":
        return {}
    if isinstance(body, str):
        return json.loads(body)
    return body if body else {}


def _should_skip_event(payload: dict[str, Any]) -> tuple[bool, str]:
    """Check if event should be skipped. Returns (should_skip, reason)."""
    action = payload.get("action")
    workflow_run = payload.get("workflow_run", {})

    if action != "completed":
        return True, "Ignoring non-completed event"

    conclusion = workflow_run.get("conclusion")
    if conclusion != "failure":
        return True, f"Ignoring {conclusion} workflow"

    workflow_name = workflow_run.get("name", "")
    if "agent" in workflow_name.lower():
        return True, "Ignoring agent workflow"

    return False, ""


def _build_agent_payload(payload: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Build the payload for the troubleshooter agent."""
    workflow_run = payload.get("workflow_run", {})
    repo = payload.get("repository", {})

    return {
        "github_token": github_token,
        "owner": repo.get("owner", {}).get("login"),
        "repo": repo.get("name"),
        "run_id": workflow_run.get("id"),
        "workflow_name": workflow_run.get("name"),
        "workflow_path": workflow_run.get("path", ""),
        "head_sha": workflow_run.get("head_sha"),
        "head_branch": workflow_run.get("head_branch"),
    }


def _process_webhook_event(payload: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Process a single webhook event."""
    should_skip, reason = _should_skip_event(payload)

    if should_skip:
        return {"status": "skipped", "reason": reason}

    workflow_run = payload.get("workflow_run", {})
    repo = payload.get("repository", {})
    logger.info(
        "Processing failed workflow: %s (run %s) in %s/%s",
        workflow_run.get("name"),
        workflow_run.get("id"),
        repo.get("owner", {}).get("login"),
        repo.get("name"),
    )

    agent_payload = _build_agent_payload(payload, github_token)
    result = invoke_agent("troubleshooter_of_workflows", agent_payload)
    result = handle_recommendation(result, github_token)

    logger.info("Agent result: %s", json.dumps(result, indent=2))

    return {"status": "processed", "result": result}


def _process_record(body: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Process a single SQS record body."""
    payload = _parse_webhook_payload(body.get("body", body))
    return _process_webhook_event(payload, github_token)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for SQS webhook events."""
    return process_sqs_records(event, get_github_token(), _process_record)
