"""Layer 2: Authorization - Verify we have permission to call EC2 APIs."""
import pytest
from botocore.exceptions import ClientError



class TestEC2Authorization:
    """Layer 2: Verify we have permission to call EC2 APIs."""

    def test_can_call_describe_images_api(self, ec2_client):
        """Verify we have permission to call DescribeImages API."""
        try:
            # Use a filter that returns no results to minimize data transfer
            ec2_client.describe_images(
                Owners=["self"],
                Filters=[{"Name": "name", "Values": ["nonexistent-test-image-xyz"]}]
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call DescribeImages. "
                    "Check IAM policy for ec2:DescribeImages permission."
                )
            raise

    def test_can_call_describe_images_with_filters(self, ec2_client):
        """Verify we can call DescribeImages with tag filters."""
        try:
            ec2_client.describe_images(
                Owners=["self"],
                Filters=[{"Name": "tag:Purpose", "Values": ["nonexistent-value-xyz"]}]
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call DescribeImages with filters. "
                    "Check IAM policy for ec2:DescribeImages permission."
                )
            raise
