"""Layer 1-2 tests: AWS credentials and API authorization.

These tests MUST run first. All other tests depend on valid credentials.
"""
import pytest
from botocore.exceptions import ClientError


class TestAWSCredentialsExistence:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_01_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        assert sts_client is not None, (
            "No AWS credentials found. Configure via environment variables, "
            "~/.aws/credentials, or IAM role."
        )

    def test_02_can_call_sts_api(self, sts_client):
        """Verify credentials are valid by calling STS."""
        try:
            response = sts_client.get_caller_identity()
            assert response.get("Account"), "STS returned no account ID"
        except ClientError as e:
            pytest.fail(
                f"Credentials invalid or expired: {e.response['Error']['Message']}"
            )


class TestEC2APIAuthorization:
    """Layer 2: Verify we have permission to call EC2 APIs."""

    def test_01_can_call_describe_vpcs(self, ec2_client):
        """Verify we have permission to call EC2 DescribeVpcs."""
        try:
            ec2_client.describe_vpcs(MaxResults=5)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call EC2 DescribeVpcs. "
                    "Check IAM policy has ec2:DescribeVpcs."
                )
            raise

    def test_02_can_call_describe_images(self, ec2_client):
        """Verify we have permission to call EC2 DescribeImages."""
        try:
            ec2_client.describe_images(Owners=["self"], MaxResults=5)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call EC2 DescribeImages. "
                    "Check IAM policy has ec2:DescribeImages."
                )
            raise
