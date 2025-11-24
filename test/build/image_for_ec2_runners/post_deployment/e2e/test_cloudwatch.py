import time
import pytest


def test_cloudwatch_agent_status_check(ssm_client, e2e_test_instance):
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[e2e_test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=e2e_test_instance
    )

    assert output["Status"] == "Success"
    assert "status" in output["StandardOutputContent"]
