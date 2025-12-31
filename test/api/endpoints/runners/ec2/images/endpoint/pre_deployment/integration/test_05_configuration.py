"""Layer 5: Configuration - Verify prerequisite resources are configured correctly."""
import pytest

pytestmark = pytest.mark.layer(5)


class TestRunnersConfiguration:
    """Layer 5: Verify runners.json configuration values are valid."""

    def test_ami_purpose_value_is_valid(self, ami_purpose_value):
        """Verify the AMI purpose tag value is configured in runners.json."""
        assert ami_purpose_value, (
            "AMI purpose value is empty. "
            "Check tags.ec2.ami.purpose_value in etc/runners.json"
        )

    def test_ami_stable_tag_is_valid(self, ami_stable_tag):
        """Verify the AMI stable tag name is configured in runners.json."""
        assert ami_stable_tag, (
            "AMI stable tag is empty. "
            "Check tags.ec2.ami.stable_tag in etc/runners.json"
        )
