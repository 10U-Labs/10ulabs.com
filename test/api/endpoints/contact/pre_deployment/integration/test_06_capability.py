"""Layer 6: Capability tests for contact endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
These tests verify we have the capability to deploy the contact endpoint.

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(6)


class TestDeploymentCapabilities:
    """Layer 6: Verify we have capability to deploy contact endpoint resources."""

    def test_can_list_lambda_functions(self, lambda_client):
        """Verify we can list Lambda functions (required for deployment)."""
        try:
            lambda_client.list_functions(MaxItems=1)
        except ClientError as e:
            pytest.fail(
                f"Cannot list Lambda functions, deployment will fail: {e}"
            )

    def test_can_list_iam_roles(self, iam_client):
        """Verify we can list IAM roles (required for deployment)."""
        try:
            iam_client.list_roles(MaxItems=1)
        except ClientError as e:
            pytest.fail(
                f"Cannot list IAM roles, deployment will fail: {e}"
            )

    def test_can_describe_ssm_parameters(self, ssm_client):
        """Verify we can describe SSM parameters (required for deployment)."""
        try:
            ssm_client.describe_parameters(MaxResults=1)
        except ClientError as e:
            pytest.fail(
                f"Cannot describe SSM parameters, deployment will fail: {e}"
            )
