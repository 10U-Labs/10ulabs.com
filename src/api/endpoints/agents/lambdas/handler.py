"""
Agent Webhook Handler - Routes requests to AgentCore runtime.

This Lambda handles:
1. GitHub webhook events (workflow failures) -> troubleshooter_of_workflows
2. Scheduled scans for unresolved failures -> troubleshooter_of_workflows
3. Direct agent invocation with agent_type parameter
4. Orchestration: routes to other agents based on recommendations

Agents return results with optional recommendations:
{
    "result": "...",
    "recommendation": "create_agent",  # Optional
    "create_agent_request": "..."      # Details for agent creation
}

When a recommendation is present, this handler routes to the appropriate agent.

Note: github_auth is a Lambda layer. Stub provided for type checking.
"""

import json
import logging
import os
import random
import time
import traceback
import urllib.request
import urllib.error
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Lambda layer import - stub provided for type checking
try:
    from github_auth import get_github_token
except ImportError:

    def get_github_token() -> str:
        """Stub for when Lambda layer is not available."""
        raise NotImplementedError("github_auth layer not available")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

GITHUB_ORG = os.environ.get("GITHUB_ORG", "10U-Labs-LLC")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "10ulabs.com")


def _github_api_request(
    endpoint: str, token: str, method: str = "GET"
) -> dict[str, Any]:
    """Make a request to the GitHub API."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AgentWebhook/1.0",
    }

    req = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8") if err.fp else ""
        raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err


def _get_unresolved_failures(token: str) -> list[dict[str, Any]]:
    """Find workflow runs that failed and haven't been successfully re-run."""
    endpoint = f"/repos/{GITHUB_ORG}/{GITHUB_REPO}/actions/runs?status=failure&per_page=50"
    response = _github_api_request(endpoint, token)

    unresolved = []
    for run in response.get("workflow_runs", []):
        workflow_id = run["workflow_id"]
        head_branch = run["head_branch"]

        # Check if there's a more recent successful run for this workflow+branch
        check_endpoint = (
            f"/repos/{GITHUB_ORG}/{GITHUB_REPO}/actions/workflows/{workflow_id}/runs"
            f"?branch={head_branch}&status=success&per_page=1"
        )
        try:
            success_response = _github_api_request(check_endpoint, token)
            success_runs = success_response.get("workflow_runs", [])

            if success_runs:
                latest_success = success_runs[0]
                if latest_success["created_at"] > run["created_at"]:
                    continue  # Already fixed

            # Skip agent workflows to avoid loops
            workflow_name = run.get("name", "").lower()
            if "agent" in workflow_name:
                continue

            unresolved.append(run)
        except RuntimeError:
            continue  # Skip if we can't check

    return unresolved


def invoke_agent(agent_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke the AgentCore runtime with a specific agent type."""
    client = boto3.client(
        "bedrock-agentcore", region_name=os.environ.get("AWS_REGION_NAME", "us-east-2")
    )

    agent_arn = os.environ.get("AGENT_RUNTIME_ARN")
    if not agent_arn:
        raise ValueError("AGENT_RUNTIME_ARN environment variable not set")

    # Add agent_type to payload so runtime knows which prompt to load
    payload["agent_type"] = agent_type

    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        payload=json.dumps(payload).encode("utf-8"),
        contentType="application/json",
    )

    content = []
    response_body = response.get("response")
    if response_body:
        for chunk in response_body:
            if isinstance(chunk, bytes):
                content.append(chunk.decode("utf-8"))
            else:
                content.append(str(chunk))

    return json.loads("".join(content)) if content else {}


def _handle_recommendation(result: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Handle agent recommendations by routing to appropriate agents."""
    recommendation = result.get("recommendation")

    if recommendation == "create_agent":
        # Route to creator_of_agents
        create_request = result.get("create_agent_request", {})
        if isinstance(create_request, str):
            create_request = {"request": create_request}

        create_request["github_token"] = github_token
        logger.info("Routing to creator_of_agents: %s", create_request.get("request", "")[:100])

        creator_result = invoke_agent("creator_of_agents", create_request)
        return {
            "original_result": result,
            "creator_result": creator_result,
            "routed_to": "creator_of_agents",
        }

    # No recommendation or unknown recommendation - return original result
    return result


def _parse_webhook_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Parse the webhook payload from the event."""
    body = event.get("body")
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


def _build_agent_payload(
    payload: dict[str, Any], github_token: str
) -> dict[str, Any]:
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


def _build_agent_payload_from_run(
    run: dict[str, Any], github_token: str
) -> dict[str, Any]:
    """Build agent payload from a workflow run object."""
    return {
        "github_token": github_token,
        "owner": GITHUB_ORG,
        "repo": GITHUB_REPO,
        "run_id": run.get("id"),
        "workflow_name": run.get("name"),
        "workflow_path": run.get("path", ""),
        "head_sha": run.get("head_sha"),
        "head_branch": run.get("head_branch"),
    }


def _handle_scheduled_scan(
    github_token: str, test_mode: bool = False
) -> dict[str, Any]:
    """Handle scheduled scan for unresolved failures."""
    logger.info("Running scheduled scan for unresolved workflow failures")

    if test_mode:
        logger.info("Test mode enabled, skipping actual scan")
        return {
            "statusCode": 200,
            "body": json.dumps({"mode": "scheduled", "processed": 0, "test_mode": True}),
        }

    unresolved = _get_unresolved_failures(github_token)
    logger.info("Found %d unresolved failures", len(unresolved))

    results = []
    for run in unresolved:
        logger.info("Processing unresolved failure: %s (run %s)", run["name"], run["id"])

        # Initial random delay 0-30 seconds to avoid thundering herd
        initial_delay = random.uniform(0, 30)
        logger.info("Initial delay of %.1fs before processing run %s", initial_delay, run["id"])
        time.sleep(initial_delay)

        # Process with exponential backoff
        max_attempts = 7
        for attempt in range(max_attempts):
            try:
                agent_payload = _build_agent_payload_from_run(run, github_token)
                result = invoke_agent("troubleshooter_of_workflows", agent_payload)

                # Handle any recommendations
                result = _handle_recommendation(result, github_token)

                results.append({"run_id": run["id"], "status": "processed", "result": result})
                break
            except (ClientError, ValueError) as err:
                if attempt < max_attempts - 1:
                    backoff = 2 ** (4 + attempt)
                    logger.warning(
                        "Attempt %d/%d failed for run %s, retrying in %ds: %s",
                        attempt + 1,
                        max_attempts,
                        run["id"],
                        backoff,
                        err,
                    )
                    time.sleep(backoff)
                else:
                    logger.error(
                        "All %d retries exhausted for run %s: %s", max_attempts, run["id"], err
                    )
                    results.append({"run_id": run["id"], "status": "error", "error": str(err)})

    return {
        "statusCode": 200,
        "body": json.dumps({"mode": "scheduled", "processed": len(results), "results": results}),
    }


def _handle_webhook_event(event: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Handle webhook event for a new failure."""
    payload = _parse_webhook_payload(event)
    should_skip, reason = _should_skip_event(payload)

    if should_skip:
        return {"statusCode": 200, "body": json.dumps({"message": reason})}

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

    # Handle any recommendations
    result = _handle_recommendation(result, github_token)

    logger.info("Agent result: %s", json.dumps(result, indent=2))

    return {
        "statusCode": 200,
        "body": json.dumps({"mode": "webhook", "message": "Agent invoked", "result": result}),
    }


def _handle_direct_invocation(event: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Handle direct agent invocation with agent_type parameter."""
    payload = _parse_webhook_payload(event)
    agent_type = payload.get("agent_type")

    if not agent_type:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "agent_type is required for direct invocation"}),
        }

    # Add github token if not present
    if "github_token" not in payload:
        payload["github_token"] = github_token

    logger.info("Direct invocation of agent: %s", agent_type)
    result = invoke_agent(agent_type, payload)

    # Handle any recommendations
    result = _handle_recommendation(result, github_token)

    return {
        "statusCode": 200,
        "body": json.dumps({"mode": "direct", "agent_type": agent_type, "result": result}),
    }


def _is_scheduled_event(event: dict[str, Any]) -> bool:
    """Check if event is a scheduled EventBridge event."""
    if event.get("source") == "aws.events" or event.get("detail-type"):
        return True

    body = _parse_webhook_payload(event)
    if body.get("source") == "aws.events" or body.get("detail-type"):
        return True

    return False


def _is_direct_invocation(event: dict[str, Any]) -> bool:
    """Check if event is a direct agent invocation."""
    payload = _parse_webhook_payload(event)
    return "agent_type" in payload and "workflow_run" not in payload


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Main Lambda handler - supports webhook, scheduled, and direct modes."""
    logger.info("Received event: %s", json.dumps(event))

    try:
        github_token = get_github_token()

        # Check if this is a scheduled event (EventBridge/CloudWatch)
        if _is_scheduled_event(event):
            body = _parse_webhook_payload(event)
            test_mode = body.get("test_mode", False) or event.get("test_mode", False)
            return _handle_scheduled_scan(github_token, test_mode=test_mode)

        # Check if this is a direct agent invocation
        if _is_direct_invocation(event):
            return _handle_direct_invocation(event, github_token)

        # Otherwise, treat as webhook event
        return _handle_webhook_event(event, github_token)

    except (ClientError, ValueError, json.JSONDecodeError, RuntimeError) as err:
        logger.error("Error in lambda_handler: %s", err)
        traceback.print_exc()
        return {"statusCode": 500, "body": json.dumps({"error": str(err)})}
