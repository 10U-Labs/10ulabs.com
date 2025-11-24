import time
import pytest


def test_cloudwatch_agent_is_installed(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -f /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"
