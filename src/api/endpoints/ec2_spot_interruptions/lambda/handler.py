"""EC2 spot interruption handler - detects spot interruptions and retries workflows.

This endpoint receives EC2 spot interruption warning events from EventBridge
and cancels/re-dispatches GitHub workflows for runners that have workflow
metadata in their tags.
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


def _get_ec2_client():
    """Get EC2 client."""
    return boto3.client("ec2")


def _get_ssm_client():
    """Get SSM client."""
    return boto3.client("ssm")


def _get_ec2_instance_tags(instance_id: str) -> dict[str, str]:
    """Get tags from an EC2 instance.

    Args:
        instance_id: EC2 instance ID

    Returns:
        Dictionary of tag key-value pairs
    """
    tag_dict: dict[str, str] = {}
    try:
        response = _get_ec2_client().describe_instances(InstanceIds=[instance_id])
        reservations = response.get("Reservations", [])
        if reservations:
            instances = reservations[0].get("Instances", [])
            if instances:
                tags = instances[0].get("Tags", [])
                for tag in tags:
                    tag_dict[tag["Key"]] = tag["Value"]
    except ClientError as err:
        logger.error("Failed to get instance tags: %s", str(err))
    return tag_dict


# --- GitHub retry logic (inlined from github_workflows/retries) ---


def _get_github_token() -> str:
    """Get GitHub token from SSM parameter."""
    param_name = os.environ.get("GITHUB_TOKEN_SECRET_NAME", "")
    if not param_name:
        logger.error("GITHUB_TOKEN_SECRET_NAME not set")
        return ""
    try:
        response = _get_ssm_client().get_parameter(Name=param_name, WithDecryption=True)
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


def _process_retry_request(
    run_id: int,
    github_repo: str,
    reason: str,
    resource_type: str,
    resource_id: str,
) -> dict[str, Any]:
    """Process a workflow retry request.

    Args:
        run_id: GitHub workflow run ID
        github_repo: Repository full name (org/repo)
        reason: Reason for the retry
        resource_type: Type of resource (ec2)
        resource_id: Resource identifier (instance ID)

    Returns:
        Response dictionary
    """
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
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Workflow retry dispatched",
                "retried": True,
                "workflow_id": workflow_id,
            }),
        }

    return {
        "statusCode": 500,
        "body": json.dumps({"error": "Failed to dispatch retry workflow"}),
    }


# --- End GitHub retry logic ---


def _handle_ec2_spot_interruption(event: dict[str, Any]) -> dict[str, Any]:
    """Handle EC2 spot interruption warning.

    Args:
        event: EventBridge event

    Returns:
        Response dictionary
    """
    instance_id = event.get("detail", {}).get("instance-id", "")
    logger.info("EC2 spot interruption warning for instance: %s", instance_id)

    if not instance_id:
        logger.error("No instance-id in event")
        return {"statusCode": 400, "body": json.dumps({"error": "No instance-id"})}

    tag_dict = _get_ec2_instance_tags(instance_id)
    if not tag_dict:
        logger.warning("No tags found for instance %s", instance_id)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No tags found", "handled": False}),
        }

    run_id_str = tag_dict.get("RunId", "")
    github_repo = tag_dict.get("GitHubRepo", "")

    if not run_id_str or not github_repo:
        logger.info("Instance %s is not a runner (no RunId/GitHubRepo tags)", instance_id)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Not our runner", "handled": False}),
        }

    reason = f"EC2 spot instance {instance_id} received interruption warning"
    result = _process_retry_request(
        run_id=int(run_id_str),
        github_repo=github_repo,
        reason=reason,
        resource_type="ec2",
        resource_id=instance_id,
    )

    # Add instance info to response
    if result.get("statusCode") == 200:
        body = json.loads(result["body"])
        body["instance_id"] = instance_id
        body["run_id"] = run_id_str
        result["body"] = json.dumps(body)

    return result


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for EC2 spot interruption events.

    Handles direct EventBridge invocations.

    Args:
        event: EventBridge event
        _context: Lambda context (unused)

    Returns:
        Response dictionary
    """
    logger.info("Received event: %s", json.dumps(event))

    # Handle direct EventBridge invocation
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    if source == "aws.ec2" and detail_type == "EC2 Spot Instance Interruption Warning":
        return _handle_ec2_spot_interruption(event)

    logger.info("Ignoring event: source=%s, detail-type=%s", source, detail_type)
    return {"statusCode": 200, "body": json.dumps({"message": "Event ignored"})}
