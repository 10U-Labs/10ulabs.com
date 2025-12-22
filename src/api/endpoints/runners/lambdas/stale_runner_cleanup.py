"""Stale runner cleanup Lambda handler - removes orphaned infrastructure."""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Any

from botocore.exceptions import ClientError

from common.aws_clients import get_ec2_client
from common.ec2_utils import terminate_ec2_instance
from common.ecs_utils import (
    list_running_task_arns,
    describe_tasks_with_tags,
    extract_task_tags,
    stop_ecs_task,
    get_cluster_from_env,
)
from common.github_api import get_github_token

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ORPHAN_THRESHOLD_SECONDS = 300
ECS_MANAGED_BY_TAG = "ecs-runner-api"
WORKFLOW_RUNNER_TYPE_TAG = "workflow-runner"


def _github_api_request(method: str, endpoint: str, token: str) -> dict[str, Any]:
    """Make a GitHub API request.

    Args:
        method: HTTP method
        endpoint: API endpoint path
        token: GitHub token

    Returns:
        Parsed JSON response

    Raises:
        RuntimeError: If request fails
    """
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "StaleRunnerCleanup/1.0",
    }

    request = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status == 204:
                return {}
            response_body = response.read().decode("utf-8")
            return json.loads(response_body) if response_body else {}
    except urllib.error.HTTPError as err:
        if err.code == 204:
            return {}
        error_body = err.read().decode("utf-8") if err.fp else ""
        raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err


def _get_all_github_runners(
    github_token: str, github_repo: str
) -> list[dict[str, Any]] | None:
    """Get all GitHub runners for a repository with pagination.

    Returns:
        List of runners or None on error
    """
    runners: list[dict[str, Any]] = []
    page = 1

    try:
        while True:
            endpoint = f"/repos/{github_repo}/actions/runners?per_page=100&page={page}"
            data = _github_api_request("GET", endpoint, github_token)
            page_runners = data.get("runners", [])
            runners.extend(page_runners)
            if len(page_runners) < 100:
                break
            page += 1
        return runners
    except RuntimeError as err:
        logger.error("Failed to list GitHub runners: %s", str(err))
        return None


def _delete_github_runner_by_id(
    github_token: str, github_repo: str, runner_id: int, runner_name: str
) -> bool:
    """Delete a GitHub runner by ID.

    Returns:
        True if successfully deleted
    """
    try:
        _github_api_request(
            "DELETE", f"/repos/{github_repo}/actions/runners/{runner_id}", github_token
        )
        logger.info("Deleted GitHub runner: %s", runner_name)
        return True
    except RuntimeError as err:
        if "204" in str(err):
            return True
        logger.error("Failed to delete GitHub runner %s: %s", runner_name, str(err))
        return False


def _delete_github_runner(
    github_token: str, github_repo: str, runner_name: str
) -> bool:
    """Delete a GitHub runner by name.

    Returns:
        True if successfully deleted or not found
    """
    runners = _get_all_github_runners(github_token, github_repo)
    if runners is None:
        return False
    runner = next((r for r in runners if r.get("name") == runner_name), None)
    if not runner:
        return True
    return _delete_github_runner_by_id(
        github_token, github_repo, runner["id"], runner_name
    )


def _terminate_ecs_task(task_arn: str) -> bool:
    """Terminate an ECS task.

    Returns:
        True if successfully stopped
    """
    cluster = get_cluster_from_env()
    if not cluster:
        return False
    return stop_ecs_task(cluster, task_arn, "Stale runner cleanup")


def _is_orphaned_ecs_task(
    task: dict[str, Any], current_time: float
) -> dict[str, Any] | None:
    """Check if an ECS task is orphaned.

    Returns:
        Orphan info dict or None if not orphaned
    """
    tags = {t["key"]: t["value"] for t in task.get("tags", [])}

    if tags.get("Type") != WORKFLOW_RUNNER_TYPE_TAG:
        return None
    if tags.get("ManagedBy") != ECS_MANAGED_BY_TAG:
        return None

    started_at = task.get("startedAt")
    if not started_at:
        return None

    # startedAt is a datetime object from boto3
    started_timestamp = started_at.timestamp() if hasattr(started_at, 'timestamp') else 0
    age_seconds = current_time - started_timestamp

    if age_seconds < ORPHAN_THRESHOLD_SECONDS:
        return None

    return {
        "task_arn": task.get("taskArn", ""),
        "age_seconds": int(age_seconds),
        "runner_name": tags.get("Name", ""),
        "github_repo": tags.get("GitHubRepo", ""),
    }


def _get_orphaned_ecs_tasks() -> list[dict[str, Any]]:
    """Get all orphaned ECS tasks.

    Returns:
        List of orphaned task info dicts
    """
    orphaned_tasks: list[dict[str, Any]] = []
    cluster = get_cluster_from_env()
    if not cluster:
        return orphaned_tasks

    try:
        task_arns = list_running_task_arns(cluster)
        if not task_arns:
            return orphaned_tasks

        current_time = time.time()
        for task in describe_tasks_with_tags(cluster, task_arns):
            orphaned = _is_orphaned_ecs_task(task, current_time)
            if orphaned:
                orphaned_tasks.append(orphaned)
    except ClientError as err:
        logger.error("Failed to get orphaned ECS tasks: %s", str(err))

    return orphaned_tasks


def _get_orphaned_ec2_instances() -> list[dict[str, Any]]:
    """Get all orphaned EC2 instances.

    Returns:
        List of orphaned instance info dicts
    """
    instances: list[dict[str, Any]] = []
    ec2_managed_by_tag = os.environ.get("EC2_MANAGED_BY_TAG", "")
    if not ec2_managed_by_tag:
        return instances

    try:
        response = get_ec2_client().describe_instances(
            Filters=[
                {"Name": "tag:Type", "Values": [WORKFLOW_RUNNER_TYPE_TAG]},
                {"Name": "tag:ManagedBy", "Values": [ec2_managed_by_tag]},
                {"Name": "instance-state-name", "Values": ["pending", "running"]},
            ]
        )

        current_time = time.time()
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                launch_time = instance.get("LaunchTime")
                if launch_time:
                    # LaunchTime is a datetime object from boto3
                    launch_timestamp = (
                        launch_time.timestamp()
                        if hasattr(launch_time, "timestamp")
                        else 0
                    )
                    age_seconds = current_time - launch_timestamp
                    if age_seconds >= ORPHAN_THRESHOLD_SECONDS:
                        tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                        instances.append(
                            {
                                "instance_id": instance["InstanceId"],
                                "age_seconds": int(age_seconds),
                                "runner_name": tags.get("Name", ""),
                                "github_repo": tags.get("GitHubRepo", ""),
                            }
                        )
    except ClientError as err:
        logger.error("Failed to get orphaned EC2 instances: %s", str(err))

    return instances


def _has_running_ec2_by_name(runner_name: str) -> bool:
    """Check if there's a running EC2 instance with the given name."""
    ec2_managed_by_tag = os.environ.get("EC2_MANAGED_BY_TAG", "")
    if not ec2_managed_by_tag:
        return False

    try:
        response = get_ec2_client().describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": [runner_name]},
                {"Name": "tag:ManagedBy", "Values": [ec2_managed_by_tag]},
                {"Name": "instance-state-name", "Values": ["pending", "running"]},
            ]
        )
        for reservation in response.get("Reservations", []):
            if reservation.get("Instances"):
                return True
    except ClientError as err:
        logger.error("Failed to check EC2 instance by name %s: %s", runner_name, str(err))

    return False


def _extract_run_id_from_runner_name(runner_name: str) -> str:
    """Extract run ID from runner name."""
    if runner_name.startswith("fargate-runner-"):
        return runner_name.replace("fargate-runner-", "")
    if runner_name.startswith("ec2-runner-"):
        return runner_name.replace("ec2-runner-", "")
    return ""


def _has_running_ecs_task_by_name(runner_name: str) -> bool:
    """Check if there's a running ECS task for the given runner name."""
    cluster = get_cluster_from_env()
    run_id = _extract_run_id_from_runner_name(runner_name)
    if not cluster or not run_id:
        return False

    try:
        task_arns = list_running_task_arns(cluster)
        for task in describe_tasks_with_tags(cluster, task_arns):
            tags = extract_task_tags(task)
            if tags.get("RunId") == run_id:
                return True
    except ClientError as err:
        logger.error("Failed to check ECS task by name %s: %s", runner_name, str(err))

    return False


def _runner_has_infrastructure(runner_name: str) -> bool:
    """Check if a runner has associated infrastructure."""
    has_ec2 = _has_running_ec2_by_name(runner_name)
    has_ecs = not has_ec2 and _has_running_ecs_task_by_name(runner_name)
    return has_ec2 or has_ecs


def _cleanup_orphaned_github_runners(github_token: str) -> dict[str, int]:
    """Clean up orphaned GitHub runners.

    Returns:
        Dictionary with cleanup counts
    """
    counts = {"github_cleaned": 0, "errors": 0}
    github_repo = os.environ.get("GITHUB_REPO", "")
    if not github_repo or not github_token:
        counts["errors"] = 1
        return counts

    runners = _get_all_github_runners(github_token, github_repo)
    if runners is None:
        counts["errors"] = 1
        return counts

    for runner in runners:
        status = runner.get("status", "")
        runner_name = runner.get("name", "")
        runner_id = runner.get("id")

        if status != "offline":
            continue
        if not runner_name or not runner_id:
            continue

        has_infra = _runner_has_infrastructure(runner_name)
        if has_infra:
            logger.info("Offline runner %s has infrastructure, skipping", runner_name)
            continue

        logger.info(
            "Cleaning up orphaned GitHub runner: %s (id=%s)", runner_name, runner_id
        )
        if _delete_github_runner_by_id(github_token, github_repo, runner_id, runner_name):
            counts["github_cleaned"] += 1
        else:
            counts["errors"] += 1

    logger.info(
        "Orphaned GitHub runner cleanup complete: cleaned=%d, errors=%d",
        counts["github_cleaned"],
        counts["errors"],
    )
    return counts


def _cleanup_orphaned_resources(github_token: str) -> dict[str, int]:
    """Clean up orphaned ECS tasks and EC2 instances.

    Returns:
        Dictionary with cleanup counts
    """
    counts = {"ecs_cleaned": 0, "ec2_cleaned": 0, "errors": 0}
    github_repo = os.environ.get("GITHUB_REPO", "")

    # Clean orphaned ECS tasks
    orphaned_tasks = _get_orphaned_ecs_tasks()
    for task in orphaned_tasks:
        logger.info(
            "Cleaning orphaned ECS task: %s (age=%ds)",
            task["task_arn"],
            task["age_seconds"],
        )
        if _terminate_ecs_task(task["task_arn"]):
            counts["ecs_cleaned"] += 1
            runner_name = task.get("runner_name", "")
            task_repo = task.get("github_repo") or github_repo
            if runner_name and task_repo and github_token:
                _delete_github_runner(github_token, task_repo, runner_name)
        else:
            counts["errors"] += 1

    # Clean orphaned EC2 instances
    orphaned_instances = _get_orphaned_ec2_instances()
    for instance in orphaned_instances:
        logger.info(
            "Cleaning orphaned EC2 instance: %s (age=%ds)",
            instance["instance_id"],
            instance["age_seconds"],
        )
        if terminate_ec2_instance(instance["instance_id"]):
            counts["ec2_cleaned"] += 1
            runner_name = instance.get("runner_name", "")
            instance_repo = instance.get("github_repo") or github_repo
            if runner_name and instance_repo and github_token:
                _delete_github_runner(github_token, instance_repo, runner_name)
        else:
            counts["errors"] += 1

    logger.info(
        "Orphaned resource cleanup complete: ecs=%d, ec2=%d, errors=%d",
        counts["ecs_cleaned"],
        counts["ec2_cleaned"],
        counts["errors"],
    )
    return counts


def lambda_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for stale runner cleanup.

    Args:
        _event: Lambda event (unused)
        _context: Lambda context (unused)

    Returns:
        Response dictionary with cleanup counts
    """
    logger.info("Starting orphaned runner cleanup")
    github_token = get_github_token()
    orphan_result = _cleanup_orphaned_resources(github_token)
    github_result = _cleanup_orphaned_github_runners(github_token)

    result = {
        "orphaned_ecs_cleaned": orphan_result["ecs_cleaned"],
        "orphaned_ec2_cleaned": orphan_result["ec2_cleaned"],
        "orphaned_github_cleaned": github_result["github_cleaned"],
        "errors": orphan_result["errors"] + github_result["errors"],
    }

    logger.info("Orphan cleanup complete: %s", json.dumps(result))
    return {"statusCode": 200, "body": json.dumps(result)}
