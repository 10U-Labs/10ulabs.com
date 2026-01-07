"""Layer 3: Authorization tests for www home page deployment.

Test that credentials have permission to INSPECT prerequisite resources.
Not existence, not capability - just authorization to check.
"""
import pytest
from botocore.exceptions import ClientError


class TestS3Authorization:
    """Layer 3: Verify permission to inspect S3 bucket."""

    def test_can_describe_s3_bucket(self, s3_client, www_common_outputs):
        """Verify permission to inspect the website S3 bucket."""
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                pytest.fail("No permission to inspect S3 bucket")
            if error_code == "404":
                pass  # Bucket doesn't exist - but we have permission to check

    def test_can_list_s3_bucket_objects(self, s3_client, www_common_outputs):
        """Verify permission to list objects in the S3 bucket."""
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail("No permission to list S3 bucket objects")
            if error_code == "NoSuchBucket":
                pass  # Bucket doesn't exist - but we have permission to check


class TestCloudFrontAuthorization:
    """Layer 3: Verify permission to inspect CloudFront distribution."""

    def test_can_describe_cloudfront_distribution(
        self, cloudfront_client, www_common_outputs
    ):
        """Verify permission to inspect CloudFront distribution."""
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        try:
            cloudfront_client.get_distribution(Id=distribution_id)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail("No permission to inspect CloudFront distribution")
            if error_code == "NoSuchDistribution":
                pass  # Distribution doesn't exist - but we have permission to check

    def test_can_list_cloudfront_distributions(self, cloudfront_client):
        """Verify permission to list CloudFront distributions."""
        try:
            cloudfront_client.list_distributions(MaxItems="1")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail("No permission to list CloudFront distributions")
