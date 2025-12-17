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


def test_cloudwatch_agent_config_exists(ssm_client, test_instance, run_ssm_command):
    """CloudWatch agent config file exists."""
    if not test_instance:
        pytest.fail("Test instance not created")

    config_path = "/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json"
    cmd = f"test -f {config_path} && echo exists"
    output = run_ssm_command(ssm_client, test_instance, cmd)

    assert output["StandardOutputContent"].strip() == "exists"


def test_cloudwatch_agent_config_has_metrics_namespace(
    ssm_client, test_instance, run_ssm_command
):
    """CloudWatch agent config has correct metrics namespace."""
    if not test_instance:
        pytest.fail("Test instance not created")

    config_path = "/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json"
    cmd = f"cat {config_path} | jq -r '.metrics.namespace'"
    output = run_ssm_command(ssm_client, test_instance, cmd)

    assert output["StandardOutputContent"].strip() == "GitHubRunner/EC2"
