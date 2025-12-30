"""Layer 1: Existence tests for api/shared/parameters post-deployment.

Tests ONLY that resources exist. No configuration checks.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(1)


class TestSSMParameterExists:
    """Layer 1: Verify SSM parameter exists."""

    def test_ssm_parameter_name_output_exists(self, parameters_outputs):
        """Verify ssm_ec2_runner_ami_latest_name output is available."""
        name = parameters_outputs.get("ssm_ec2_runner_ami_latest_name", "")
        assert name, (
            "ssm_ec2_runner_ami_latest_name output not found. "
            "Run terraform apply in src/api/shared/parameters/"
        )

    def test_ssm_parameter_exists_in_aws(self, ssm_client, ssm_parameter_name):
        """Verify the SSM parameter exists in AWS."""
        if not ssm_parameter_name:
            pytest.skip("SSM parameter name not available from outputs")
        try:
            response = ssm_client.get_parameter(Name=ssm_parameter_name)
            assert response["Parameter"]["Name"] == ssm_parameter_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{ssm_parameter_name}' does not exist. "
                    "Run terraform apply in src/api/shared/parameters/"
                )
            raise

    def test_ssm_parameter_arn_output_exists(self, parameters_outputs):
        """Verify ssm_ec2_runner_ami_latest_arn output is available."""
        arn = parameters_outputs.get("ssm_ec2_runner_ami_latest_arn", "")
        assert arn, (
            "ssm_ec2_runner_ami_latest_arn output not found. "
            "Run terraform apply in src/api/shared/parameters/"
        )
