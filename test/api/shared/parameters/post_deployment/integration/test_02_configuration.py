"""Layer 2: Configuration tests for api/shared/parameters post-deployment.

Tests that resources are configured correctly. Assumes existence tests passed.

Three-layer testing model:
- Layer 2: Configuration - Resources configured correctly
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(2)


class TestSSMParameterConfiguration:
    """Layer 2: Verify SSM parameter configuration."""

    def test_ssm_parameter_type_is_string(self, ssm_client, ssm_parameter_name):
        """Verify the SSM parameter type is String."""
        if not ssm_parameter_name:
            pytest.skip("SSM parameter name not available from outputs")
        try:
            response = ssm_client.get_parameter(Name=ssm_parameter_name)
            assert response["Parameter"]["Type"] == "String", (
                f"SSM parameter '{ssm_parameter_name}' should be type 'String', "
                f"got '{response['Parameter']['Type']}'"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                pytest.skip("SSM parameter not found")
            raise

    def test_ssm_parameter_name_follows_convention(self, ssm_parameter_name):
        """Verify the SSM parameter name follows naming convention."""
        if not ssm_parameter_name:
            pytest.skip("SSM parameter name not available from outputs")
        assert ssm_parameter_name.startswith("/ami/"), (
            f"SSM parameter name '{ssm_parameter_name}' should start with '/ami/'"
        )

    def test_ssm_parameter_has_value(self, ssm_client, ssm_parameter_name):
        """Verify the SSM parameter has a value (not empty)."""
        if not ssm_parameter_name:
            pytest.skip("SSM parameter name not available from outputs")
        try:
            response = ssm_client.get_parameter(Name=ssm_parameter_name)
            value = response["Parameter"]["Value"]
            assert value, (
                f"SSM parameter '{ssm_parameter_name}' has empty value"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                pytest.skip("SSM parameter not found")
            raise

    def test_ssm_parameter_arn_starts_with_ssm_prefix(self, parameters_outputs):
        """Verify the SSM parameter ARN starts with 'arn:aws:ssm:'."""
        arn = parameters_outputs.get("ssm_ec2_runner_ami_latest_arn", "")
        if not arn:
            pytest.skip("SSM parameter ARN not available from outputs")
        assert arn.startswith("arn:aws:ssm:"), (
            f"SSM parameter ARN '{arn}' should start with 'arn:aws:ssm:'"
        )

    def test_ssm_parameter_arn_contains_parameter_path(self, parameters_outputs):
        """Verify the SSM parameter ARN contains ':parameter/'."""
        arn = parameters_outputs.get("ssm_ec2_runner_ami_latest_arn", "")
        if not arn:
            pytest.skip("SSM parameter ARN not available from outputs")
        assert ":parameter/" in arn, (
            f"SSM parameter ARN '{arn}' should contain ':parameter/'"
        )
