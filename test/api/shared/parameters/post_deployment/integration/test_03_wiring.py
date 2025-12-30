"""Layer 3: Wiring tests for api/shared/parameters post-deployment.

Tests that components are connected properly. Assumes existence and configuration passed.

Three-layer testing model:
- Layer 3: Wiring - Components connected properly

Note: For the parameters module, there is minimal wiring to test since it only
creates an SSM parameter. The wiring tests verify that the parameter can be
read by other components that depend on it.
"""

import pytest


pytestmark = pytest.mark.layer(3)


class TestSSMParameterWiring:
    """Layer 3: Verify SSM parameter is accessible for wiring."""

    def test_ssm_parameter_is_readable(self, ssm_client, ssm_parameter_name):
        """Verify the SSM parameter can be read (basic wiring check)."""
        if not ssm_parameter_name:
            pytest.skip("SSM parameter name not available from outputs")
        # Simply reading the parameter verifies it can be accessed
        # by downstream consumers (ec2 runner Lambda, etc.)
        response = ssm_client.get_parameter(Name=ssm_parameter_name)
        assert response["Parameter"]["Name"] == ssm_parameter_name, (
            "SSM parameter read returned unexpected name"
        )

    def test_ssm_parameter_arn_matches_name(
        self, parameters_outputs, ssm_parameter_name
    ):
        """Verify the ARN output matches the parameter name."""
        if not ssm_parameter_name:
            pytest.skip("SSM parameter name not available from outputs")
        arn = parameters_outputs.get("ssm_ec2_runner_ami_latest_arn", "")
        if not arn:
            pytest.skip("SSM parameter ARN not available from outputs")
        # The ARN should end with the parameter name
        expected_suffix = f":parameter{ssm_parameter_name}"
        assert arn.endswith(expected_suffix), (
            f"SSM parameter ARN '{arn}' should end with '{expected_suffix}'"
        )
