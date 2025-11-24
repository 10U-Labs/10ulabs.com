import time
import pytest


def test_github_runner_user_exists(ssm_client, test_instance):
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


def test_github_runner_directory_exists(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "test -d /home/github-runner/actions-runner && echo exists")

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_binary_exists(ssm_client, test_instance, tfvars_data, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    runner_version = tfvars_data["github_runner_version"]
    os_arch = tfvars_data["os_architecture"]
    runner_arch = "arm64" if os_arch == "arm64" else "x64"

    output = run_ssm_command(ssm_client, test_instance, f"test -f /home/github-runner/actions-runner/actions-runner-linux-{runner_arch}-{runner_version}.tar.gz && echo exists")

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_config_script_exists(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "test -f /home/github-runner/actions-runner/config.sh && echo exists")

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_run_script_exists(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "test -f /home/github-runner/actions-runner/run.sh && echo exists")

    assert output["StandardOutputContent"].strip() == "exists"
