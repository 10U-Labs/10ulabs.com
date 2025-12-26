"""Layer 5: Configuration - Verify prerequisite resources are configured correctly."""
import pytest

pytestmark = pytest.mark.layer(5)


class TestTerraformOutputsConfiguration:
    """Layer 5: Verify terraform outputs are accessible and valid."""

    def test_ami_purpose_output_exists(self, api_shared_routing_outputs):
        """Verify ec2_runner_ami_purpose_value output is accessible."""
        assert api_shared_routing_outputs.get("ec2_runner_ami_purpose_value"), (
            "Missing ec2_runner_ami_purpose_value output from api_shared_routing. "
            "Run terraform apply in src/api/backend/"
        )

    def test_ami_stable_tag_output_exists(self, api_shared_routing_outputs):
        """Verify ec2_runner_ami_stable_tag output is accessible."""
        assert api_shared_routing_outputs.get("ec2_runner_ami_stable_tag"), (
            "Missing ec2_runner_ami_stable_tag output from api_shared_routing. "
            "Run terraform apply in src/api/backend/"
        )

    def test_ami_purpose_value_is_valid(self, ami_purpose_value):
        """Verify the AMI purpose tag value is configured."""
        assert ami_purpose_value, (
            "AMI purpose value is empty. "
            "Check ec2_runner_ami_purpose_value in api_shared_routing terraform."
        )

    def test_ami_stable_tag_is_valid(self, ami_stable_tag):
        """Verify the AMI stable tag name is configured."""
        assert ami_stable_tag, (
            "AMI stable tag is empty. "
            "Check ec2_runner_ami_stable_tag in api_shared_routing terraform."
        )
