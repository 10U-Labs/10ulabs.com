"""Layer 6: Capability tests for api/common/parameters pre-deployment.

Tests that we can perform required operations for deployment.

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(6)


class TestSSMCapability:
    """Layer 6: Verify SSM capabilities for deployment."""

    def test_can_describe_parameters(self, ssm_client):
        """Verify we can describe SSM parameters."""
        try:
            ssm_client.describe_parameters(MaxResults=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to describe SSM parameters. "
                    "Check IAM permissions for ssm:DescribeParameters."
                )
            raise

    def test_can_get_parameters_by_path(self, ssm_client):
        """Verify we can get SSM parameters by path."""
        try:
            ssm_client.get_parameters_by_path(Path="/", MaxResults=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to get SSM parameters by path. "
                    "Check IAM permissions for ssm:GetParametersByPath."
                )
            raise
