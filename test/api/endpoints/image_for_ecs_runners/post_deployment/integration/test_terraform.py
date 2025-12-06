"""Tests for Terraform installation in ECS runner image."""
from .conftest import run_command_in_container


def test_terraform_installed(docker_image):
    """Test that Terraform is installed."""
    result = run_command_in_container(docker_image, "which terraform")

    assert result.returncode == 0


def test_terraform_version_matches(docker_image, config_terraform_version):
    """Test that Terraform version matches configuration."""
    result = run_command_in_container(
        docker_image,
        f"terraform version | grep -q 'v{config_terraform_version}'"
    )

    assert result.returncode == 0


def test_tflint_installed(docker_image):
    """Test that tflint is installed."""
    result = run_command_in_container(docker_image, "which tflint")

    assert result.returncode == 0
