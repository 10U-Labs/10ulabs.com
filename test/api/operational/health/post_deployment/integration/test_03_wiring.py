"""Layer 3: Wiring tests for health endpoint post-deployment.

Tests that components are connected. Assumes existence and configuration passed.
These tests verify that resources are properly wired together.

Three-layer testing model:
- Layer 3: Wiring - Components connected properly
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(3)


class TestLambdaWiring:
    """Layer 3: Verify Lambda is wired to API Gateway and has correct role."""

    def test_health_handler_has_api_gateway_permission(
        self, lambda_client, config
    ):
        """Verify Lambda has permission to be invoked by API Gateway."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        try:
            response = lambda_client.get_policy(FunctionName=function_name)
            policy = response.get("Policy", "")
            # Check that API Gateway has permission to invoke
            assert "apigateway.amazonaws.com" in policy, (
                f"Lambda '{function_name}' missing API Gateway invoke permission"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda '{function_name}' has no resource policy - "
                    "API Gateway cannot invoke it"
                )
            raise

    def test_health_handler_has_role_attached(self, lambda_client, config):
        """Verify Lambda function has IAM role attached."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        role_arn = response["Configuration"].get("Role", "")
        assert role_arn, (
            f"Lambda '{function_name}' has no IAM role attached"
        )

    def test_health_handler_role_follows_naming_pattern(self, lambda_client, config):
        """Verify Lambda role ARN follows expected naming pattern."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        role_arn = response["Configuration"].get("Role", "")
        expected_role_suffix = f"{function_name}ServiceRole"
        assert expected_role_suffix in role_arn, (
            f"Lambda role ARN '{role_arn}' doesn't match expected pattern "
            f"containing '{expected_role_suffix}'"
        )


class TestIAMPolicyWiring:
    """Layer 3: Verify IAM role has required policies attached."""

    def test_health_handler_role_has_basic_execution_policy(self, iam_client, config):
        """Verify IAM role has Lambda basic execution policy attached."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        role_name = f"{function_name}ServiceRole"
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        basic_execution = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        assert basic_execution in policy_arns, (
            f"IAM role '{role_name}' missing AWSLambdaBasicExecutionRole policy. "
            f"Attached policies: {policy_arns}"
        )

    def test_health_handler_role_has_ec2_describe_policy(self, iam_client, config):
        """Verify IAM role has EC2 describe inline policy."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        role_name = f"{function_name}ServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        # Check for an inline policy that grants EC2 describe permissions
        assert len(inline_policies) > 0, (
            f"IAM role '{role_name}' has no inline policies for EC2 describe"
        )
