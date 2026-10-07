from datetime import datetime, timedelta, timezone
from typing import Any, Optional


def iam_role_exists(client: Any, role_name: str) -> bool:
    try:
        client.get_role(RoleName=role_name)
        return True
    except client.exceptions.NoSuchEntityException:
        return False


def find_lifecycle_rule(client: Any, bucket_name: str, rule_id: str) -> Optional[dict]:
    lifecycle = client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    for rule in lifecycle["Rules"]:
        if rule.get("ID") == rule_id:
            return rule
    return None


def stale_delete_markers(client: Any, bucket_name: str, older_than_days: int = 7) -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    stale: list = []
    paginator = client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket_name):
        for marker in page.get("DeleteMarkers", []):
            if marker["LastModified"] < cutoff:
                stale.append(marker["Key"])
    return stale
