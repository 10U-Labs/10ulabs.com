"""Tests to validate circuit breaker reset Lambda infrastructure.

These tests verify that the circuit breaker reset Lambda and its
associated resources exist and are properly configured.

Five-layer testing model:
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
"""

import pytest
from botocore.exceptions import ClientError


class TestCircuitBreakerResetLambdaExists:
    """Layer 3: Verify circuit breaker reset Lambda exists."""

    def test_01_lambda_function_exists(self, lambda_client, config):
        """Verify the circuit breaker reset Lambda function exists."""
        function_name = f"{config['resource_prefix']}CircuitBreakerReset"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            assert response['Configuration']['FunctionName'] == function_name
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.fail(
                    f"Lambda function {function_name} not found. "
                    "Run: cd src/api/endpoints/runners && terraform apply"
                )
            raise

    def test_02_lambda_function_is_arm64(self, lambda_client, config):
        """Verify the Lambda function uses ARM64 architecture."""
        function_name = f"{config['resource_prefix']}CircuitBreakerReset"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            architectures = response['Configuration'].get('Architectures', [])
            assert 'arm64' in architectures
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip("Lambda function not found - covered by existence test")
            raise


class TestCircuitBreakerResetLambdaConfiguration:
    """Layer 4: Verify circuit breaker reset Lambda is configured correctly."""

    def test_01_lambda_has_correct_runtime(self, lambda_client, config):
        """Verify Lambda uses Python 3.13 runtime."""
        function_name = f"{config['resource_prefix']}CircuitBreakerReset"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            runtime = response['Configuration']['Runtime']
            assert runtime == 'python3.13', (
                f"Expected runtime 'python3.13', got '{runtime}'"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip("Lambda function not found - covered by existence test")
            raise

    def test_02_lambda_has_correct_handler(self, lambda_client, config):
        """Verify Lambda has correct handler configuration."""
        function_name = f"{config['resource_prefix']}CircuitBreakerReset"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            handler = response['Configuration']['Handler']
            assert handler == 'circuit_breaker_reset.lambda_handler', (
                f"Expected handler 'circuit_breaker_reset.lambda_handler', got '{handler}'"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip("Lambda function not found - covered by existence test")
            raise

    def test_03_lambda_has_environment_variables(self, lambda_client, config):
        """Verify Lambda has required environment variables."""
        function_name = f"{config['resource_prefix']}CircuitBreakerReset"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            env_vars = response['Configuration'].get('Environment', {}).get(
                'Variables', {}
            )
            assert 'WEBHOOK_FUNCTION_NAME' in env_vars, (
                "Missing WEBHOOK_FUNCTION_NAME environment variable"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip("Lambda function not found - covered by existence test")
            raise

    def test_04_lambda_has_state_table_env_var(self, lambda_client, config):
        """Verify Lambda has STATE_TABLE_NAME environment variable."""
        function_name = f"{config['resource_prefix']}CircuitBreakerReset"
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            env_vars = response['Configuration'].get('Environment', {}).get(
                'Variables', {}
            )
            assert 'STATE_TABLE_NAME' in env_vars, (
                "Missing STATE_TABLE_NAME environment variable"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip("Lambda function not found - covered by existence test")
            raise


class TestCircuitBreakerResetIAMRole:
    """Layer 3-4: Verify circuit breaker reset IAM role exists and is configured."""

    def test_01_iam_role_exists(self, iam_client, config):
        """Verify the IAM role for circuit breaker reset exists."""
        role_name = f"{config['resource_prefix']}CircuitBreakerResetRole"
        try:
            response = iam_client.get_role(RoleName=role_name)
            assert response['Role']['RoleName'] == role_name
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                pytest.fail(
                    f"IAM role {role_name} not found. "
                    "Run: cd src/api/endpoints/runners && terraform apply"
                )
            raise

    def test_02_iam_role_has_lambda_trust_policy(self, iam_client, config):
        """Verify IAM role can be assumed by Lambda."""
        role_name = f"{config['resource_prefix']}CircuitBreakerResetRole"
        try:
            response = iam_client.get_role(RoleName=role_name)
            trust_policy = response['Role']['AssumeRolePolicyDocument']
            statements = trust_policy.get('Statement', [])
            lambda_trust = any(
                stmt.get('Principal', {}).get('Service') == 'lambda.amazonaws.com'
                for stmt in statements
            )
            assert lambda_trust, (
                "IAM role missing Lambda trust relationship"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                pytest.skip("IAM role not found - covered by existence test")
            raise
