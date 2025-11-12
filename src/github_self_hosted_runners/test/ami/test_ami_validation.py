"""AMI validation tests using AWS SSM (no foreign dependencies)

These tests validate that the AMI has all required components installed
and properly configured using AWS Systems Manager.

100% US-controlled code. No foreign-maintained dependencies.
"""
import time

import boto3
import pytest


@pytest.fixture
def ssm_client(region):
    """Create SSM client for running commands"""
    return boto3.client("ssm", region_name=region)


def run_ssm_command(ssm_client, instance_id, command, timeout=30):
    """Run command via SSM and return result.

    Args:
        ssm_client: boto3 SSM client
        instance_id: EC2 instance ID
        command: Shell command to execute
        timeout: Max seconds to wait (default: 30)

    Returns:
        dict: {
            'exit_code': int,
            'stdout': str,
            'stderr': str,
            'succeeded': bool
        }
    """
    # Send command
    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [command]},
        TimeoutSeconds=timeout,
    )

    command_id = response["Command"]["CommandId"]

    # Wait for completion
    max_attempts = timeout
    for _ in range(max_attempts):
        try:
            invocation = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )

            status = invocation["Status"]

            if status in ("Success", "Failed", "Cancelled", "TimedOut"):
                return {
                    "exit_code": invocation.get("ResponseCode", -1),
                    "stdout": invocation.get("StandardOutputContent", ""),
                    "stderr": invocation.get("StandardErrorContent", ""),
                    "succeeded": status == "Success"
                }
        except ssm_client.exceptions.InvocationDoesNotExist:
            # Command still initializing
            pass

        time.sleep(1)

    raise TimeoutError(f"Command timed out after {timeout} seconds: {command}")


def test_docker_installed(ssm_client, instance_id):
    """Docker should be installed"""
    result = run_ssm_command(ssm_client, instance_id, "dpkg -l docker-ce")
    assert result["succeeded"], f"Command failed: {result['stderr']}"
    assert "docker-ce" in result["stdout"]


def test_docker_service_enabled(ssm_client, instance_id):
    """Docker service should be enabled"""
    result = run_ssm_command(ssm_client, instance_id, "systemctl is-enabled docker")
    assert result["succeeded"], f"Docker not enabled: {result['stderr']}"
    assert "enabled" in result["stdout"]


def test_github_runner_user_exists(ssm_client, instance_id):
    """github-runner user should exist"""
    result = run_ssm_command(ssm_client, instance_id, "id -u github-runner")
    assert result["succeeded"], "github-runner user doesn't exist"


def test_github_runner_home_directory(ssm_client, instance_id):
    """github-runner user should have correct home directory"""
    result = run_ssm_command(ssm_client, instance_id, "getent passwd github-runner")
    assert result["succeeded"]
    assert "/home/github-runner" in result["stdout"]


def test_github_runner_in_docker_group(ssm_client, instance_id):
    """github-runner user should be in docker group"""
    result = run_ssm_command(ssm_client, instance_id, "groups github-runner")
    assert result["succeeded"]
    assert "docker" in result["stdout"]


def test_github_runner_directory_exists(ssm_client, instance_id):
    """GitHub runner directory should exist with correct ownership"""
    result = run_ssm_command(ssm_client, instance_id, "stat -c '%U:%G %a' /home/github-runner/actions-runner")
    assert result["succeeded"], "actions-runner directory doesn't exist"
    assert "github-runner:github-runner" in result["stdout"]


def test_github_runner_binaries_exist(ssm_client, instance_id):
    """GitHub runner binaries should be installed"""
    commands = [
        "test -f /home/github-runner/actions-runner/run.sh",
        "test -f /home/github-runner/actions-runner/config.sh"
    ]
    for cmd in commands:
        result = run_ssm_command(ssm_client, instance_id, cmd)
        assert result["succeeded"], f"Binary missing: {cmd}"


def test_cloudwatch_agent_installed(ssm_client, instance_id):
    """CloudWatch agent should be installed"""
    result = run_ssm_command(ssm_client, instance_id, "dpkg -l amazon-cloudwatch-agent")
    assert result["succeeded"], "CloudWatch agent not installed"
    assert "amazon-cloudwatch-agent" in result["stdout"]


def test_ssm_agent_installed(ssm_client, instance_id):
    """SSM agent should be installed"""
    result = run_ssm_command(ssm_client, instance_id, "dpkg -l amazon-ssm-agent")
    assert result["succeeded"], "SSM agent not installed"
    assert "amazon-ssm-agent" in result["stdout"]


def test_ssm_agent_enabled(ssm_client, instance_id):
    """SSM agent service should be enabled"""
    result = run_ssm_command(ssm_client, instance_id, "systemctl is-enabled amazon-ssm-agent")
    assert result["succeeded"], "SSM agent not enabled"
    assert "enabled" in result["stdout"]


def test_required_packages_installed(ssm_client, instance_id):
    """Required system packages should be installed"""
    packages = ["curl", "git", "jq"]
    for package in packages:
        result = run_ssm_command(ssm_client, instance_id, f"dpkg -l {package}")
        assert result["succeeded"], f"Package {package} not installed"
        assert package in result["stdout"]


def test_docker_command_available(ssm_client, instance_id):
    """Docker command should be available"""
    result = run_ssm_command(ssm_client, instance_id, "which docker")
    assert result["succeeded"], "docker command not found"
    assert "/usr/bin/docker" in result["stdout"]


def test_systemd_available(ssm_client, instance_id):
    """Systemd should be available"""
    result = run_ssm_command(ssm_client, instance_id, "test -d /run/systemd/system")
    assert result["succeeded"], "Systemd not available"
