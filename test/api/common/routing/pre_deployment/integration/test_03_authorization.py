"""Layer 3: Authorization tests for api_common_routing pre-deployment validation.

Verify permission to inspect prerequisite resources (not existence, not capability).
"""
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    Layer2IAMAuthorizationTests,
    Layer2S3AuthorizationTests,
)



class TestS3Authorization(Layer2S3AuthorizationTests):
    """Inherit S3 authorization tests for state bucket."""


class TestIAMAuthorization(Layer2IAMAuthorizationTests):
    """Inherit IAM authorization tests for current role."""


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
