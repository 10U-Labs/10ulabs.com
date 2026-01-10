"""Runner terminator Lambda handler - stops ECS tasks and EC2 instances."""

import json
import logging
import os
import time
from typing import Any

from botocore.exceptions import ClientError

from common.aws_clients import get_ec2_client
from common.cloudwatch import publish_metric
from common.ec2_utils import terminate_ec2_instance
from common.ecs_utils import (
    list_running_task_arns,
    describe_tasks_with_tags,
    extract_task_tags,
    stop_ecs_task,
    get_cluster_from_env,
)
from common.lambda_utils import (
    get_sqs_records,
    empty_records_response,
    count_results,
    parse_error_response,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

METRICS_NAMESPACE = "RunnerTerminator"
WORKFLOW_RUNNER_TYPE_TAG = "workflow-runner"


def _find_ecs_task_by_run_id(run_id: int | str) -> dict[str, Any] | None:
    """Find ECS task by workflow run ID tag.

    Args:
        run_id: GitHub workflow run ID

    Returns:
        Dictionary with taskArn, runnerName, tags or None if not found
    """
    cluster = get_cluster_from_env()
    if not cluster or not run_id:
        return None

    try:
        task_arns = list_running_task_arns(cluster)
        if not task_arns:
            return None

        for task in describe_tasks_with_tags(cluster, task_arns):
            tags = extract_task_tags(task)
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
        response = get_ec2_client().describe_instances(
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


def _stop_ecs_task_with_metrics(task_arn: str, reason: str) -> bool:
    """Stop an ECS task and publish metrics.

    Args:
        task_arn: ARN of the task to stop
        reason: Reason for stopping

    Returns:
        True if successful or task already stopped
    """
    cluster = get_cluster_from_env()
    if not cluster:
        logger.error("ECS_CLUSTER not configured")
        return False

    result = stop_ecs_task(cluster, task_arn, reason)
    if result:
        publish_metric(METRICS_NAMESPACE, "EcsTasksStopped", 1, "Count")
    else:
        publish_metric(METRICS_NAMESPACE, "EcsStopErrors", 1, "Count")
    return result


def _terminate_ec2_instance_with_metrics(instance_id: str, reason: str) -> bool:
    """Terminate an EC2 instance and publish metrics.

    Args:
        instance_id: ID of the instance to terminate
        reason: Reason for termination (logged)

    Returns:
        True if successful or instance already terminated
    """
    logger.info("Terminating EC2 instance: %s (reason: %s)", instance_id, reason)
    result = terminate_ec2_instance(instance_id)
    if result:
        publish_metric(METRICS_NAMESPACE, "Ec2InstancesTerminated", 1, "Count")
    else:
        publish_metric(METRICS_NAMESPACE, "Ec2TerminateErrors", 1, "Count")
    return result


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
        success = _stop_ecs_task_with_metrics(ecs_task["taskArn"], reason)
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
        success = _terminate_ec2_instance_with_metrics(ec2_instance["instanceId"], reason)
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
        return parse_error_response(err)


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
    records = get_sqs_records(event)
    if records is None:
        return empty_records_response()

    logger.info("Processing %d cancellation(s) from SQS", len(records))

    results = [_handle_cancellation_message(record) for record in records]

    elapsed_ms = (time.time() - start_time) * 1000
    publish_metric(METRICS_NAMESPACE, "ProcessingTime", elapsed_ms, "Milliseconds")

    success_count, fail_count = count_results(results)

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
