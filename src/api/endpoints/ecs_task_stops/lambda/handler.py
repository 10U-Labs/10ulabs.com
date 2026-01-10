"""ECS task stops handler - detects spot interruptions and triggers retries.

This endpoint receives ECS task stopped events from EventBridge
and sends retry requests to the github-workflows/retries queue for runners
that have workflow metadata in their tags.
"""

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_ecs_client():
    """Get ECS client."""
    return boto3.client("ecs")


def _get_sqs_client():
    """Get SQS client."""
    return boto3.client("sqs")


def _is_spot_interruption(stop_code: str, stopped_reason: str) -> bool:
    """Check if the stop was due to spot interruption.

    Args:
        stop_code: The ECS stop code
        stopped_reason: The ECS stopped reason

    Returns:
        True if this appears to be a spot interruption
    """
    return "SpotInterruption" in stop_code or "capacity" in stopped_reason.lower()


def _get_ecs_task_tags(task_arn: str, cluster_arn: str) -> dict[str, str]:
    """Get tags from an ECS task.

    Args:
        task_arn: ECS task ARN
        cluster_arn: ECS cluster ARN

    Returns:
        Dictionary of tag key-value pairs
    """
    tag_dict: dict[str, str] = {}
    try:
        response = _get_ecs_client().describe_tasks(
            cluster=cluster_arn, tasks=[task_arn], include=["TAGS"]
        )
        tasks = response.get("tasks", [])
        if tasks:
            tags = tasks[0].get("tags", [])
            for tag in tags:
                tag_dict[tag["key"]] = tag["value"]
    except ClientError as err:
        logger.error("Failed to get ECS task tags: %s", str(err))
    return tag_dict


def _send_retry_request(
    run_id: int,
    github_repo: str,
    reason: str,
    resource_type: str,
    resource_id: str,
) -> bool:
    """Send a retry request to the github-workflows/retries queue.

    Args:
        run_id: GitHub workflow run ID
        github_repo: Repository full name (org/repo)
        reason: Reason for the retry
        resource_type: Type of resource (ecs)
        resource_id: Resource identifier (task ARN)

    Returns:
        True if message sent successfully
    """
    queue_url = os.environ.get("RETRIES_QUEUE_URL", "")
    if not queue_url:
        logger.error("RETRIES_QUEUE_URL not set")
        return False

    message = {
        "run_id": run_id,
        "github_repo": github_repo,
        "reason": reason,
        "resource_type": resource_type,
        "resource_id": resource_id,
    }

    try:
        _get_sqs_client().send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
        )
        logger.info("Sent retry request for run_id=%s to queue", run_id)
        return True
    except ClientError as err:
        logger.error("Failed to send retry request: %s", str(err))
        return False


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
    cluster_arn = detail.get("clusterArn", "")

    logger.info(
        "ECS task stopped: arn=%s, stopCode=%s, reason=%s",
        task_arn,
        stop_code,
        stopped_reason,
    )

    if not task_arn:
        logger.error("No taskArn in event")
        return {"statusCode": 400, "body": json.dumps({"error": "No taskArn"})}

    if not _is_spot_interruption(stop_code, stopped_reason):
        logger.info("Not a spot interruption, ignoring")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Not a spot interruption",
                "handled": False,
            }),
        }

    tag_dict = _get_ecs_task_tags(task_arn, cluster_arn)
    if not tag_dict:
        logger.warning("No tags found for task %s", task_arn)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No tags found", "handled": False}),
        }

    run_id_str = tag_dict.get("RunId", "")
    github_repo = tag_dict.get("GitHubRepo", "")

    if not run_id_str or not github_repo:
        logger.info("Task %s is not a runner (no RunId/GitHubRepo tags)", task_arn)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Not our runner", "handled": False}),
        }

    task_id = task_arn.split("/")[-1] if "/" in task_arn else task_arn
    reason = f"ECS Fargate spot task {task_id} was interrupted"
    if _send_retry_request(
        run_id=int(run_id_str),
        github_repo=github_repo,
        reason=reason,
        resource_type="ecs",
        resource_id=task_arn,
    ):
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Retry request sent",
                "handled": True,
                "task_arn": task_arn,
                "run_id": run_id_str,
            }),
        }

    return {
        "statusCode": 500,
        "body": json.dumps({"error": "Failed to send retry request"}),
    }


def _process_sqs_record(record: dict[str, Any]) -> dict[str, Any]:
    """Process a single SQS record containing an EventBridge event.

    Args:
        record: SQS record

    Returns:
        Response dictionary
    """
    body = json.loads(record["body"])

    # Check if this is a direct EventBridge event or wrapped
    if "source" in body and "detail-type" in body:
        return _handle_ecs_task_stopped(body)

    # Otherwise assume it's the event body directly
    return _handle_ecs_task_stopped(body)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for ECS task stopped events.

    Handles both direct EventBridge invocations and SQS-triggered events.

    Args:
        event: EventBridge event or SQS event
        _context: Lambda context (unused)

    Returns:
        Response dictionary
    """
    logger.info("Received event: %s", json.dumps(event))

    # Handle SQS event
    if "Records" in event:
        results = []
        for record in event["Records"]:
            result = _process_sqs_record(record)
            results.append(result)
        return {
            "statusCode": 200,
            "body": json.dumps({"results": results}),
        }

    # Handle direct EventBridge invocation
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    if source == "aws.ecs" and detail_type == "ECS Task State Change":
        last_status = event.get("detail", {}).get("lastStatus", "")
        if last_status == "STOPPED":
            return _handle_ecs_task_stopped(event)

    logger.info("Ignoring event: source=%s, detail-type=%s", source, detail_type)
    return {"statusCode": 200, "body": json.dumps({"message": "Event ignored"})}
