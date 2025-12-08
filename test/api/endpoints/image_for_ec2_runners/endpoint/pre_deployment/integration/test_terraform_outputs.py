"""Pre-deployment integration tests for terraform outputs."""


def test_terraform_outputs_readable(api_backend_outputs):
    """Verify api_backend terraform outputs are accessible."""
    assert api_backend_outputs.get("ec2_runner_ami_purpose_value"), (
        "Missing ec2_runner_ami_purpose_value output"
    )
    assert api_backend_outputs.get("ec2_runner_ami_stable_tag"), (
        "Missing ec2_runner_ami_stable_tag output"
    )


def test_ami_purpose_value_is_valid(ami_purpose_value):
    """Verify the AMI purpose tag value is configured."""
    assert ami_purpose_value, "AMI purpose value is not configured"


def test_ami_stable_tag_is_valid(ami_stable_tag):
    """Verify the AMI stable tag name is configured."""
    assert ami_stable_tag, "AMI stable tag is not configured"
