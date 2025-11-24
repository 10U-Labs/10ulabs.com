import time
import pytest


def test_ssm_session_manager_connection_works(ssm_client, e2e_test_instance):
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[e2e_test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["echo 'SSM Session Manager Test'"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=e2e_test_instance
    )

    assert output["StandardOutputContent"].strip() == "SSM Session Manager Test"
