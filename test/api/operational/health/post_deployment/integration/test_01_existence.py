"""Layer 1: Existence tests for health endpoint post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(1)


class TestDeployedResourcesExist:
    """Layer 1: Verify Lambda, IAM role, and log group exist."""

    def test_health_handler_lambda_exists(self, lambda_client, config):
        """Verify TenULabsHealthHandler Lambda function exists."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            assert response["Configuration"]["FunctionName"] == function_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{function_name}' does not exist. "
                    "Run terraform apply in src/api/operational/health/"
                )
            raise

    def test_health_handler_iam_role_exists(self, iam_client, config):
        """Verify HealthHandler IAM role exists."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        role_name = f"{function_name}ServiceRole"
        try:
            response = iam_client.get_role(RoleName=role_name)
            assert response["Role"]["RoleName"] == role_name
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(
                f"IAM role '{role_name}' does not exist. "
                "Run terraform apply in src/api/operational/health/"
            )

    def test_health_handler_log_group_exists(self, health_handler_log_group):
        """Verify CloudWatch log group for HealthHandler exists."""
        assert health_handler_log_group["exists"], (
            f"CloudWatch log group '{health_handler_log_group['name']}' does not exist"
        )
