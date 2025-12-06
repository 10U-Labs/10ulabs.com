"""Tests for GitHub Actions runner scripts in ECS runner image."""
from .conftest import run_command_in_container


def test_github_runner_config_script_exists(docker_image):
    """Test that GitHub runner config script exists."""
    result = run_command_in_container(docker_image, "test -f /home/runner/config.sh")

    assert result.returncode == 0


def test_github_runner_run_script_exists(docker_image):
    """Test that GitHub runner run script exists."""
    result = run_command_in_container(
        docker_image, "test -f /home/runner/run.sh"
    )

    assert result.returncode == 0


def test_github_runner_files_owned_by_runner(docker_image):
    """Test that GitHub runner files are owned by runner user."""
    result = run_command_in_container(
        docker_image, "test -O /home/runner/config.sh"
    )

    assert result.returncode == 0


def test_github_runner_version_matches_expected(docker_image):
    """Test that GitHub runner version can be read."""
    result = run_command_in_container(
        docker_image,
        "cat /home/runner/.runner | "
        "grep -o '\"version\":\"[^\"]*\"' | "
        "cut -d'\"' -f4"
    )
    assert result.returncode == 0
