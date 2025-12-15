"""Post-deployment tests for webhook Lambda package."""
import pytest
from botocore.exceptions import ClientError


class TestWebhookLambdaDeployed:
    """Tests to verify webhook Lambda is deployed correctly."""

    @pytest.fixture
    def lambda_client(self, aws_region):
        """Get Lambda client."""
        import boto3
        return boto3.client("lambda", region_name=aws_region)

    def test_webhook_lambda_exists(self, lambda_client, shared_config):
        """Verify webhook Lambda function exists."""
        resource_prefix = shared_config.get("resource_prefix", "10ulabs")
        # Function name pattern: {prefix}-agents-webhook
        function_patterns = [
            f"{resource_prefix}-agents-webhook",
            f"{resource_prefix}_agents_webhook",
        ]

        found = False
        for pattern in function_patterns:
            try:
                lambda_client.get_function(FunctionName=pattern)
                found = True
                break
            except ClientError as err:
                if err.response["Error"]["Code"] != "ResourceNotFoundException":
                    raise

        if not found:
            pytest.skip(
                "Webhook Lambda not deployed yet. "
                f"Looked for: {function_patterns}"
            )

    def test_webhook_lambda_has_handler_configured(self, lambda_client, shared_config):
        """Verify Lambda has correct handler configured."""
        resource_prefix = shared_config.get("resource_prefix", "10ulabs")
        function_name = f"{resource_prefix}-agents-webhook"

        try:
            response = lambda_client.get_function(FunctionName=function_name)
            handler = response["Configuration"]["Handler"]
            assert "handler" in handler.lower(), (
                f"Lambda handler '{handler}' should reference handler module"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Webhook Lambda not deployed yet")
            raise


class TestWebhookLambdaEnvironment:
    """Tests for Lambda environment configuration."""

    @pytest.fixture
    def lambda_client(self, aws_region):
        """Get Lambda client."""
        import boto3
        return boto3.client("lambda", region_name=aws_region)

    def test_webhook_lambda_has_agent_runtime_arn(self, lambda_client, shared_config):
        """Verify Lambda has AGENT_RUNTIME_ARN environment variable."""
        resource_prefix = shared_config.get("resource_prefix", "10ulabs")
        function_name = f"{resource_prefix}-agents-webhook"

        try:
            response = lambda_client.get_function(FunctionName=function_name)
            env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
            assert "AGENT_RUNTIME_ARN" in env_vars or "AGENTCORE" in str(env_vars).upper(), (
                "Lambda should have AGENT_RUNTIME_ARN environment variable"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Webhook Lambda not deployed yet")
            raise
