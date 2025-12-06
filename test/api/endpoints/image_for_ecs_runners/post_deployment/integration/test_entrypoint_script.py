"""Tests for entrypoint script in ECS runner image."""
from .conftest import run_command_in_container


def test_entrypoint_script_exists(docker_image):
    """Test that entrypoint script exists."""
    result = run_command_in_container(docker_image, "test -f /home/runner/entrypoint.py")

    assert result.returncode == 0


def test_entrypoint_script_executable(docker_image):
    """Test that entrypoint script is executable."""
    result = run_command_in_container(
        docker_image, "test -x /home/runner/entrypoint.py"
    )

    assert result.returncode == 0


def test_entrypoint_script_owned_by_runner(docker_image):
    """Test that entrypoint script is owned by runner user."""
    result = run_command_in_container(
        docker_image, "test -O /home/runner/entrypoint.py"
    )

    assert result.returncode == 0


def test_entrypoint_shebang_is_python3(docker_image):
    """Test that entrypoint script has python3 shebang."""
    result = run_command_in_container(
        docker_image,
        "head -1 /home/runner/entrypoint.py | grep -q 'python3'"
    )

    assert result.returncode == 0


def test_entrypoint_accepts_repo_argument(docker_image):
    """Test that entrypoint accepts --repo argument."""
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--repo'"
    )

    assert result.returncode == 0


def test_entrypoint_accepts_name_argument(docker_image):
    """Test that entrypoint accepts --name argument."""
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--name'"
    )

    assert result.returncode == 0


def test_entrypoint_accepts_labels_argument(docker_image):
    """Test that entrypoint accepts --labels argument."""
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--labels'"
    )

    assert result.returncode == 0


def test_entrypoint_accepts_token_argument(docker_image):
    """Test that entrypoint accepts --token argument."""
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--token'"
    )

    assert result.returncode == 0
