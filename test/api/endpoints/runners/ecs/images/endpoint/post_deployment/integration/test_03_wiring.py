"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration import create_lambda_execution_role_wiring_tests


# Create Lambda execution role wiring tests using lambda_config fixture
TestLambdaExecutionRole = create_lambda_execution_role_wiring_tests(
    fixture_name="lambda_config"
)


class TestLambdaRolePolicies:
    """Verify IAM role has required policies attached."""

    def test_lambda_role_has_basic_execution_policy(self, lambda_role_policies):
        """Verify IAM role has Lambda basic execution policy attached."""
        policy_arns = [p["PolicyArn"] for p in lambda_role_policies["attached"]]
        basic_execution = (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        assert basic_execution in policy_arns, (
            f"Lambda role missing AWSLambdaBasicExecutionRole. "
            f"Attached policies: {policy_arns}"
        )

    def test_lambda_role_has_ecr_access_policy(self, lambda_role_policies):
        """Verify IAM role has ECR access inline policy."""
        inline_policies = lambda_role_policies["inline"]
        assert "ECRAccess" in inline_policies, (
            f"Lambda role missing 'ECRAccess' inline policy. "
            f"Inline policies: {inline_policies}"
        )

    def test_lambda_role_has_ssm_access_policy(self, lambda_role_policies):
        """Verify IAM role has SSM access inline policy."""
        inline_policies = lambda_role_policies["inline"]
        assert "SSMAccess" in inline_policies, (
            f"Lambda role missing 'SSMAccess' inline policy. "
            f"Inline policies: {inline_policies}"
        )

    def test_lambda_role_has_kms_access_policy(self, lambda_role_policies):
        """Verify IAM role has KMS access inline policy."""
        inline_policies = lambda_role_policies["inline"]
        assert "KMSDecryptPermissions" in inline_policies, (
            f"Lambda role missing 'KMSDecryptPermissions' inline policy. "
            f"Inline policies: {inline_policies}"
        )


class TestAPIGatewayWiring:
    """Verify Lambda is wired to API Gateway."""

    def test_api_gateway_can_invoke_lambda(self, lambda_client, lambda_function):
        """Verify API Gateway has permission to invoke Lambda."""
        function_name = lambda_function["FunctionName"]
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
