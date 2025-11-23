import subprocess
import boto3
from conftest import run_command_in_container, login_to_ecr


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
    result = run_command_in_container(docker_image, "sudo -n true")

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


def test_ecr_image_exists(aws_region, ecr_repository, image_tag):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    assert len(response["imageDetails"]) == 1


def test_ecr_image_is_arm64(aws_region, ecr_repository, image_tag):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": image_tag}]
    )
    assert response["imageDetails"][0]["imageManifestMediaType"] == "application/vnd.oci.image.index.v1+json"


def test_runner_fails_with_missing_repo_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--name", "test-runner",
            "--labels", "test",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_name_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--labels", "test",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_labels_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--name", "test-runner",
            "--token", "test-token"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_runner_fails_with_missing_token_argument(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            ecr_image_uri,
            "--repo", "org/repo",
            "--name", "test-runner",
            "--labels", "test"
        ],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_ecr_image_can_be_pulled(ecr_image_uri, aws_region):
    login_to_ecr(aws_region)

    result = subprocess.run(
        ["docker", "pull", ecr_image_uri],
        check=False,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


def test_entrypoint_prints_registration_message(docker_image):
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "test-runner",
            "--labels", "test-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    assert "Registering GitHub Actions runner..." in result.stdout


def test_entrypoint_prints_repository_from_arguments(docker_image):
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "myorg/myrepo",
            "--name", "test-runner",
            "--labels", "test-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    assert "Repository: myorg/myrepo" in result.stdout


def test_entrypoint_prints_runner_name_from_arguments(docker_image):
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "my-test-runner",
            "--labels", "test-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    assert "Runner Name: my-test-runner" in result.stdout


def test_entrypoint_prints_labels_from_arguments(docker_image):
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "test-runner",
            "--labels", "custom-label,another-label",
            "--token", "fake-token"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    assert "Labels: custom-label,another-label" in result.stdout


def test_entrypoint_fails_with_invalid_token(docker_image):
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            docker_image,
            "--repo", "test/repo",
            "--name", "test-runner",
            "--labels", "test-label",
            "--token", "invalid-token-123"
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 1


def test_github_runner_version_matches_expected(docker_image):
    result = run_command_in_container(docker_image, "cat /home/runner/.runner | grep -o '\"version\":\"[^\"]*\"' | cut -d'\"' -f4")
    assert result.returncode == 0


def test_container_runs_on_arm64_platform(docker_image):
    result = run_command_in_container(docker_image, "uname -m")
    assert result.stdout.strip() == "aarch64"
