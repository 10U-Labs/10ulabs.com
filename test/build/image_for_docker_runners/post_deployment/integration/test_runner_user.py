from .conftest import run_command_in_container


def test_runner_user_exists(docker_image):
    result = run_command_in_container(docker_image, "id runner")

    assert result.returncode == 0


def test_runner_user_home_directory(docker_image):
    result = run_command_in_container(docker_image, "test -d /home/runner")

    assert result.returncode == 0


def test_runner_user_has_sudo_privileges(docker_image):
    result = run_command_in_container(docker_image, "sudo -n true")

    assert result.returncode == 0
