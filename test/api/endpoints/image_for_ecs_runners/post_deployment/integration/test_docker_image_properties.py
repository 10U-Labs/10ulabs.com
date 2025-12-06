"""Tests for Docker image properties in ECS runner image."""
import subprocess
from .conftest import run_command_in_container


def test_docker_image_exists(docker_image):
    """Test that Docker image exists."""
    assert docker_image


def test_image_platform_is_arm64(docker_image):
    """Test that image is built for ARM64 architecture."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.Architecture}}", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.stdout.strip() == "arm64"


def test_image_has_entrypoint(docker_image):
    """Test that image has correct entrypoint configured."""
    result = subprocess.run(
        [
            "docker", "inspect",
            "--format", "{{json .Config.Entrypoint}}",
            docker_image
        ],
        check=False,
        capture_output=True,
        text=True
    )

    expected = "/home/runner/entrypoint.py"
    start_index = result.stdout.find(expected)
    assert start_index != -1


def test_debian_base_image(docker_image):
    """Test that image is based on Debian."""
    result = run_command_in_container(
        docker_image, "cat /etc/os-release | grep -q debian"
    )

    assert result.returncode == 0


def test_container_user_is_runner(docker_image):
    """Test that container runs as runner user."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.Config.User}}", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.stdout.strip() == "runner"


def test_container_workdir_is_runner_home(docker_image):
    """Test that container working directory is /home/runner."""
    result = subprocess.run(
        [
            "docker", "inspect",
            "--format", "{{.Config.WorkingDir}}",
            docker_image
        ],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.stdout.strip() == "/home/runner"


def test_container_runs_on_arm64_platform(docker_image):
    """Test that container runs on ARM64 platform."""
    result = run_command_in_container(docker_image, "uname -m")
    assert result.stdout.strip() == "aarch64"
