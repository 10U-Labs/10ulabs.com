"""Runner cleanup handler - removes orphaned infrastructure and GitHub runners.

This endpoint cleans up:
- Orphaned ECS tasks (running longer than threshold without active jobs)
- Orphaned EC2 instances (running longer than threshold without active jobs)
- Orphaned GitHub runners (offline runners without infrastructure)
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

ORPHAN_THRESHOLD_SECONDS = 300
ECS_MANAGED_BY_TAG = "ecs-runner-api"
WORKFLOW_RUNNER_TYPE_TAG = "workflow-runner"


def _get_ssm_client():
    """Get SSM client."""
    return boto3.client("ssm")


def _get_ec2_client():
    """Get EC2 client."""
    return boto3.client("ec2")


def _get_ecs_client():
    """Get ECS client."""
    return boto3.client("ecs")


def _get_github_token() -> str:
    """Get GitHub token from SSM Parameter Store."""
    secret_name = os.environ.get("GITHUB_TOKEN_SECRET_NAME", "")
    if not secret_name:
        logger.error("GITHUB_TOKEN_SECRET_NAME not set")
        return ""

    try:
        response = _get_ssm_client().get_parameter(
            Name=secret_name, WithDecryption=True
        )
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
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status == 204:
            return {}
        return json.loads(response.read().decode())


def _get_all_github_runners(
    github_token: str, github_repo: str
) -> list[dict[str, Any]] | None:
    """Get all GitHub runners for a repository with pagination."""
    runners: list[dict[str, Any]] = []
    page = 1

    try:
        while True:
            path = f"/repos/{github_repo}/actions/runners?per_page=100&page={page}"
            data = _github_api_request("GET", path, github_token)
            page_runners = data.get("runners", [])
            runners.extend(page_runners)
            if len(page_runners) < 100:
                break
            page += 1
        return runners
    except urllib.error.HTTPError as err:
        logger.error("Failed to list GitHub runners: %s", str(err))
        return None


def _is_job_active(github_token: str, github_repo: str, job_id: str) -> bool:
    """Check if a GitHub Actions job is still active."""
    if not job_id:
        return False
    try:
        path = f"/repos/{github_repo}/actions/jobs/{job_id}"
        data = _github_api_request("GET", path, github_token)
        status = data.get("status", "")
        return status in ("queued", "in_progress")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
        logger.error("Failed to check job %s status: %s", job_id, str(err))
        return True


def _delete_github_runner_by_id(
    github_token: str, github_repo: str, runner_id: int, runner_name: str
) -> bool:
    """Delete a GitHub runner by ID."""
    try:
        _github_api_request(
            "DELETE", f"/repos/{github_repo}/actions/runners/{runner_id}",
            github_token
        )
        logger.info("Deleted GitHub runner: %s", runner_name)
        return True
    except urllib.error.HTTPError as err:
        if err.code == 204:
            logger.info("Deleted GitHub runner: %s", runner_name)
            return True
        logger.error("Failed to delete GitHub runner %s: %s", runner_name, str(err))
        return False


def _get_cluster_from_env() -> str:
    """Get ECS cluster from environment."""
    return os.environ.get("ECS_CLUSTER", "")


def _list_running_task_arns(cluster: str) -> list[str]:
    """List running ECS task ARNs."""
    task_arns: list[str] = []
    try:
        paginator = _get_ecs_client().get_paginator("list_tasks")
        for page in paginator.paginate(cluster=cluster, desiredStatus="RUNNING"):
            task_arns.extend(page.get("taskArns", []))
    except ClientError as err:
        logger.error("Failed to list tasks: %s", str(err))
    return task_arns


def _describe_tasks_with_tags(cluster: str, task_arns: list[str]) -> list[dict]:
    """Describe ECS tasks with tags."""
    tasks: list[dict] = []
    if not task_arns:
        return tasks

    try:
        for i in range(0, len(task_arns), 100):
            batch = task_arns[i:i + 100]
            response = _get_ecs_client().describe_tasks(
                cluster=cluster, tasks=batch, include=["TAGS"]
            )
            tasks.extend(response.get("tasks", []))
    except ClientError as err:
        logger.error("Failed to describe tasks: %s", str(err))
    return tasks


def _stop_ecs_task(cluster: str, task_arn: str, reason: str) -> bool:
    """Stop an ECS task."""
    try:
        _get_ecs_client().stop_task(cluster=cluster, task=task_arn, reason=reason)
        logger.info("Stopped ECS task: %s", task_arn)
        return True
    except ClientError as err:
        logger.error("Failed to stop task %s: %s", task_arn, str(err))
        return False


def _terminate_ec2_instance(instance_id: str) -> bool:
    """Terminate an EC2 instance."""
    try:
        _get_ec2_client().terminate_instances(InstanceIds=[instance_id])
        logger.info("Terminated EC2 instance: %s", instance_id)
        return True
    except ClientError as err:
        logger.error("Failed to terminate instance %s: %s", instance_id, str(err))
        return False


def _is_orphaned_ecs_task(
    task: dict[str, Any], current_time: float
) -> dict[str, Any] | None:
    """Check if an ECS task is orphaned."""
    tags = {t["key"]: t["value"] for t in task.get("tags", [])}

    if tags.get("Type") != WORKFLOW_RUNNER_TYPE_TAG:
        return None
    if tags.get("ManagedBy") != ECS_MANAGED_BY_TAG:
        return None

    started_at = task.get("startedAt")
    if not started_at:
        return None

    started_timestamp = started_at.timestamp() if hasattr(started_at, 'timestamp') else 0
    age_seconds = current_time - started_timestamp

    if age_seconds < ORPHAN_THRESHOLD_SECONDS:
        return None

    return {
        "task_arn": task.get("taskArn", ""),
        "age_seconds": int(age_seconds),
        "job_id": tags.get("GitHubJobId", ""),
        "github_repo": tags.get("GitHubRepo", ""),
    }


def _get_orphaned_ecs_tasks() -> list[dict[str, Any]]:
    """Get all orphaned ECS tasks."""
    orphaned_tasks: list[dict[str, Any]] = []
    cluster = _get_cluster_from_env()
    if not cluster:
        return orphaned_tasks

    try:
        task_arns = _list_running_task_arns(cluster)
        if not task_arns:
            return orphaned_tasks

        current_time = time.time()
        for task in _describe_tasks_with_tags(cluster, task_arns):
            orphaned = _is_orphaned_ecs_task(task, current_time)
            if orphaned:
                orphaned_tasks.append(orphaned)
    except ClientError as err:
        logger.error("Failed to get orphaned ECS tasks: %s", str(err))

    return orphaned_tasks


def _get_orphaned_ec2_instances() -> list[dict[str, Any]]:
    """Get all orphaned EC2 instances."""
    instances: list[dict[str, Any]] = []
    ec2_managed_by_tag = os.environ.get("EC2_MANAGED_BY_TAG", "")
    if not ec2_managed_by_tag:
        return instances

    try:
        response = _get_ec2_client().describe_instances(
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
                    launch_timestamp = (
                        launch_time.timestamp()
                        if hasattr(launch_time, "timestamp")
                        else 0
                    )
                    age_seconds = current_time - launch_timestamp
                    if age_seconds >= ORPHAN_THRESHOLD_SECONDS:
                        tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                        instances.append({
                            "instance_id": instance["InstanceId"],
                            "age_seconds": int(age_seconds),
                            "job_id": tags.get("GitHubJobId", ""),
                            "github_repo": tags.get("GitHubRepo", ""),
                        })
    except ClientError as err:
        logger.error("Failed to get orphaned EC2 instances: %s", str(err))

    return instances


def _extract_run_id_from_runner_name(runner_name: str) -> str:
    """Extract run ID from runner name."""
    if runner_name.startswith("fargate-runner-"):
        return runner_name.replace("fargate-runner-", "")
    if runner_name.startswith("ec2-runner-"):
        return runner_name.replace("ec2-runner-", "")
    return ""


def _has_running_ec2_by_name(runner_name: str) -> bool:
    """Check if there's a running EC2 instance with the given name."""
    ec2_managed_by_tag = os.environ.get("EC2_MANAGED_BY_TAG", "")
    if not ec2_managed_by_tag:
        return False

    try:
        response = _get_ec2_client().describe_instances(
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


def _has_running_ecs_task_by_name(runner_name: str) -> bool:
    """Check if there's a running ECS task for the given runner name."""
    cluster = _get_cluster_from_env()
    run_id = _extract_run_id_from_runner_name(runner_name)
    if not cluster or not run_id:
        return False

    try:
        task_arns = _list_running_task_arns(cluster)
        for task in _describe_tasks_with_tags(cluster, task_arns):
            tags = {t["key"]: t["value"] for t in task.get("tags", [])}
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
    """Clean up orphaned GitHub runners."""
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

    return counts


def _cleanup_orphaned_resources(github_token: str) -> dict[str, int]:
    """Clean up orphaned ECS tasks and EC2 instances."""
    counts = {
        "ecs_cleaned": 0, "ecs_skipped": 0,
        "ec2_cleaned": 0, "ec2_skipped": 0,
        "errors": 0
    }
    github_repo = os.environ.get("GITHUB_REPO", "")
    cluster = _get_cluster_from_env()

    # Clean orphaned ECS tasks
    orphaned_tasks = _get_orphaned_ecs_tasks()
    for task in orphaned_tasks:
        job_id = task.get("job_id", "")
        task_repo = task.get("github_repo") or github_repo

        if job_id and task_repo and github_token:
            if _is_job_active(github_token, task_repo, job_id):
                logger.info(
                    "Skipping ECS task with active job: %s (job_id=%s)",
                    task["task_arn"], job_id,
                )
                counts["ecs_skipped"] += 1
                continue

        logger.info(
            "Cleaning orphaned ECS task: %s (age=%ds)",
            task["task_arn"], task["age_seconds"],
        )
        if cluster and _stop_ecs_task(cluster, task["task_arn"], "Stale runner cleanup"):
            counts["ecs_cleaned"] += 1
        else:
            counts["errors"] += 1

    # Clean orphaned EC2 instances
    orphaned_instances = _get_orphaned_ec2_instances()
    for instance in orphaned_instances:
        job_id = instance.get("job_id", "")
        instance_repo = instance.get("github_repo") or github_repo

        if job_id and instance_repo and github_token:
            if _is_job_active(github_token, instance_repo, job_id):
                logger.info(
                    "Skipping EC2 instance with active job: %s (job_id=%s)",
                    instance["instance_id"], job_id,
                )
                counts["ec2_skipped"] += 1
                continue

        logger.info(
            "Cleaning orphaned EC2 instance: %s (age=%ds)",
            instance["instance_id"], instance["age_seconds"],
        )
        if _terminate_ec2_instance(instance["instance_id"]):
            counts["ec2_cleaned"] += 1
        else:
            counts["errors"] += 1

    return counts


def _run_cleanup() -> dict[str, Any]:
    """Run the cleanup process."""
    logger.info("Starting orphaned runner cleanup")
    github_token = _get_github_token()
    orphan_result = _cleanup_orphaned_resources(github_token)
    github_result = _cleanup_orphaned_github_runners(github_token)

    result = {
        "orphaned_ecs_cleaned": orphan_result["ecs_cleaned"],
        "orphaned_ecs_skipped": orphan_result["ecs_skipped"],
        "orphaned_ec2_cleaned": orphan_result["ec2_cleaned"],
        "orphaned_ec2_skipped": orphan_result["ec2_skipped"],
        "orphaned_github_cleaned": github_result["github_cleaned"],
        "errors": orphan_result["errors"] + github_result["errors"],
    }

    logger.info("Orphan cleanup complete: %s", json.dumps(result))
    return result


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for stale runner cleanup.

    Handles both scheduled invocations (EventBridge) and SQS-triggered events.

    Args:
        event: Lambda event
        _context: Lambda context (unused)

    Returns:
        Response dictionary with cleanup counts
    """
    logger.info("Received event: %s", json.dumps(event))

    # Handle SQS event (API Gateway trigger)
    if "Records" in event:
        results = []
        for _ in event["Records"]:
            result = _run_cleanup()
            results.append(result)
        return {
            "statusCode": 200,
            "body": json.dumps({"results": results}),
        }

    # Handle direct invocation (scheduled or manual)
    result = _run_cleanup()
    return {"statusCode": 200, "body": json.dumps(result)}
