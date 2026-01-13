"""GitHub workflow retry handler - cancels and re-triggers workflows.

This endpoint receives retry requests from EC2/ECS spot interruption handlers
and performs the GitHub API operations to cancel and re-dispatch workflows.
"""

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_github_token() -> str:
    """Get GitHub token from SSM parameter."""
    ssm = boto3.client("ssm")
    param_name = os.environ.get("GITHUB_TOKEN_SECRET_NAME", "")
    if not param_name:
        logger.error("GITHUB_TOKEN_SECRET_NAME not set")
        return ""
    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except ClientError as err:
        logger.error("Failed to get GitHub token: %s", str(err))
        return ""


def _github_api_request(
    method: str, endpoint: str, token: str, data: dict | None = None
) -> dict:
    """Make a GitHub API request."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status == 204:
            return {}
        return json.loads(response.read().decode())


def _get_workflow_run_status(token: str, repo: str, run_id: int) -> str:
    """Get the status of a workflow run."""
    try:
        data = _github_api_request("GET", f"/repos/{repo}/actions/runs/{run_id}", token)
        return data.get("status", "unknown")
    except urllib.error.HTTPError as err:
        logger.error("Failed to get workflow run status: %s", str(err))
        return "unknown"


def _cancel_workflow_run(token: str, repo: str, run_id: int) -> bool:
    """Cancel a workflow run."""
    try:
        _github_api_request(
            "POST", f"/repos/{repo}/actions/runs/{run_id}/cancel", token, data={}
        )
        logger.info("Successfully cancelled workflow run %s", run_id)
        return True
    except urllib.error.HTTPError as err:
        if err.code == 202:
            logger.info("Successfully cancelled workflow run %s", run_id)
            return True
        logger.error("Failed to cancel workflow %s: %s", run_id, str(err))
    return False


def _create_check_run_annotation(
    token: str, repo: str, head_sha: str, title: str, summary: str
) -> bool:
    """Create a check run annotation on a commit."""
    payload = {
        "name": "Workflow Retry Handler",
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": "neutral",
        "output": {"title": title, "summary": summary},
    }
    try:
        _github_api_request("POST", f"/repos/{repo}/check-runs", token, data=payload)
        logger.info("Successfully created check run annotation")
        return True
    except urllib.error.HTTPError as err:
        if err.code == 201:
            logger.info("Successfully created check run annotation")
            return True
        logger.error("Failed to create check run: %s", str(err))
    return False


def _wait_for_workflow_completion(
    token: str, repo: str, run_id: int, timeout_seconds: int = 60
) -> bool:
    """Wait for a workflow run to complete."""
    start_time = time.time()
    while (time.time() - start_time) < timeout_seconds:
        try:
            data = _github_api_request(
                "GET", f"/repos/{repo}/actions/runs/{run_id}", token
            )
            if data.get("status") == "completed":
                logger.info("Workflow %s completed", run_id)
                return True
        except urllib.error.HTTPError as err:
            logger.warning("Error polling workflow status: %s", str(err))
        time.sleep(5)
    logger.warning("Timeout waiting for workflow %s to complete", run_id)
    return False


def _get_workflow_info_from_run(token: str, repo: str, run_id: int) -> dict[str, str]:
    """Get workflow info from a run."""
    try:
        data = _github_api_request("GET", f"/repos/{repo}/actions/runs/{run_id}", token)
        return {
            "workflow_id": str(data.get("workflow_id", "")),
            "head_sha": data.get("head_sha", ""),
            "head_branch": data.get("head_branch", "main"),
        }
    except urllib.error.HTTPError as err:
        logger.error("Failed to get workflow info: %s", str(err))
        return {"workflow_id": "", "head_sha": "", "head_branch": "main"}


def _dispatch_workflow(
    token: str, repo: str, workflow_id: str, ref: str, reason: str
) -> bool:
    """Dispatch a workflow run."""
    payload = {"ref": ref, "inputs": {"retry_reason": reason}}
    try:
        _github_api_request(
            "POST",
            f"/repos/{repo}/actions/workflows/{workflow_id}/dispatches",
            token,
            data=payload,
        )
        logger.info("Successfully dispatched workflow %s", workflow_id)
        return True
    except urllib.error.HTTPError as err:
        if err.code == 204:
            logger.info("Successfully dispatched workflow %s", workflow_id)
            return True
        logger.error("Failed to dispatch workflow: %s", str(err))
    return False


def _process_retry_request(body: dict) -> dict[str, Any]:
    """Process a workflow retry request.

    Expected body format:
    {
        "run_id": 12345,
        "github_repo": "org/repo",
        "reason": "EC2 spot interruption",
        "resource_type": "ec2",
        "resource_id": "i-abc123"
    }
    """
    run_id = body.get("run_id")
    github_repo = body.get("github_repo")
    reason = body.get("reason", "Unknown")
    resource_type = body.get("resource_type", "unknown")
    resource_id = body.get("resource_id", "unknown")

    if not run_id or not github_repo:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required fields: run_id, github_repo"}),
        }

    token = _get_github_token()
    if not token:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to get GitHub token"}),
        }

    # Check if workflow is still active
    status = _get_workflow_run_status(token, github_repo, run_id)
    if status not in ("queued", "in_progress", "waiting"):
        logger.info("Workflow %s not active (status=%s), skipping", run_id, status)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Workflow not active: {status}",
                "retried": False,
            }),
        }

    # Get workflow info
    workflow_info = _get_workflow_info_from_run(token, github_repo, run_id)
    workflow_id = workflow_info.get("workflow_id", "")
    head_sha = workflow_info.get("head_sha", "")
    head_branch = workflow_info.get("head_branch", "main")

    if not workflow_id:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to get workflow info"}),
        }

    # Cancel the workflow
    if not _cancel_workflow_run(token, github_repo, run_id):
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to cancel workflow"}),
        }

    # Create annotation
    title = f"{resource_type.upper()} Resource Interrupted"
    summary = (
        f"Resource {resource_id} ({resource_type}) was interrupted. "
        f"Reason: {reason}. Workflow cancelled and will be re-triggered."
    )
    _create_check_run_annotation(token, github_repo, head_sha, title, summary)

    # Wait for cancellation to complete
    _wait_for_workflow_completion(token, github_repo, run_id)

    # Re-dispatch the workflow
    if _dispatch_workflow(
        token, github_repo, workflow_id, head_branch,
        f"Auto-retry: {reason} ({resource_type}:{resource_id})"
    ):
        logger.info("Successfully dispatched retry workflow for %s", workflow_id)
        result = {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Workflow retry dispatched",
                "retried": True,
                "workflow_id": workflow_id,
            }),
        }
    else:
        result = {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to dispatch retry workflow"}),
        }
    return result


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for workflow retry requests.

    Handles both direct invocations and SQS-triggered events.
    """
    logger.info("Received event: %s", json.dumps(event))

    # Handle SQS event
    if "Records" in event:
        results = []
        for record in event["Records"]:
            body = json.loads(record["body"])
            result = _process_retry_request(body)
            results.append(result)
        return {
            "statusCode": 200,
            "body": json.dumps({"results": results}),
        }

    # Handle direct invocation or API Gateway event
    if "body" in event:
        body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
    else:
        body = event

    return _process_retry_request(body)
