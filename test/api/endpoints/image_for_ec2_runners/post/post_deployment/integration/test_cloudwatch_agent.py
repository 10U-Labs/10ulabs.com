"""Integration tests for CloudWatch agent on EC2 runner AMI."""
import pytest


def test_cloudwatch_agent_is_installed(ssm_client, test_instance, run_ssm_command):
    """Cloudwatch agent is installed."""

    if not test_instance:
        pytest.fail("Test instance not created")

    agent_path = "/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent"
    cmd = f"test -f {agent_path} && echo exists"
    output = run_ssm_command(ssm_client, test_instance, cmd)

    assert output["StandardOutputContent"].strip() == "exists"
