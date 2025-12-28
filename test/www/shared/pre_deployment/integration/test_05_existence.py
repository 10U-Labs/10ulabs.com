"""Layer 5: Existence tests for www_shared pre-deployment validation.

Verify prerequisite resources exist. Assumes state tests passed.
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.layer(5)


def test_github_actions_role_exists(iam_client, github_actions_role_name):
    """Verify GitHub Actions IAM role exists."""
    try:
        response = iam_client.get_role(RoleName=github_actions_role_name)
        assert response["Role"]["RoleName"] == github_actions_role_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(f"GitHub Actions role '{github_actions_role_name}' does not exist")
        raise


def test_state_bucket_exists(s3_client, state_bucket_name):
    """Verify Terraform state bucket exists."""
    try:
        response = s3_client.head_bucket(Bucket=state_bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            pytest.fail(f"State bucket '{state_bucket_name}' does not exist")
        raise


def test_hosted_zone_exists(route53_client, hosted_zone_id):
    """Verify Route53 hosted zone exists."""
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
