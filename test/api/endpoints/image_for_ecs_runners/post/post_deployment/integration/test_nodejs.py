"""Tests for Node.js installation in ECS runner image."""
from .conftest import run_command_in_container


def test_nodejs_installed(docker_image):
    """Test that Node.js is installed."""
    result = run_command_in_container(docker_image, "which node")

    assert result.returncode == 0


def test_nodejs_version_matches(docker_image, config_node_version):
    """Test that Node.js version matches configuration."""
    result = run_command_in_container(
        docker_image,
        f"node --version | grep -q 'v{config_node_version}'"
    )

    assert result.returncode == 0


def test_npm_installed(docker_image):
    """Test that npm is installed."""
    result = run_command_in_container(docker_image, "which npm")

    assert result.returncode == 0


def test_eslint_installed_globally(docker_image):
    """Test that eslint is installed globally."""
    result = run_command_in_container(docker_image, "which eslint")

    assert result.returncode == 0


def test_jsonlint_installed_globally(docker_image):
    """Test that jsonlint is installed globally."""
    result = run_command_in_container(docker_image, "which jsonlint")

    assert result.returncode == 0
