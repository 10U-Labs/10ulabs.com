"""Layer 2: Configuration tests for health endpoint post-deployment.

Tests that resources have correct settings. Assumes existence tests passed.
These tests verify that resources created by THIS workflow are configured correctly.

Three-layer testing model:
- Layer 2: Configuration - Resources configured correctly
"""

import pytest
from naming_conventions import validate_name


pytestmark = pytest.mark.layer(2)


class TestLambdaConfiguration:
    """Layer 2: Verify Lambda function is configured correctly."""

    def test_health_handler_uses_python_runtime(self, lambda_client, config):
        """Verify Lambda uses Python 3.13 runtime."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        runtime = response["Configuration"]["Runtime"]
        assert runtime == "python3.13", (
            f"Lambda runtime should be python3.13, got: {runtime}"
        )

    def test_health_handler_uses_arm64_architecture(self, lambda_client, config):
        """Verify Lambda uses ARM64 architecture."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        architectures = response["Configuration"].get("Architectures", [])
        assert "arm64" in architectures, (
            f"Lambda should use arm64 architecture, got: {architectures}"
        )

    def test_health_handler_has_handler_configured(self, lambda_client, config):
        """Verify Lambda has correct handler configured."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        handler = response["Configuration"]["Handler"]
        assert handler == "handler.handler", (
            f"Lambda handler should be handler.handler, got: {handler}"
        )

    def test_health_handler_has_environment_variables(self, lambda_client, config):
        """Verify Lambda has required environment variables."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        env_vars = response["Configuration"].get("Environment", {}).get(
            "Variables", {}
        )
        required_vars = ["SECURITY_GROUPS", "SUBNETS", "VPC_ID"]
        missing = [v for v in required_vars if v not in env_vars]
        assert len(missing) == 0, (
            f"Lambda missing required environment variables: {missing}"
        )


class TestCloudWatchLogsConfiguration:
    """Layer 2: Verify CloudWatch log group is configured correctly."""

    def test_health_handler_log_group_has_retention_set(self, health_handler_log_group):
        """Verify log group has retention period set."""
        assert health_handler_log_group["retention"] is not None, (
            f"Log group '{health_handler_log_group['name']}' should have retention set"
        )

    def test_health_handler_log_group_retention_is_7_days(self, health_handler_log_group):
        """Verify log group retention is 7 days."""
        retention = health_handler_log_group["retention"]
        assert retention == 7, (
            f"Log group retention should be 7 days, got: {retention}"
        )


class TestNamingConventions:
    """Layer 2: Verify resources follow naming conventions."""

    def test_health_handler_lambda_name_is_pascalcase(self, lambda_client, config):
        """Verify Lambda function name uses PascalCase."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        response = lambda_client.get_function(FunctionName=function_name)
        actual_name = response["Configuration"]["FunctionName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"Lambda function has invalid name '{actual_name}': {error}"
        )

    def test_health_handler_role_name_is_pascalcase(self, iam_client, config):
        """Verify IAM role name uses PascalCase."""
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        role_name = f"{function_name}ServiceRole"
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response["Role"]["RoleName"]
        error = validate_name(actual_name)
        assert error is None, (
            f"IAM role has invalid name '{actual_name}': {error}"
        )
