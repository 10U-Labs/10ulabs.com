import pytest


def test_cloudwatch_agent_status_check(ssm_client, e2e_test_instance, run_ssm_command):
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, e2e_test_instance, "sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status")

    assert output["Status"] == "Success"
