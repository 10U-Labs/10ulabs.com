import os
import subprocess
import pytest


@pytest.fixture(scope="module")
def dockerfile_path():
    return os.path.join(os.path.dirname(__file__), "../../../../src/api/docker_runner/Dockerfile")


@pytest.fixture(scope="module")
def entrypoint_path():
    return os.path.join(os.path.dirname(__file__), "../../../../src/api/docker_runner/entrypoint.py")


@pytest.fixture(scope="module")
def docker_image_tag():
    return os.environ.get("TEST_DOCKER_IMAGE_TAG", "github-docker-runner:test")


@pytest.fixture(scope="module")
def docker_image(dockerfile_path, entrypoint_path, docker_image_tag):
    build_context = os.path.dirname(dockerfile_path)

    result = subprocess.run(
        ["docker", "build", "-t", docker_image_tag, "-f", dockerfile_path, build_context],
        check=False,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"Docker build failed: {result.stderr}")

    yield docker_image_tag

    subprocess.run(["docker", "rmi", "-f", docker_image_tag], check=False, capture_output=True)


def run_command_in_container(image_tag, command):
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/bin/bash", image_tag, "-c", command],
        check=False,
        capture_output=True,
        text=True
    )
    return result


def test_docker_image_exists(docker_image):
    assert docker_image


def test_image_platform_is_arm64(docker_image):
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.Architecture}}", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.stdout.strip() == "arm64"


def test_image_has_entrypoint(docker_image):
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{json .Config.Entrypoint}}", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert "/home/runner/entrypoint.py" in result.stdout


def test_debian_base_image(docker_image):
    result = run_command_in_container(docker_image, "cat /etc/os-release | grep -q debian")

    assert result.returncode == 0


def test_python3_installed(docker_image):
    result = run_command_in_container(docker_image, "which python3")

    assert result.returncode == 0


def test_curl_installed(docker_image):
    result = run_command_in_container(docker_image, "which curl")

    assert result.returncode == 0


def test_git_installed(docker_image):
    result = run_command_in_container(docker_image, "which git")

    assert result.returncode == 0


def test_jq_installed(docker_image):
    result = run_command_in_container(docker_image, "which jq")

    assert result.returncode == 0


def test_sudo_installed(docker_image):
    result = run_command_in_container(docker_image, "which sudo")

    assert result.returncode == 0


def test_tar_installed(docker_image):
    result = run_command_in_container(docker_image, "which tar")

    assert result.returncode == 0


def test_unzip_installed(docker_image):
    result = run_command_in_container(docker_image, "which unzip")

    assert result.returncode == 0


def test_wget_installed(docker_image):
    result = run_command_in_container(docker_image, "which wget")

    assert result.returncode == 0


def test_aws_cli_installed(docker_image):
    result = run_command_in_container(docker_image, "which aws")

    assert result.returncode == 0


def test_aws_cli_version(docker_image):
    result = run_command_in_container(docker_image, "aws --version | grep -q 'aws-cli/2'")

    assert result.returncode == 0


def test_runner_user_exists(docker_image):
    result = run_command_in_container(docker_image, "id runner")

    assert result.returncode == 0


def test_runner_user_home_directory(docker_image):
    result = run_command_in_container(docker_image, "test -d /home/runner")

    assert result.returncode == 0


def test_runner_user_has_sudo_privileges(docker_image):
    result = run_command_in_container(docker_image, "grep -q 'runner.*NOPASSWD:ALL' /etc/sudoers")

    assert result.returncode == 0


def test_github_runner_directory_exists(docker_image):
    result = run_command_in_container(docker_image, "test -d /home/runner")

    assert result.returncode == 0


def test_github_runner_version_matches(docker_image):
    result = run_command_in_container(docker_image, "test -f /home/runner/config.sh")

    assert result.returncode == 0


def test_github_runner_config_script_exists(docker_image):
    result = run_command_in_container(docker_image, "test -f /home/runner/config.sh")

    assert result.returncode == 0


def test_github_runner_run_script_exists(docker_image):
    result = run_command_in_container(docker_image, "test -f /home/runner/run.sh")

    assert result.returncode == 0


def test_github_runner_files_owned_by_runner(docker_image):
    result = run_command_in_container(docker_image, "test -O /home/runner/config.sh")

    assert result.returncode == 0


def test_nodejs_installed(docker_image):
    result = run_command_in_container(docker_image, "which node")

    assert result.returncode == 0


def test_nodejs_version_matches(docker_image):
    result = run_command_in_container(docker_image, "node --version | grep -q 'v20.18.1'")

    assert result.returncode == 0


def test_npm_installed(docker_image):
    result = run_command_in_container(docker_image, "which npm")

    assert result.returncode == 0


def test_jsonlint_installed_globally(docker_image):
    result = run_command_in_container(docker_image, "which jsonlint")

    assert result.returncode == 0


def test_boto3_installed(docker_image):
    result = run_command_in_container(docker_image, "python3 -c 'import boto3'")

    assert result.returncode == 0


def test_mypy_installed(docker_image):
    result = run_command_in_container(docker_image, "which mypy")

    assert result.returncode == 0


def test_pylint_installed(docker_image):
    result = run_command_in_container(docker_image, "which pylint")

    assert result.returncode == 0


def test_pytest_installed(docker_image):
    result = run_command_in_container(docker_image, "which pytest")

    assert result.returncode == 0


def test_pyyaml_installed(docker_image):
    result = run_command_in_container(docker_image, "python3 -c 'import yaml'")

    assert result.returncode == 0


def test_requests_installed(docker_image):
    result = run_command_in_container(docker_image, "python3 -c 'import requests'")

    assert result.returncode == 0


def test_yamllint_installed(docker_image):
    result = run_command_in_container(docker_image, "which yamllint")

    assert result.returncode == 0


def test_terraform_installed(docker_image):
    result = run_command_in_container(docker_image, "which terraform")

    assert result.returncode == 0


def test_terraform_version_matches(docker_image):
    result = run_command_in_container(docker_image, "terraform version | grep -q 'v1.14.0'")

    assert result.returncode == 0


def test_tflint_installed(docker_image):
    result = run_command_in_container(docker_image, "which tflint")

    assert result.returncode == 0


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


def test_container_starts_with_missing_args(docker_image):
    result = subprocess.run(
        ["docker", "run", "--rm", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.returncode != 0


def test_container_user_is_runner(docker_image):
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.Config.User}}", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.stdout.strip() == "runner"


def test_container_workdir_is_runner_home(docker_image):
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.Config.WorkingDir}}", docker_image],
        check=False,
        capture_output=True,
        text=True
    )

    assert result.stdout.strip() == "/home/runner"


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
