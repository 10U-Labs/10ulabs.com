import pytest


def test_cloudwatch_agent_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "test -f /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent && echo exists")

    assert output["StandardOutputContent"].strip() == "exists"
