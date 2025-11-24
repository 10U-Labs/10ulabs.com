import time
import pytest


def test_docker_can_run_containers_as_github_runner(ssm_client, e2e_test_instance):
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[e2e_test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["sudo -u github-runner docker run --rm hello-world"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(10)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=e2e_test_instance
    )

    assert output["Status"] == "Success"
