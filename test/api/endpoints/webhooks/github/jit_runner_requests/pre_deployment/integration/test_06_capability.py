"""Layer 6: Capability - Can we perform required operations?

These tests verify that we have the capability to perform operations required
for deployment on prerequisite resources.

Six-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Does Terraform state match AWS reality?
- Layer 4: Existence - Do the required resources exist?
- Layer 5: Configuration - Are resources configured correctly?
- Layer 6: Capability - Can we perform required operations? (THIS FILE)

Note: The api_endpoint_v1_runners deployment relies on prerequisites from other
workflows (api_common_networking, api_common_docker_repository, ec2_runner, ecs_runner).
Capability tests here verify we can perform operations on those prerequisites.
"""
import pytest

from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(6)


def _verify_lambda_configuration(lambda_client, outputs, output_key):
    """Verify we can read a Lambda function configuration from outputs.

    Returns None if skipped, raises on unexpected error.
    """
    function_name = outputs.get(output_key)
    if not function_name:
        pytest.skip(f"{output_key} output not available")
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        assert response.get("FunctionName") == function_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.skip("Function not found - covered by existence test")
        raise


# === SSM Capability ===


def test_can_decrypt_github_pat_parameter(ssm_client, ssm_github_pat_name):
    """Verify we can decrypt the GitHub PAT SSM parameter.

    This tests KMS key access permissions for the GitHub Actions role.
    Skips if parameter doesn't exist (covered by Layer 4 existence tests).
    """
    response = ssm_client.get_parameter(Name=ssm_github_pat_name, WithDecryption=True)
    assert response.get("Parameter") is not None, (
        f"SSM parameter '{ssm_github_pat_name}' returned empty response"
    )


class TestLambdaCapability:
    """Layer 6: Verify capability to invoke runner Lambda functions."""

    def test_can_get_ec2_runner_lambda_configuration(
        self, lambda_client, ec2_runner_outputs
    ):
        """Verify we can read the EC2 runner Lambda configuration."""
        _verify_lambda_configuration(lambda_client, ec2_runner_outputs, "lambda_function_name")

    def test_can_get_ecs_runner_lambda_configuration(
        self, lambda_client, ecs_runner_outputs
    ):
        """Verify we can read the ECS runner Lambda configuration."""
        _verify_lambda_configuration(lambda_client, ecs_runner_outputs, "lambda_function_name")
