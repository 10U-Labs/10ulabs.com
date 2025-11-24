from .conftest import run_command_in_container


def test_entrypoint_script_exists(docker_image):
    result = run_command_in_container(docker_image, "test -f /home/runner/entrypoint.py")

    assert result.returncode == 0


def test_entrypoint_script_executable(docker_image):
    result = run_command_in_container(docker_image, "test -x /home/runner/entrypoint.py")

    assert result.returncode == 0


def test_entrypoint_script_owned_by_runner(docker_image):
    result = run_command_in_container(docker_image, "test -O /home/runner/entrypoint.py")

    assert result.returncode == 0


def test_entrypoint_shebang_is_python3(docker_image):
    result = run_command_in_container(docker_image, "head -1 /home/runner/entrypoint.py | grep -q 'python3'")

    assert result.returncode == 0


def test_entrypoint_accepts_repo_argument(docker_image):
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--repo'"
    )

    assert result.returncode == 0


def test_entrypoint_accepts_name_argument(docker_image):
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--name'"
    )

    assert result.returncode == 0


def test_entrypoint_accepts_labels_argument(docker_image):
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--labels'"
    )

    assert result.returncode == 0


def test_entrypoint_accepts_token_argument(docker_image):
    result = run_command_in_container(
        docker_image,
        "/home/runner/entrypoint.py --help | grep -q '\\--token'"
    )

    assert result.returncode == 0
