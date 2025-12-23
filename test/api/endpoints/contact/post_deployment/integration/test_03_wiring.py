"""Layer 3: Wiring tests for contact endpoint post-deployment.

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

    def test_contact_handler_has_api_gateway_permission(
        self, lambda_client, shared_config
    ):
        """Verify Lambda has permission to be invoked by API Gateway."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        try:
            response = lambda_client.get_policy(FunctionName=function_name)
            policy = response.get("Policy", "")
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

    def test_contact_handler_has_role_attached(
        self, lambda_client, shared_config
    ):
        """Verify Lambda function has IAM role attached."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        role_arn = response["Configuration"].get("Role", "")
        assert role_arn, (
            f"Lambda '{function_name}' has no IAM role attached"
        )

    def test_contact_handler_role_follows_naming_pattern(
        self, lambda_client, shared_config
    ):
        """Verify Lambda role ARN follows expected naming pattern."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        role_arn = response["Configuration"].get("Role", "")
        expected_role_suffix = "ContactHandlerServiceRole"
        assert expected_role_suffix in role_arn, (
            f"Lambda role ARN '{role_arn}' doesn't match expected pattern "
            f"containing '{expected_role_suffix}'"
        )


class TestIAMPolicyWiring:
    """Layer 3: Verify IAM role has required policies attached."""

    def test_contact_handler_role_has_basic_execution_policy(
        self, iam_client, shared_config
    ):
        """Verify IAM role has Lambda basic execution policy attached."""
        resource_prefix = shared_config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
        basic_execution = (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        assert basic_execution in policy_arns, (
            f"IAM role '{role_name}' missing AWSLambdaBasicExecutionRole policy. "
            f"Attached policies: {policy_arns}"
        )

    def test_contact_handler_role_has_ssm_policy(
        self, iam_client, shared_config
    ):
        """Verify IAM role has SSM parameter access inline policy."""
        resource_prefix = shared_config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        assert "SSMParameterAccess" in inline_policies, (
            f"IAM role '{role_name}' missing SSMParameterAccess inline policy. "
            f"Available policies: {inline_policies}"
        )

    def test_contact_handler_role_has_kms_policy(
        self, iam_client, shared_config
    ):
        """Verify IAM role has KMS decrypt inline policy."""
        resource_prefix = shared_config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        assert "KMSDecrypt" in inline_policies, (
            f"IAM role '{role_name}' missing KMSDecrypt inline policy. "
            f"Available policies: {inline_policies}"
        )

    def test_contact_handler_role_has_ses_policy(
        self, iam_client, shared_config
    ):
        """Verify IAM role has SES send email inline policy."""
        resource_prefix = shared_config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        assert "SESAccess" in inline_policies, (
            f"IAM role '{role_name}' missing SESAccess inline policy. "
            f"Available policies: {inline_policies}"
        )
