import time
import pytest


def test_github_runner_user_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["id github-runner"]}
    )

    command_id = response["Command"]["CommandId"]

    for attempt in range(8):
        wait_time = 2 ** attempt
        time.sleep(wait_time)

        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=test_instance
        )

        if output["Status"] == "Success":
            assert output["Status"] == "Success"
            return

        if output["Status"] == "Failed":
            pytest.fail(f"SSM command failed: {output.get('StandardErrorContent', '')}")

    pytest.fail("SSM command did not complete within timeout")


def test_github_runner_directory_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -d /home/github-runner/actions-runner && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_binary_exists(ssm_client, test_instance, aws_region, tfvars):
    if not test_instance:
        pytest.fail("Test instance not created")

    runner_version = tfvars["github_runner_version"]
    os_arch = tfvars["os_architecture"]
    runner_arch = "arm64" if os_arch == "arm64" else "x64"

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [f"test -f /home/github-runner/actions-runner/actions-runner-linux-{runner_arch}-{runner_version}.tar.gz && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_config_script_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -f /home/github-runner/actions-runner/config.sh && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_run_script_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -f /home/github-runner/actions-runner/run.sh && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"
