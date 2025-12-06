"""Integration tests for Docker installation on EC2 runner AMI."""
import pytest


def test_docker_is_installed(ssm_client, test_instance, run_ssm_command):
    """Test that Docker is installed on the instance."""
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which docker")

    assert output["Status"] == "Success"


def test_docker_daemon_is_running(ssm_client, test_instance, run_ssm_command):
    """Test that the Docker daemon is running."""
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "systemctl is-active docker")

    assert output["StandardOutputContent"].strip() == "active"


def test_github_runner_user_in_docker_group(ssm_client, test_instance, run_ssm_command):
    """Test that the github-runner user is in the docker group."""
    if not test_instance:
        pytest.fail("Test instance not created")

    cmd = "groups github-runner | grep -q docker && echo in_group"
    output = run_ssm_command(ssm_client, test_instance, cmd)

    assert output["StandardOutputContent"].strip() == "in_group"
