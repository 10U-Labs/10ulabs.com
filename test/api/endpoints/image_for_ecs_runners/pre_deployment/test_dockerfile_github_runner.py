"""Tests for Dockerfile GitHub runner installation."""


def test_dockerfile_installs_github_runner(dockerfile_run_commands_joined):
    """Test that Dockerfile installs GitHub actions-runner."""
    assert dockerfile_run_commands_joined.find('actions-runner') != -1


def test_dockerfile_declares_runner_version_arg(dockerfile_content):
    """Test that Dockerfile declares RUNNER_VERSION ARG."""
    assert dockerfile_content.find('ARG RUNNER_VERSION') != -1


def test_dockerfile_declares_runner_arch_arg(dockerfile_content):
    """Test that Dockerfile declares RUNNER_ARCH ARG."""
    assert dockerfile_content.find('ARG RUNNER_ARCH') != -1
