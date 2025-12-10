"""
Integration tests for AWS CLI installation in ECS runner image.
"""
from .conftest import run_command_in_container


def test_aws_cli_installed(docker_image):
    """
    Test that AWS CLI is installed in the container.
    """
    result = run_command_in_container(docker_image, "which aws")

    assert result.returncode == 0


def test_aws_cli_version(docker_image):
    """
    Test that AWS CLI version 2 is installed in the container.
    """
    result = run_command_in_container(
        docker_image,
        "aws --version | grep -q 'aws-cli/2'"
    )

    assert result.returncode == 0
