import time
import pytest


def test_ssm_agent_is_installed(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["which amazon-ssm-agent"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["Status"] == "Success"


def test_ssm_agent_service_is_running(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["systemctl is-active amazon-ssm-agent"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "active"
