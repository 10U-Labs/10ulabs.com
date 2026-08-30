from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
import pytest


def iam_role_exists(client, role_name: str) -> bool:
    try:
        client.get_role(RoleName=role_name)
        return True
    except client.exceptions.NoSuchEntityException:
        return False


def get_log_group_info(client, log_group_name: str) -> dict:
    response = client.describe_log_groups(
        logGroupNamePrefix=log_group_name,
        limit=1
    )
    log_groups = response.get("logGroups", [])
    matching = [lg for lg in log_groups if lg["logGroupName"] == log_group_name]
    return {
        "name": log_group_name,
        "exists": len(matching) > 0,
        "retention": matching[0].get("retentionInDays") if matching else None
    }


def find_lifecycle_rule(client, bucket_name: str, rule_id: str) -> Optional[dict]:
    lifecycle = client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    for rule in lifecycle["Rules"]:
        if rule.get("ID") == rule_id:
            return rule
    return None


def stale_delete_markers(client, bucket_name: str, older_than_days: int = 7) -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    stale: list = []
    paginator = client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket_name):
        for marker in page.get("DeleteMarkers", []):
            if marker["LastModified"] < cutoff:
                stale.append(marker["Key"])
    return stale


@pytest.fixture(scope="session")
def caller_identity(request):
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()


@pytest.fixture(scope="session")
def _current_role_arn(request):
    identity = request.getfixturevalue("caller_identity")
    arn = identity.get("Arn", "")
    if ":assumed-role/" in arn:
        account = identity.get("Account", "")
        role_name = arn.split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}"
    return arn


@pytest.fixture(scope="session")
def current_role_name(request):
    role_arn = request.getfixturevalue("_current_role_arn")
    if not role_arn:
        return ""
    return role_arn.split("/")[-1]


@pytest.fixture(scope="session")
def scheduler_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("scheduler", region_name=region)


@pytest.fixture(scope="session")
def backup_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("backup", region_name=region)
