"""Layer 6: Capability tests for rack_designer endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
These tests verify we have the capability to deploy the rack_designer endpoint.

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(6)


class TestDeploymentCapabilities:
    """Layer 6: Verify we have capability to deploy rack_designer resources."""

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

    def test_can_list_dynamodb_tables(self, dynamodb_client):
        """Verify we can list DynamoDB tables (required for deployment)."""
        try:
            dynamodb_client.list_tables(Limit=1)
        except ClientError as e:
            pytest.fail(
                f"Cannot list DynamoDB tables, deployment will fail: {e}"
            )

    def test_can_list_log_groups(self, logs_client):
        """Verify we can list CloudWatch log groups (required for deployment)."""
        try:
            logs_client.describe_log_groups(limit=1)
        except ClientError as e:
            pytest.fail(
                f"Cannot list CloudWatch log groups, deployment will fail: {e}"
            )
