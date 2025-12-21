"""Layer 2: Authorization tests for www_shared pre-deployment validation.

Verify permission to inspect prerequisite resources (not existence, not capability).
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.layer(2)


def test_can_call_iam_get_role(iam_client, github_actions_role_name):
    """Verify permission to call iam:GetRole."""
    try:
        iam_client.get_role(RoleName=github_actions_role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail("No permission to call iam:GetRole")
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise


def test_can_call_iam_list_attached_role_policies(iam_client, github_actions_role_name):
    """Verify permission to call iam:ListAttachedRolePolicies."""
    try:
        iam_client.list_attached_role_policies(RoleName=github_actions_role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail("No permission to call iam:ListAttachedRolePolicies")
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise


def test_can_call_s3_head_bucket(s3_client, state_bucket_name):
    """Verify permission to call s3:HeadBucket."""
    try:
        s3_client.head_bucket(Bucket=state_bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:HeadBucket on '{state_bucket_name}'")
        if error_code != "404":
            raise


def test_can_call_route53_get_hosted_zone(route53_client, hosted_zone_id):
    """Verify permission to call route53:GetHostedZone."""
    try:
        route53_client.get_hosted_zone(Id=hosted_zone_id)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call route53:GetHostedZone on '{hosted_zone_id}'")
        if error_code != "NoSuchHostedZone":
            raise


def test_can_call_route53_list_resource_record_sets(route53_client, hosted_zone_id):
    """Verify permission to call route53:ListResourceRecordSets."""
    try:
        route53_client.list_resource_record_sets(HostedZoneId=hosted_zone_id, MaxItems="1")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(
                f"No permission to call route53:ListResourceRecordSets on '{hosted_zone_id}'"
            )
        if error_code != "NoSuchHostedZone":
            raise
