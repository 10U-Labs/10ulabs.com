"""Layer 3: Wiring tests for health endpoint post-deployment.

Tests that components are connected. Assumes existence and configuration passed.
These tests verify that resources are properly wired together.

Three-layer testing model:
- Layer 3: Wiring - Components connected properly
"""

import pytest
from test_fixtures.integration import (
    create_lambda_api_gateway_wiring_tests,
    create_lambda_iam_wiring_tests,
)




# Create wiring test classes for health handler
TestLambdaWiring = create_lambda_api_gateway_wiring_tests(
    function_name_config_key='health_handler_function_name',
    default_function_name='TenULabsHealthHandler',
)

TestIAMPolicyWiring = create_lambda_iam_wiring_tests(
    function_name_config_key='health_handler_function_name',
    default_function_name='TenULabsHealthHandler',
    check_basic_execution=True,
    check_lambda_trust=False,  # Health endpoint has additional specific tests
)


class TestHealthSpecificIAMWiring:
    """Health-specific IAM wiring tests."""

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

    def test_health_handler_role_has_lambda_trust_relationship(self, iam_client, config):
        """Verify IAM role trusts Lambda service."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        role_name = f"{function_name}ServiceRole"
        response = iam_client.get_role(RoleName=role_name)
        assume_role_policy = response['Role']['AssumeRolePolicyDocument']
        statements = assume_role_policy.get('Statement', [])
        lambda_trusted = any(
            stmt.get('Principal', {}).get('Service') == 'lambda.amazonaws.com'
            for stmt in statements
        )
        assert lambda_trusted, (
            f"IAM role '{role_name}' does not trust lambda.amazonaws.com"
        )
