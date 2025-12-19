"""Runner terminator Lambda handler - stops ECS tasks and EC2 instances."""

import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.cloudwatch import publish_metric

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

METRICS_NAMESPACE = "RunnerTerminator"
WORKFLOW_RUNNER_TYPE_TAG = "workflow-runner"

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


def _find_ecs_task_by_run_id(run_id: int | str) -> dict[str, Any] | None:
    """Find ECS task by workflow run ID tag.

    Args:
        run_id: GitHub workflow run ID

    Returns:
        Dictionary with taskArn, runnerName, tags or None if not found
    """
    cluster = os.environ.get("ECS_CLUSTER")
    if not cluster or not run_id:
        return None

    try:
        ecs = _get_ecs_client()
        task_arns: list[str] = []

        # List all running/pending tasks
        for status in ["RUNNING", "PENDING"]:
            paginator = ecs.get_paginator("list_tasks")
            for page in paginator.paginate(cluster=cluster, desiredStatus=status):
                task_arns.extend(page.get("taskArns", []))

        if not task_arns:
            return None

        # Describe tasks in batches of 100 to find the one with matching RunId
        for i in range(0, len(task_arns), 100):
            batch = task_arns[i : i + 100]
            response = ecs.describe_tasks(cluster=cluster, tasks=batch, include=["TAGS"])

            for task in response.get("tasks", []):
                tags = {t["key"]: t["value"] for t in task.get("tags", [])}
                if tags.get("RunId") == str(run_id):
                    return {
                        "taskArn": task["taskArn"],
                        "runnerName": tags.get("Name"),
                        "tags": tags,
                    }
    except ClientError as err:
        logger.error("Failed to find ECS task by RunId %s: %s", run_id, str(err))

    return None


def _find_ec2_instance_by_run_id(run_id: int | str) -> dict[str, Any] | None:
    """Find EC2 instance by workflow run ID tag.

    Args:
        run_id: GitHub workflow run ID

    Returns:
        Dictionary with instanceId, runnerName, tags or None if not found
    """
    ec2_managed_by_tag = os.environ.get("EC2_MANAGED_BY_TAG")
    if not ec2_managed_by_tag or not run_id:
        return None

    try:
        response = _get_ec2_client().describe_instances(
            Filters=[
                {"Name": "tag:RunId", "Values": [str(run_id)]},
                {"Name": "tag:Type", "Values": [WORKFLOW_RUNNER_TYPE_TAG]},
                {"Name": "tag:ManagedBy", "Values": [ec2_managed_by_tag]},
                {"Name": "instance-state-name", "Values": ["pending", "running"]},
            ]
        )

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                return {
                    "instanceId": instance["InstanceId"],
                    "runnerName": tags.get("Name"),
                    "tags": tags,
                }
    except ClientError as err:
        logger.error("Failed to find EC2 instance by RunId %s: %s", run_id, str(err))

    return None


def _stop_ecs_task(task_arn: str, reason: str) -> bool:
    """Stop an ECS task.

    Args:
        task_arn: ARN of the task to stop
        reason: Reason for stopping

    Returns:
        True if successful or task already stopped
    """
    cluster = os.environ.get("ECS_CLUSTER")
    if not cluster:
        logger.error("ECS_CLUSTER not configured")
        return False

    try:
        _get_ecs_client().stop_task(cluster=cluster, task=task_arn, reason=reason)
        logger.info("Stopped ECS task: %s (reason: %s)", task_arn, reason)
        publish_metric(METRICS_NAMESPACE, "EcsTasksStopped", 1, "Count")
        return True
    except ClientError as err:
        error_code = err.response.get("Error", {}).get("Code", "")
        if error_code == "InvalidParameterException" or "TaskNotFound" in str(err):
            logger.info("Task already stopped or not found: %s", task_arn)
            return True
        logger.error("Failed to stop ECS task: %s", str(err))
        publish_metric(METRICS_NAMESPACE, "EcsStopErrors", 1, "Count")
        return False


def _terminate_ec2_instance(instance_id: str, reason: str) -> bool:
    """Terminate an EC2 instance.

    Args:
        instance_id: ID of the instance to terminate
        reason: Reason for termination (logged)

    Returns:
        True if successful or instance already terminated
    """
    try:
        _get_ec2_client().terminate_instances(InstanceIds=[instance_id])
        logger.info("Terminated EC2 instance: %s (reason: %s)", instance_id, reason)
        publish_metric(METRICS_NAMESPACE, "Ec2InstancesTerminated", 1, "Count")
        return True
    except ClientError as err:
        error_code = err.response.get("Error", {}).get("Code", "")
        if error_code in ("InvalidInstanceID.NotFound", "InvalidInstanceID.Malformed"):
            logger.info("Instance already terminated or not found: %s", instance_id)
            return True
        logger.error("Failed to terminate EC2 instance: %s", str(err))
        publish_metric(METRICS_NAMESPACE, "Ec2TerminateErrors", 1, "Count")
        return False


def _terminate_runner_by_run_id(
    run_id: int | str, action: str, job_id: int | str
) -> dict[str, Any]:
    """Terminate runner infrastructure by workflow run ID.

    Args:
        run_id: GitHub workflow run ID
        action: Action that triggered termination (cancelled/completed)
        job_id: GitHub job ID

    Returns:
        Result dictionary with success status and resource info
    """
    reason = f"Workflow {action} (job_id={job_id})"

    # Try to find and stop ECS task first
    ecs_task = _find_ecs_task_by_run_id(run_id)
    if ecs_task:
        logger.info("Found ECS task for RunId %s: %s", run_id, ecs_task["taskArn"])
        success = _stop_ecs_task(ecs_task["taskArn"], reason)
        return {
            "success": success,
            "type": "ecs",
            "resourceId": ecs_task["taskArn"],
            "runnerName": ecs_task.get("runnerName"),
        }

    # Try to find and terminate EC2 instance
    ec2_instance = _find_ec2_instance_by_run_id(run_id)
    if ec2_instance:
        logger.info(
            "Found EC2 instance for RunId %s: %s", run_id, ec2_instance["instanceId"]
        )
        success = _terminate_ec2_instance(ec2_instance["instanceId"], reason)
        return {
            "success": success,
            "type": "ec2",
            "resourceId": ec2_instance["instanceId"],
            "runnerName": ec2_instance.get("runnerName"),
        }

    logger.info("No running ECS task or EC2 instance found for RunId %s", run_id)
    publish_metric(METRICS_NAMESPACE, "RunnerNotFound", 1, "Count")
    return {"success": True, "type": "none", "resourceId": None, "runnerName": None}


def _handle_cancellation_message(message: dict[str, Any]) -> dict[str, Any]:
    """Handle a single cancellation message.

    Args:
        message: SQS message record

    Returns:
        Result dictionary with success status
    """
    try:
        body = json.loads(message.get("body", "{}"))
        action = body.get("action")
        job_id = body.get("job_id")
        run_id = body.get("run_id")
        runner_name = body.get("runner_name")

        logger.info(
            "Processing cancellation: action=%s, job_id=%s, run_id=%s, runner_name=%s",
            action,
            job_id,
            run_id,
            runner_name,
        )

        if not run_id:
            logger.warning("No run_id in cancellation message, cannot find runner")
            return {"success": True, "skipped": True, "reason": "no_run_id"}

        result = _terminate_runner_by_run_id(run_id, action, job_id)

        if result.get("success"):
            logger.info(
                "Successfully processed cancellation for job %s: %s %s",
                job_id,
                result.get("type"),
                result.get("resourceId") or "(no resource found)",
            )
            return {"success": True, **result}

        logger.error("Failed to process cancellation for job %s", job_id)
        return {"success": False, "error": "Failed to terminate runner"}
    except (json.JSONDecodeError, KeyError) as err:
        logger.error("Failed to parse cancellation message: %s", str(err))
        return {"success": False, "error": f"Invalid message format: {err}"}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for runner termination.

    Args:
        event: Lambda event with SQS records
        _context: Lambda context (unused)

    Returns:
        Response dictionary with status and counts

    Raises:
        RuntimeError: If any cancellations fail
    """
    start_time = time.time()
    logger.info("Received event: %s", json.dumps(event))

    records = event.get("Records", [])
    if not records:
        logger.warning("No records in event")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No records to process"}),
        }

    logger.info("Processing %d cancellation(s) from SQS", len(records))

    results = [_handle_cancellation_message(record) for record in records]

    elapsed_ms = (time.time() - start_time) * 1000
    publish_metric(METRICS_NAMESPACE, "ProcessingTime", elapsed_ms, "Milliseconds")

    success_count = sum(1 for r in results if r.get("success"))
    fail_count = sum(1 for r in results if not r.get("success"))

    logger.info(
        "Processed %d cancellations successfully, %d failed", success_count, fail_count
    )

    if fail_count > 0:
        raise RuntimeError(f"{fail_count} cancellation(s) failed")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Processed",
                "count": len(records),
                "success": success_count,
                "failed": fail_count,
            }
        ),
    }
