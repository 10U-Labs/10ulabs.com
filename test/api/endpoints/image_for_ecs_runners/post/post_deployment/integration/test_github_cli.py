"""Tests for GitHub CLI installation in ECS runner image."""
from .conftest import run_command_in_container


def test_github_cli_installed(docker_image):
    """Test that GitHub CLI is installed."""
    result = run_command_in_container(docker_image, "which gh")

    assert result.returncode == 0


def test_github_cli_executable(docker_image):
    """Test that GitHub CLI is executable."""
    result = run_command_in_container(docker_image, "gh --version")

    assert result.returncode == 0


def test_github_cli_version_output(docker_image):
    """Test that GitHub CLI returns version string."""
    result = run_command_in_container(docker_image, "gh --version")

    assert "gh version" in result.stdout
