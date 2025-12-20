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


def test_entrypoint_accepts_check_interval_argument(docker_image):
    """Test that entrypoint accepts --check-interval argument."""
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--check-interval'"
    )

    assert result.returncode == 0


def test_entrypoint_check_interval_has_default(docker_image):
    """Test that --check-interval shows default value in help."""
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q 'default: 30'"
    )

    assert result.returncode == 0


def test_entrypoint_imports_required_modules(docker_image):
    """Test that entrypoint can import all required modules."""
    result = run_command_in_container(
        docker_image,
        "python3 -c 'import sys; sys.path.insert(0, \"/home/runner\"); "
        "import entrypoint; "
        "exit(0)'"
    )

    assert result.returncode == 0


def test_entrypoint_has_start_run_monitor_function(docker_image):
    """Test that entrypoint has start_run_monitor function."""
    result = run_command_in_container(
        docker_image,
        "python3 -c 'import sys; sys.path.insert(0, \"/home/runner\"); "
        "import entrypoint; "
        "assert hasattr(entrypoint, \"start_run_monitor\")'"
    )

    assert result.returncode == 0


def test_entrypoint_has_stop_run_monitor_function(docker_image):
    """Test that entrypoint has stop_run_monitor function."""
    result = run_command_in_container(
        docker_image,
        "python3 -c 'import sys; sys.path.insert(0, \"/home/runner\"); "
        "import entrypoint; "
        "assert hasattr(entrypoint, \"stop_run_monitor\")'"
    )

    assert result.returncode == 0


def test_entrypoint_has_extract_run_id_from_name_function(docker_image):
    """Test that entrypoint has extract_run_id_from_name function."""
    result = run_command_in_container(
        docker_image,
        "python3 -c 'import sys; sys.path.insert(0, \"/home/runner\"); "
        "import entrypoint; "
        "assert hasattr(entrypoint, \"extract_run_id_from_name\")'"
    )

    assert result.returncode == 0


def test_entrypoint_extract_run_id_from_fargate_runner(docker_image):
    """Test extract_run_id_from_name extracts ID from fargate runner name."""
    result = run_command_in_container(
        docker_image,
        "python3 -c 'import sys; sys.path.insert(0, \"/home/runner\"); "
        "import entrypoint; "
        "assert entrypoint.extract_run_id_from_name(\"fargate-runner-12345\") == \"12345\"'"
    )

    assert result.returncode == 0


def test_entrypoint_extract_run_id_returns_none_for_ec2_runner(docker_image):
    """Test extract_run_id_from_name returns None for ec2 runner name."""
    result = run_command_in_container(
        docker_image,
        "python3 -c 'import sys; sys.path.insert(0, \"/home/runner\"); "
        "import entrypoint; "
        "assert entrypoint.extract_run_id_from_name(\"ec2-runner-12345\") is None'"
    )

    assert result.returncode == 0
