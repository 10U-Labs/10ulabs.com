"""Layer 3: Authorization tests for api_shared_routing pre-deployment validation.

Verify permission to inspect prerequisite resources (not existence, not capability).
"""
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import Layer2S3AuthorizationTests

pytestmark = pytest.mark.layer(3)


class TestS3Authorization(Layer2S3AuthorizationTests):
    """Inherit S3 authorization tests for state bucket."""


def test_can_call_s3_head_bucket_on_central_logs(s3_client, central_logs_bucket_name):
    """Verify permission to call s3:HeadBucket on central logs bucket."""
    if not central_logs_bucket_name:
        pytest.skip("central_logs_bucket_name not available")
    try:
        s3_client.head_bucket(Bucket=central_logs_bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(
                f"No permission to call s3:HeadBucket on '{central_logs_bucket_name}'"
            )
        if error_code != "404":
            raise


def test_can_call_iam_get_role(iam_client, current_role_name):
    """Verify permission to call iam:GetRole."""
    if not current_role_name:
        pytest.skip("Could not determine current role name")
    try:
        iam_client.get_role(RoleName=current_role_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(
                f"No permission to call iam:GetRole on '{current_role_name}'"
            )
        # NoSuchEntity means role doesn't exist but we have permission to check - OK
        if error_code != "NoSuchEntity":
            raise


def test_can_call_iam_list_attached_role_policies(iam_client, current_role_name):
    """Verify permission to call iam:ListAttachedRolePolicies."""
    if not current_role_name:
        pytest.skip("Could not determine current role name")
    try:
        iam_client.list_attached_role_policies(RoleName=current_role_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(
                f"No permission to call iam:ListAttachedRolePolicies on '{current_role_name}'"
            )
        if error_code != "NoSuchEntity":
            raise
