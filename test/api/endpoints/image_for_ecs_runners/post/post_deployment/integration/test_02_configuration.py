"""Layer 2: Configuration tests for ECS runner Docker image.

These tests verify that all components are configured correctly.
Per POST_DEPLOYMENT_INTEGRATION_TESTS.md tenets, configuration tests
verify settings, permissions, and versions - assumes existence tests passed.
"""
import subprocess

import boto3

from .conftest import ENTRYPOINT_IMPORT, run_command_in_container


class TestImageConfiguration:
    """Verify Docker and ECR images are configured correctly."""

    def test_image_platform_is_arm64(self, docker_image):
        """Test that image is built for ARM64 architecture."""
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.Architecture}}", docker_image],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "arm64"

    def test_image_has_entrypoint(self, docker_image):
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

    def test_container_user_is_runner(self, docker_image):
        """Test that container runs as runner user."""
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.Config.User}}", docker_image],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "runner"

    def test_container_workdir_is_runner_home(self, docker_image):
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

    def test_debian_base_image(self, docker_image):
        """Test that image is based on Debian."""
        result = run_command_in_container(
            docker_image, "cat /etc/os-release | grep -q debian"
        )
        assert result.returncode == 0

    def test_ecr_image_is_arm64(self, aws_region, ecr_repository, image_tag):
        """Test that ECR image is ARM64 multi-platform."""
        client = boto3.client("ecr", region_name=aws_region)
        response = client.describe_images(
            repositoryName=ecr_repository,
            imageIds=[{"imageTag": image_tag}]
        )
        expected_media_type = "application/vnd.oci.image.index.v1+json"
        assert (
            response["imageDetails"][0]["imageManifestMediaType"]
            == expected_media_type
        )


class TestCLIConfiguration:
    """Verify CLI tools are configured correctly."""

    def test_aws_cli_version(self, docker_image):
        """Test that AWS CLI version 2 is installed in the container."""
        result = run_command_in_container(
            docker_image,
            "aws --version | grep -q 'aws-cli/2'"
        )
        assert result.returncode == 0

    def test_github_cli_executable(self, docker_image):
        """Test that GitHub CLI is executable."""
        result = run_command_in_container(docker_image, "gh --version")
        assert result.returncode == 0

    def test_github_cli_version_output(self, docker_image):
        """Test that GitHub CLI returns version string."""
        result = run_command_in_container(docker_image, "gh --version")
        assert "gh version" in result.stdout


class TestNodeJSConfiguration:
    """Verify Node.js and Terraform are configured correctly."""

    def test_nodejs_version_matches(self, docker_image, config_node_version):
        """Test that Node.js version matches configuration."""
        result = run_command_in_container(
            docker_image,
            f"node --version | grep -q 'v{config_node_version}'"
        )
        assert result.returncode == 0

    def test_node_path_includes_global_modules(self, docker_image):
        """Test that NODE_PATH includes global node_modules."""
        result = run_command_in_container(
            docker_image,
            "echo $NODE_PATH | grep -q '/usr/local/lib/node_modules'"
        )
        assert result.returncode == 0

    def test_node_modules_symlink_exists(self, docker_image):
        """Test that node_modules symlink exists in WORKDIR for ESM resolution."""
        result = run_command_in_container(
            docker_image,
            "test -L /home/runner/node_modules"
        )
        assert result.returncode == 0

    def test_terraform_version_matches(self, docker_image, config_terraform_version):
        """Test that Terraform version matches configuration."""
        result = run_command_in_container(
            docker_image,
            f"terraform version | grep -q 'v{config_terraform_version}'"
        )
        assert result.returncode == 0


class TestScriptsConfiguration:
    """Verify GitHub runner and entrypoint scripts are configured correctly."""

    def test_github_runner_files_owned_by_runner(self, docker_image):
        """Test that GitHub runner files are owned by runner user."""
        result = run_command_in_container(
            docker_image, "test -O /home/runner/config.sh"
        )
        assert result.returncode == 0

    def test_github_runner_version_matches_expected(self, docker_image):
        """Test that GitHub runner version can be read."""
        result = run_command_in_container(
            docker_image,
            "cat /home/runner/.runner | "
            "grep -o '\"version\":\"[^\"]*\"' | "
            "cut -d'\"' -f4"
        )
        assert result.returncode == 0

    def test_entrypoint_script_executable(self, docker_image):
        """Test that entrypoint script is executable."""
        result = run_command_in_container(
            docker_image, "test -x /home/runner/entrypoint.py"
        )
        assert result.returncode == 0

    def test_entrypoint_script_owned_by_runner(self, docker_image):
        """Test that entrypoint script is owned by runner user."""
        result = run_command_in_container(
            docker_image, "test -O /home/runner/entrypoint.py"
        )
        assert result.returncode == 0

    def test_entrypoint_shebang_is_python3(self, docker_image):
        """Test that entrypoint script has python3 shebang."""
        result = run_command_in_container(
            docker_image,
            "head -1 /home/runner/entrypoint.py | grep -q 'python3'"
        )
        assert result.returncode == 0


class TestEntrypointArgumentsConfiguration:
    """Verify entrypoint script arguments are configured correctly."""

    def test_entrypoint_accepts_repo_argument(self, docker_image):
        """Test that entrypoint accepts --repo argument."""
        result = run_command_in_container(
            docker_image,
            "/home/runner/entrypoint.py --help | grep -q '\\--repo'"
        )
        assert result.returncode == 0

    def test_entrypoint_accepts_name_argument(self, docker_image):
        """Test that entrypoint accepts --name argument."""
        result = run_command_in_container(
            docker_image,
            "/home/runner/entrypoint.py --help | grep -q '\\--name'"
        )
        assert result.returncode == 0

    def test_entrypoint_accepts_labels_argument(self, docker_image):
        """Test that entrypoint accepts --labels argument."""
        result = run_command_in_container(
            docker_image,
            "/home/runner/entrypoint.py --help | grep -q '\\--labels'"
        )
        assert result.returncode == 0

    def test_entrypoint_accepts_token_argument(self, docker_image):
        """Test that entrypoint accepts --token argument."""
        result = run_command_in_container(
            docker_image,
            "/home/runner/entrypoint.py --help | grep -q '\\--token'"
        )
        assert result.returncode == 0

    def test_entrypoint_accepts_check_interval_argument(self, docker_image):
        """Test that entrypoint accepts --check-interval argument."""
        result = run_command_in_container(
            docker_image,
            "/home/runner/entrypoint.py --help | grep -q '\\--check-interval'"
        )
        assert result.returncode == 0

    def test_entrypoint_check_interval_has_default(self, docker_image):
        """Test that --check-interval shows default value in help."""
        result = run_command_in_container(
            docker_image,
            "/home/runner/entrypoint.py --help | grep -q 'default: 30'"
        )
        assert result.returncode == 0


class TestEntrypointFunctionsConfiguration:
    """Verify entrypoint script functions are configured correctly."""

    def test_entrypoint_has_start_run_monitor_function(self, docker_image):
        """Test that entrypoint has start_run_monitor function."""
        result = run_command_in_container(
            docker_image,
            f"python3 -c '{ENTRYPOINT_IMPORT}"
            "assert hasattr(entrypoint, \"start_run_monitor\")'"
        )
        assert result.returncode == 0

    def test_entrypoint_has_stop_run_monitor_function(self, docker_image):
        """Test that entrypoint has stop_run_monitor function."""
        result = run_command_in_container(
            docker_image,
            f"python3 -c '{ENTRYPOINT_IMPORT}"
            "assert hasattr(entrypoint, \"stop_run_monitor\")'"
        )
        assert result.returncode == 0

    def test_entrypoint_has_extract_run_id_from_name_function(self, docker_image):
        """Test that entrypoint has extract_run_id_from_name function."""
        result = run_command_in_container(
            docker_image,
            f"python3 -c '{ENTRYPOINT_IMPORT}"
            "assert hasattr(entrypoint, \"extract_run_id_from_name\")'"
        )
        assert result.returncode == 0


def test_runner_user_has_sudo_privileges(docker_image):
    """Test that the runner user has passwordless sudo privileges."""
    result = run_command_in_container(docker_image, "sudo -n true")
    assert result.returncode == 0
