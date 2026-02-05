"""Layer 2: Configuration tests.

Verify resources created by this deployment are configured correctly.
"""
import pytest
from botocore.exceptions import ClientError

from naming_conventions import validate_name
from test_fixtures.integration import (
    check_lambda_role_has_policy,
    create_log_group_configuration_tests,
)



class TestLambdaConfiguration:
    """Verify Lambda function configuration and naming."""

    def test_lambda_function_name_is_pascalcase(self, lambda_client, lambda_function_name):
        """Verify Lambda function name uses PascalCase."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        actual_name = response['Configuration']['FunctionName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed Lambda function has invalid name '{actual_name}': {error}"
        )

    def test_lambda_timeout_is_60_seconds(self, lambda_client, lambda_function_name):
        """Verify Lambda timeout is 60 seconds."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function_configuration(
            FunctionName=lambda_function_name
        )
        timeout = response.get("Timeout", 0)
        assert timeout == 60, (
            f"Lambda timeout is {timeout}s, expected 60s. "
            "Check locals.tf lambda_timeout value."
        )

    def test_lambda_memory_is_256_mb(self, lambda_client, lambda_function_name):
        """Verify Lambda memory is 256 MB."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function_configuration(
            FunctionName=lambda_function_name
        )
        memory = response.get("MemorySize", 0)
        assert memory == 256, (
            f"Lambda memory is {memory}MB, expected 256MB. "
            "Check locals.tf lambda_memory_mb value."
        )

    def test_lambda_runtime_is_python313(self, lambda_client, lambda_function_name):
        """Verify Lambda runtime is Python 3.13."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function_configuration(
            FunctionName=lambda_function_name
        )
        runtime = response.get("Runtime", "")
        assert runtime == "python3.13", (
            f"Lambda runtime is '{runtime}', expected 'python3.13'. "
            "Check lambda.tf runtime value."
        )

    def test_lambda_architecture_is_arm64(self, lambda_client, lambda_function_name):
        """Verify Lambda architecture is arm64."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function_configuration(
            FunctionName=lambda_function_name
        )
        architectures = response.get("Architectures", [])
        assert "arm64" in architectures, (
            f"Lambda architecture is {architectures}, expected ['arm64']. "
            "Check lambda.tf architectures value."
        )


class TestLambdaRolePolicies:
    """Verify Lambda role naming and policies."""

    def test_lambda_role_name_is_pascalcase(self, iam_client, lambda_role_name):
        """Verify Lambda IAM role name uses PascalCase."""
        try:
            response = iam_client.get_role(RoleName=lambda_role_name)
            actual_name = response['Role']['RoleName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed IAM role has invalid name '{actual_name}': {error}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"Role {lambda_role_name} does not exist")
            raise

    def test_lambda_role_has_ssm_policy(self, iam_client, lambda_role_name):
        """Verify the Lambda role has SSM access policy attached."""
        try:
            response = iam_client.list_role_policies(RoleName=lambda_role_name)
            policy_names = response.get("PolicyNames", [])
            assert "SSMAccess" in policy_names, (
                f"Lambda role '{lambda_role_name}' missing SSMAccess inline policy. "
                f"Found policies: {policy_names}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"Lambda role '{lambda_role_name}' does not exist")
            raise

    def test_lambda_role_has_kms_policy(self, iam_client, lambda_role_name):
        """Verify the Lambda role has KMS policy attached."""
        check_lambda_role_has_policy(iam_client, lambda_role_name, "KMSDecrypt")
        assert True  # Explicit pass


# Use factory for log group configuration tests
TestHandlerLogGroupConfiguration = create_log_group_configuration_tests(
    log_group_fixture="handler_log_group",
    expected_retention=7,
)
