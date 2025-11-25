import pytest


def test_github_runner_user_exists(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "id github-runner")

    assert output["Status"] == "Success"


def test_github_runner_directory_exists(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "test -d /home/github-runner/actions-runner && echo exists")

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_binary_exists(ssm_client, test_instance, config, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    runner_version = config["runner_version"]
    os_arch = config["os_architecture"]
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
