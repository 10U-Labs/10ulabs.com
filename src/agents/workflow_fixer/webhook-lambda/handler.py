"""
Webhook Lambda - Receives GitHub workflow_run events and invokes AgentCore agent.

Supports two modes:
1. Webhook mode: Triggered by GitHub workflow_run events (failures)
2. Scheduled mode: Scans for unresolved failed workflows on a schedule
"""

import json
import logging
import os
import time
import traceback
import urllib.request
import urllib.error
from typing import Any

import boto3
from botocore.exceptions import ClientError
import jwt

logger = logging.getLogger()
logger.setLevel(logging.INFO)

GITHUB_ORG = os.environ.get("GITHUB_ORG", "10U-Labs-LLC")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "10ulabs.com")

# Cache for installation token (valid for ~1 hour)
_token_cache: dict[str, Any] = {"token": None, "expires_at": 0}


def _get_ssm_parameter(name: str) -> str:
    """Retrieve a parameter from SSM Parameter Store."""
    ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION_NAME", "us-east-2"))
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]


def _generate_jwt(app_id: str, private_key: str) -> str:
    """Generate a JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        "iat": now - 60,  # Issued 60 seconds ago to account for clock drift
        "exp": now + 600,  # Expires in 10 minutes
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def _get_installation_token(app_id: str, installation_id: str, private_key: str) -> str:
    """Get a GitHub App installation access token."""
    app_jwt = _generate_jwt(app_id, private_key)

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "10ULabsBot/1.0",
    }

    req = urllib.request.Request(url, data=b"", headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data["token"]


def get_github_token() -> str:
    """Get a GitHub App installation token (cached)."""
    now = time.time()

    # Return cached token if still valid (with 5 min buffer)
    if _token_cache["token"] and _token_cache["expires_at"] > now + 300:
        return _token_cache["token"]

    # Get GitHub App credentials from SSM
    app_id = _get_ssm_parameter(
        os.environ.get("SSM_GITHUB_APP_ID", "/github/app/id")
    )
    installation_id = _get_ssm_parameter(
        os.environ.get("SSM_GITHUB_APP_INSTALL_ID", "/github/app/installation_id")
    )
    private_key = _get_ssm_parameter(
        os.environ.get("SSM_GITHUB_APP_PRIVATE_KEY", "/github/app/private_key")
    )

    # Generate new installation token
    token = _get_installation_token(app_id, installation_id, private_key)

    # Cache for 55 minutes (tokens are valid for 1 hour)
    _token_cache["token"] = token
    _token_cache["expires_at"] = now + 3300

    logger.info("Generated new GitHub App installation token")
    return token


# Alias for backward compatibility
def get_github_pat() -> str:
    """Retrieve GitHub token (now uses GitHub App)."""
    return get_github_token()


def _github_api_request(
    endpoint: str, token: str, method: str = "GET"
) -> dict[str, Any]:
    """Make a request to the GitHub API."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "WorkflowFixerAgent/1.0",
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

            # Skip workflow-fixer workflows to avoid loops
            if "workflow-fixer" in run.get("name", "").lower():
                continue

            unresolved.append(run)
        except RuntimeError:
            continue  # Skip if we can't check

    return unresolved


def invoke_agent(payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke the AgentCore workflow fixer agent."""
    client = boto3.client(
        "bedrock-agentcore", region_name=os.environ.get("AWS_REGION_NAME", "us-east-2")
    )

    agent_arn = os.environ.get("AGENT_RUNTIME_ARN")
    if not agent_arn:
        raise ValueError("AGENT_RUNTIME_ARN environment variable not set")

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
    if "workflow-fixer" in workflow_name.lower():
        return True, "Ignoring workflow-fixer workflow"

    return False, ""


def _build_agent_payload(
    payload: dict[str, Any], github_token: str
) -> dict[str, Any]:
    """Build the payload for the AgentCore agent."""
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

    # Test mode: return immediately without scanning (for integration tests)
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
        try:
            agent_payload = _build_agent_payload_from_run(run, github_token)
            result = invoke_agent(agent_payload)
            results.append({"run_id": run["id"], "status": "processed", "result": result})
        except (ClientError, ValueError) as err:
            logger.error("Error processing run %s: %s", run["id"], err)
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
    result = invoke_agent(agent_payload)
    logger.info("Agent result: %s", json.dumps(result, indent=2))

    return {
        "statusCode": 200,
        "body": json.dumps({"mode": "webhook", "message": "Agent invoked", "result": result}),
    }


def _is_scheduled_event(event: dict[str, Any]) -> bool:
    """Check if event is a scheduled EventBridge event."""
    # Direct EventBridge invocation
    if event.get("source") == "aws.events" or event.get("detail-type"):
        return True

    # EventBridge event via Lambda function URL (wrapped in HTTP body)
    body = _parse_webhook_payload(event)
    if body.get("source") == "aws.events" or body.get("detail-type"):
        return True

    return False


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Main Lambda handler - supports webhook and scheduled modes."""
    logger.info("Received event: %s", json.dumps(event))

    try:
        github_token = get_github_pat()

        # Check if this is a scheduled event (EventBridge/CloudWatch)
        if _is_scheduled_event(event):
            # Check for test_mode flag (for integration tests)
            body = _parse_webhook_payload(event)
            test_mode = body.get("test_mode", False) or event.get("test_mode", False)
            return _handle_scheduled_scan(github_token, test_mode=test_mode)

        # Otherwise, treat as webhook event
        return _handle_webhook_event(event, github_token)

    except (ClientError, ValueError, json.JSONDecodeError, RuntimeError) as err:
        logger.error("Error in lambda_handler: %s", err)
        traceback.print_exc()
        return {"statusCode": 500, "body": json.dumps({"error": str(err)})}
