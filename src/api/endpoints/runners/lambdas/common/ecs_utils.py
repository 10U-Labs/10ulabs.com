"""ECS task utilities for Lambda handlers."""

import logging
import os
from typing import Any

from botocore.exceptions import ClientError

from common.aws_clients import get_ecs_client

logger = logging.getLogger(__name__)


def list_running_task_arns(cluster: str) -> list[str]:
    """List all running/pending task ARNs in a cluster.

    Args:
        cluster: ECS cluster name or ARN

    Returns:
        List of task ARNs
    """
    task_arns: list[str] = []
    ecs = get_ecs_client()

    for status in ["RUNNING", "PENDING"]:
        paginator = ecs.get_paginator("list_tasks")
        for page in paginator.paginate(cluster=cluster, desiredStatus=status):
            task_arns.extend(page.get("taskArns", []))

    return task_arns


def describe_tasks_with_tags(
    cluster: str, task_arns: list[str]
) -> list[dict[str, Any]]:
    """Describe tasks with tags in batches.

    Args:
        cluster: ECS cluster name or ARN
        task_arns: List of task ARNs

    Returns:
        List of task dictionaries with tags
    """
    tasks: list[dict[str, Any]] = []
    ecs = get_ecs_client()

    for i in range(0, len(task_arns), 100):
        batch = task_arns[i : i + 100]
        response = ecs.describe_tasks(cluster=cluster, tasks=batch, include=["TAGS"])
        tasks.extend(response.get("tasks", []))

    return tasks


def extract_task_tags(task: dict[str, Any]) -> dict[str, str]:
    """Extract tags from a task as a dictionary.

    Args:
        task: Task dictionary from describe_tasks

    Returns:
        Dictionary of tag key-value pairs
    """
    return {t["key"]: t["value"] for t in task.get("tags", [])}


def stop_ecs_task(cluster: str, task_arn: str, reason: str) -> bool:
    """Stop an ECS task with standard error handling.

    Args:
        cluster: ECS cluster name or ARN
        task_arn: ARN of the task to stop
        reason: Reason for stopping

    Returns:
        True if successful or task already stopped
    """
    try:
        get_ecs_client().stop_task(cluster=cluster, task=task_arn, reason=reason)
        logger.info("Stopped ECS task: %s (reason: %s)", task_arn, reason)
        return True
    except ClientError as err:
        error_code = err.response.get("Error", {}).get("Code", "")
        if error_code == "InvalidParameterException" or "TaskNotFound" in str(err):
            logger.info("Task already stopped or not found: %s", task_arn)
            return True
        logger.error("Failed to stop ECS task: %s", str(err))
        return False


def get_cluster_from_env() -> str:
    """Get ECS cluster from environment variable.

    Returns:
        Cluster name/ARN or empty string
    """
    return os.environ.get("ECS_CLUSTER", "")
