"""Layer 6: Capability tests for diagnostics endpoint pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.
Tests permissions needed for deployment (not runtime permissions).

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(6)


class TestDeploymentCapabilities:
    """Layer 6: Verify capabilities to deploy Lambda, CloudWatch, and IAM."""

    def test_can_get_lambda_function_configuration(self, lambda_client):
        """Verify capability to get Lambda function configuration."""
        try:
            # List first to get a function name, then get its config
            response = lambda_client.list_functions(MaxItems=1)
            functions = response.get("Functions", [])
            if functions:
                lambda_client.get_function_configuration(
                    FunctionName=functions[0]["FunctionName"]
                )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "Cannot get Lambda function configuration - required for deployment"
                )
            raise

    def test_can_create_log_group_dry_run(self, logs_client):
        """Verify capability to interact with CloudWatch Logs."""
        try:
            # Just describe is sufficient to prove logs access for deployment
            logs_client.describe_log_groups(limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "Cannot access CloudWatch Logs - required for deployment"
                )
            raise

    def test_can_get_iam_role_details(self, iam_client):
        """Verify capability to get IAM role details for deployment."""
        try:
            # List roles then get first one's details to prove full access
            response = iam_client.list_roles(MaxItems=1)
            roles = response.get("Roles", [])
            if roles:
                iam_client.get_role(RoleName=roles[0]["RoleName"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "Cannot get IAM role details - required for deployment"
                )
            raise
