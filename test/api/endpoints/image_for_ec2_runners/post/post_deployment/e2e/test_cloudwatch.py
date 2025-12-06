"""End-to-end tests for CloudWatch agent on EC2 runners."""
import pytest


def test_cloudwatch_agent_status_check(ssm_client, e2e_test_instance, run_ssm_command):
    """Test that CloudWatch agent is running on the EC2 instance."""
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    cmd = "sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status"
    output = run_ssm_command(ssm_client, e2e_test_instance, cmd)

    assert output["Status"] == "Success"
