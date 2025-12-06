"""Tests for Dockerfile Terraform installation."""


def test_dockerfile_installs_terraform(dockerfile_run_commands_joined):
    """Test that Dockerfile installs Terraform."""
    assert dockerfile_run_commands_joined.find('terraform') != -1


def test_dockerfile_declares_terraform_version_arg(dockerfile_content):
    """Test that Dockerfile declares TERRAFORM_VERSION ARG."""
    assert dockerfile_content.find('ARG TERRAFORM_VERSION') != -1


def test_dockerfile_installs_tflint(dockerfile_run_commands_joined):
    """Test that Dockerfile installs tflint."""
    assert dockerfile_run_commands_joined.find('tflint') != -1
