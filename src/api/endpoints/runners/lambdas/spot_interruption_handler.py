"""Spot interruption handler - recovers workflows when spot capacity is reclaimed."""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.github_api import get_github_token

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_cache: dict[str, Any] = {"ecs_client": None, "ec2_client": None}


def _get_ecs_client() -> Any:
    """Get or create ECS client (singleton)."""
    if _cache["ecs_client"] is None:
        _cache["ecs_client"] = boto3.client("ecs")
    return _cache["ecs_client"]


def _get_ec2_client() -> Any:
    """Get or create EC2 client (singleton)."""
    if _cache["ec2_client"] is None:
        _cache["ec2_client"] = boto3.client("ec2")
    return _cache["ec2_client"]


def _github_api_request(
    method: str,
    endpoint: str,
    token: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a GitHub API request.

    Args:
        method: HTTP method
        endpoint: API endpoint path
        token: GitHub token
        body: Optional request body

    Returns:
        Dictionary with status and data

    Raises:
        RuntimeError: If request fails
    """
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SpotInterruptionHandler/1.0",
    }

    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            return {
                "status": response.status,
                "data": json.loads(response_body) if response_body else {},
            }
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8") if err.fp else ""
        raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err


def _get_workflow_run_status(github_token: str, github_repo: str, run_id: int) -> str:
    """Get the status of a workflow run.

    Returns:
        Status string or 'unknown' on error
    """
    try:
        result = _github_api_request(
            "GET", f"/repos/{github_repo}/actions/runs/{run_id}", github_token
        )
        return result.get("data", {}).get("status", "unknown")
    except RuntimeError as err:
        logger.error("Failed to get workflow run status: %s", str(err))
        return "unknown"


def _cancel_workflow_run(github_token: str, github_repo: str, run_id: int) -> bool:
    """Cancel a workflow run.

    Returns:
        True if successfully cancelled
    """
    try:
        result = _github_api_request(
            "POST",
            f"/repos/{github_repo}/actions/runs/{run_id}/cancel",
            github_token,
            {},
        )
        if result.get("status") == 202:
            logger.info("Successfully cancelled workflow run %s", run_id)
            return True
        logger.warning("Unexpected response status %s for cancel", result.get("status"))
    except RuntimeError as err:
        logger.error("Failed to cancel workflow %s: %s", run_id, str(err))
    return False


def _create_check_run_annotation(
    github_token: str, github_repo: str, head_sha: str, title: str, summary: str
) -> bool:
    """Create a check run annotation on a commit.

    Returns:
        True if successfully created
    """
    payload = {
        "name": "Spot Interruption Handler",
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": "neutral",
        "output": {"title": title, "summary": summary},
    }
    try:
        result = _github_api_request(
            "POST", f"/repos/{github_repo}/check-runs", github_token, payload
        )
        if result.get("status") == 201:
            logger.info("Successfully created check run annotation")
            return True
        logger.warning(
            "Unexpected response status %s for check run", result.get("status")
        )
    except RuntimeError as err:
        logger.error("Failed to create check run: %s", str(err))
    return False


def _wait_for_workflow_completion(
    github_token: str, github_repo: str, run_id: int, timeout_seconds: int = 60
) -> bool:
    """Wait for a workflow run to complete.

    Args:
        github_token: GitHub token
        github_repo: Repository full name
        run_id: Workflow run ID
        timeout_seconds: Maximum wait time

    Returns:
        True if workflow completed within timeout
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout_seconds:
        try:
            result = _github_api_request(
                "GET", f"/repos/{github_repo}/actions/runs/{run_id}", github_token
            )
            if result.get("data", {}).get("status") == "completed":
                logger.info("Workflow %s completed", run_id)
                return True
        except RuntimeError as err:
            logger.warning("Error polling workflow status: %s", str(err))
        time.sleep(5)
    logger.warning("Timeout waiting for workflow %s to complete", run_id)
    return False


def _get_workflow_info_from_run(
    github_token: str, github_repo: str, run_id: int
) -> dict[str, str]:
    """Get workflow info from a run.

    Returns:
        Dictionary with workflowId and headSha
    """
    try:
        result = _github_api_request(
            "GET", f"/repos/{github_repo}/actions/runs/{run_id}", github_token
        )
        data = result.get("data", {})
        return {
            "workflowId": str(data.get("workflow_id", "")),
            "headSha": data.get("head_sha", ""),
        }
    except RuntimeError as err:
        logger.error("Failed to get workflow info: %s", str(err))
        return {"workflowId": "", "headSha": ""}


def _dispatch_workflow(
    github_token: str, github_repo: str, workflow_id: str, ref: str, reason: str
) -> bool:
    """Dispatch a workflow run.

    Returns:
        True if successfully dispatched
    """
    payload = {"ref": ref, "inputs": {"spot_recovery_reason": reason}}
    try:
        result = _github_api_request(
            "POST",
            f"/repos/{github_repo}/actions/workflows/{workflow_id}/dispatches",
            github_token,
            payload,
        )
        if result.get("status") == 204:
            logger.info("Successfully dispatched workflow %s", workflow_id)
            return True
        logger.warning(
            "Unexpected response status %s for dispatch", result.get("status")
        )
    except RuntimeError as err:
        logger.error("Failed to dispatch workflow: %s", str(err))
    return False


def _is_spot_interruption(stop_code: str, stopped_reason: str) -> bool:
    """Check if the stop was due to spot interruption."""
    return "SpotInterruption" in stop_code or "capacity" in stopped_reason.lower()


def _recover_from_spot_interruption(
    github_token: str, github_repo: str, run_id: int, instance_id: str
) -> dict[str, Any]:
    """Recover from EC2 spot interruption.

    Args:
        github_token: GitHub token
        github_repo: Repository full name
        run_id: Workflow run ID
        instance_id: EC2 instance ID

    Returns:
        Response dictionary
    """
    workflow_info = _get_workflow_info_from_run(github_token, github_repo, run_id)
    workflow_id = workflow_info.get("workflowId", "")
    head_sha = workflow_info.get("headSha", "")

    if not workflow_id:
        logger.error("Failed to get workflow info for run %s", run_id)
        return {"statusCode": 500, "body": "Failed to get workflow info"}

    if not _cancel_workflow_run(github_token, github_repo, run_id):
        logger.error("Failed to cancel workflow run %s", run_id)
        return {"statusCode": 500, "body": "Failed to cancel workflow"}

    reason = (
        f"EC2 Spot Instance {instance_id} received interruption warning. "
        f"AWS is reclaiming spot capacity. Workflow cancelled and will be "
        f"automatically re-triggered."
    )
    _create_check_run_annotation(
        github_token, github_repo, head_sha, "Spot Instance Interruption", reason
    )

    _wait_for_workflow_completion(github_token, github_repo, run_id)

    recovery_reason = f"Auto-recovery from spot interruption of instance {instance_id}"
    if _dispatch_workflow(github_token, github_repo, workflow_id, "main", recovery_reason):
        logger.info("Successfully dispatched recovery workflow for %s", workflow_id)
        return {"statusCode": 200, "body": "Recovery workflow dispatched"}

    logger.error("Failed to dispatch recovery workflow")
    return {"statusCode": 500, "body": "Failed to dispatch recovery workflow"}


def _recover_from_ecs_spot_interruption(
    github_token: str, github_repo: str, run_id: int, task_arn: str
) -> dict[str, Any]:
    """Recover from ECS Fargate spot interruption.

    Args:
        github_token: GitHub token
        github_repo: Repository full name
        run_id: Workflow run ID
        task_arn: ECS task ARN

    Returns:
        Response dictionary
    """
    workflow_info = _get_workflow_info_from_run(github_token, github_repo, run_id)
    workflow_id = workflow_info.get("workflowId", "")
    head_sha = workflow_info.get("headSha", "")

    if not workflow_id:
        logger.error("Failed to get workflow info for run %s", run_id)
        return {"statusCode": 500, "body": "Failed to get workflow info"}

    if not _cancel_workflow_run(github_token, github_repo, run_id):
        logger.error("Failed to cancel workflow run %s", run_id)
        return {"statusCode": 500, "body": "Failed to cancel workflow"}

    task_id = task_arn.split("/")[-1] if "/" in task_arn else task_arn
    reason = (
        f"ECS Fargate Spot task {task_id} was interrupted. "
        f"AWS reclaimed spot capacity. Workflow cancelled and will be "
        f"automatically re-triggered."
    )
    _create_check_run_annotation(
        github_token, github_repo, head_sha, "ECS Spot Interruption", reason
    )

    _wait_for_workflow_completion(github_token, github_repo, run_id)

    recovery_reason = f"Auto-recovery from ECS spot interruption of task {task_id}"
    if _dispatch_workflow(github_token, github_repo, workflow_id, "main", recovery_reason):
        logger.info("Successfully dispatched recovery workflow for %s", workflow_id)
        return {"statusCode": 200, "body": "Recovery workflow dispatched"}

    logger.error("Failed to dispatch recovery workflow")
    return {"statusCode": 500, "body": "Failed to dispatch recovery workflow"}


def _trigger_ecs_recovery(
    github_repo: str, run_id: int, task_arn: str
) -> dict[str, Any]:
    """Trigger ECS spot recovery.

    Args:
        github_repo: Repository full name
        run_id: Workflow run ID
        task_arn: ECS task ARN

    Returns:
        Response dictionary
    """
    github_token = get_github_token()
    if not github_token:
        logger.error("No GitHub token available")
        return {"statusCode": 500, "body": "No GitHub token"}

    workflow_status = _get_workflow_run_status(github_token, github_repo, run_id)
    if workflow_status not in ("queued", "in_progress", "waiting"):
        logger.info(
            "Workflow %s not active (status=%s), skipping", run_id, workflow_status
        )
        return {"statusCode": 200, "body": f"Workflow not active: {workflow_status}"}

    logger.info("Initiating ECS spot recovery for run_id=%s", run_id)
    return _recover_from_ecs_spot_interruption(
        github_token, github_repo, run_id, task_arn
    )


def _get_ecs_task_tags(task_arn: str) -> dict[str, str]:
    """Get tags from an ECS task.

    Args:
        task_arn: ECS task ARN

    Returns:
        Dictionary of tag key-value pairs
    """
    tag_dict: dict[str, str] = {}
    try:
        cluster = os.environ.get("ECS_CLUSTER", "")
        response = _get_ecs_client().describe_tasks(
            cluster=cluster, tasks=[task_arn], include=["TAGS"]
        )
        tasks = response.get("tasks", [])
        if tasks:
            tags = tasks[0].get("tags", [])
            for tag in tags:
                tag_dict[tag["key"]] = tag["value"]
    except ClientError as err:
        logger.error("Failed to get ECS task tags: %s", str(err))
    return tag_dict


def _handle_ecs_task_stopped(event: dict[str, Any]) -> dict[str, Any]:
    """Handle ECS task stopped event.

    Args:
        event: EventBridge event

    Returns:
        Response dictionary
    """
    detail = event.get("detail", {})
    stop_code = detail.get("stopCode", "")
    stopped_reason = detail.get("stoppedReason", "")
    task_arn = detail.get("taskArn", "")
    tag_dict = _get_ecs_task_tags(task_arn)
    run_id_str = tag_dict.get("RunId", "")
    github_repo = tag_dict.get("GitHubRepo", "")

    logger.info(
        "ECS task stopped: arn=%s, stopCode=%s, reason=%s, run_id=%s",
        task_arn,
        stop_code,
        stopped_reason,
        run_id_str,
    )

    if not run_id_str:
        logger.info("No run_id in task tags, skipping")
        return {"statusCode": 200, "body": "No run_id"}

    if not _is_spot_interruption(stop_code, stopped_reason):
        logger.info("Not a spot interruption, skipping recovery")
        return {"statusCode": 200, "body": "Not a spot interruption"}

    return _trigger_ecs_recovery(github_repo, int(run_id_str), task_arn)


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


def _handle_ec2_spot_interruption(event: dict[str, Any]) -> dict[str, Any]:
    """Handle EC2 spot interruption warning.

    Args:
        event: EventBridge event

    Returns:
        Response dictionary
    """
    instance_id = event.get("detail", {}).get("instance-id", "")
    logger.info("EC2 spot interruption warning for instance: %s", instance_id)

    tag_dict = _get_ec2_instance_tags(instance_id)
    if not tag_dict:
        return {"statusCode": 500, "body": "Failed to get instance tags"}

    run_id_str = tag_dict.get("RunId", "")
    github_repo = tag_dict.get("GitHubRepo", "")

    if not run_id_str:
        logger.info("No run_id in instance tags, skipping")
        return {"statusCode": 200, "body": "No run_id"}

    github_token = get_github_token()
    if not github_token:
        logger.error("No GitHub token available")
        return {"statusCode": 500, "body": "No GitHub token"}

    run_id = int(run_id_str)
    workflow_status = _get_workflow_run_status(github_token, github_repo, run_id)
    if workflow_status not in ("queued", "in_progress", "waiting"):
        logger.info(
            "Workflow %s not active (status=%s), skipping", run_id, workflow_status
        )
        return {"statusCode": 200, "body": f"Workflow not active: {workflow_status}"}

    logger.info("Initiating spot interruption recovery for run_id=%s", run_id)
    return _recover_from_spot_interruption(
        github_token, github_repo, run_id, instance_id
    )


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for spot interruption events.

    Args:
        event: EventBridge event
        _context: Lambda context (unused)

    Returns:
        Response dictionary
    """
    logger.info("Received event: %s", json.dumps(event))
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    if source == "aws.ecs" and detail_type == "ECS Task State Change":
        last_status = event.get("detail", {}).get("lastStatus", "")
        if last_status == "STOPPED":
            return _handle_ecs_task_stopped(event)
    elif source == "aws.ec2" and detail_type == "EC2 Spot Instance Interruption Warning":
        return _handle_ec2_spot_interruption(event)

    logger.info("Ignoring event: source=%s, detail-type=%s", source, detail_type)
    return {"statusCode": 200, "body": "Event ignored"}
