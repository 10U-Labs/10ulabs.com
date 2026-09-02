from typing import Any

import pytest
from botocore.exceptions import ClientError


def test_github_actions_role_exists(iam_client: Any, github_actions_role_name: str) -> None:
    try:
        response = iam_client.get_role(RoleName=github_actions_role_name)
        assert response["Role"]["RoleName"] == github_actions_role_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(f"GitHub Actions role '{github_actions_role_name}' does not exist")
        raise


def test_state_bucket_exists(s3_client: Any, state_bucket_name: str) -> None:
    try:
        response = s3_client.head_bucket(Bucket=state_bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            pytest.fail(f"State bucket '{state_bucket_name}' does not exist")
        raise


def test_hosted_zone_exists(route53_client: Any, hosted_zone_id: str) -> None:
    try:
        response = route53_client.get_hosted_zone(Id=hosted_zone_id)
        zone_id_from_response = response["HostedZone"]["Id"]
        assert zone_id_from_response.endswith(hosted_zone_id), (
            f"Zone ID mismatch: expected {hosted_zone_id}, got {zone_id_from_response}"
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchHostedZone":
            pytest.fail(f"Hosted zone '{hosted_zone_id}' does not exist")
        raise
