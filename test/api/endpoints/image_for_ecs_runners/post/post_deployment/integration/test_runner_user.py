"""
Integration tests for runner user configuration in ECS runner image.
"""
from .conftest import run_command_in_container


def test_runner_user_exists(docker_image):
    """
    Test that the runner user exists in the container.
    """
    result = run_command_in_container(docker_image, "id runner")

    assert result.returncode == 0


def test_runner_user_home_directory(docker_image):
    """
    Test that the runner user has a home directory.
    """
    result = run_command_in_container(
        docker_image,
        "test -d /home/runner"
    )

    assert result.returncode == 0


def test_runner_user_has_sudo_privileges(docker_image):
    """
    Test that the runner user has passwordless sudo privileges.
    """
    result = run_command_in_container(docker_image, "sudo -n true")

    assert result.returncode == 0
