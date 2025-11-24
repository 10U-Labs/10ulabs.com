from .conftest import run_command_in_container


def test_github_runner_config_script_exists(docker_image):
    result = run_command_in_container(docker_image, "test -f /home/runner/config.sh")

    assert result.returncode == 0


def test_github_runner_run_script_exists(docker_image):
    result = run_command_in_container(docker_image, "test -f /home/runner/run.sh")

    assert result.returncode == 0


def test_github_runner_files_owned_by_runner(docker_image):
    result = run_command_in_container(docker_image, "test -O /home/runner/config.sh")

    assert result.returncode == 0


def test_github_runner_version_matches_expected(docker_image):
    result = run_command_in_container(docker_image, "cat /home/runner/.runner | grep -o '\"version\":\"[^\"]*\"' | cut -d'\"' -f4")
    assert result.returncode == 0
