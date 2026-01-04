"""Layer 1: Existence tests for ECS runner Docker image.

These tests verify that all required components exist in the deployed image.
Per POST_DEPLOYMENT_INTEGRATION_TESTS.md tenets, existence tests only verify
that resources were created - no configuration or wiring checks.
"""
import boto3

from .conftest import run_command_in_container


class TestImageExists:
    """Verify Docker and ECR images exist."""

    def test_docker_image_exists(self, docker_image):
        """Test that Docker image exists."""
        assert docker_image

    def test_ecr_image_exists(self, aws_region, ecr_repository, image_tag):
        """Test that ECR image exists with expected tag."""
        client = boto3.client("ecr", region_name=aws_region)
        response = client.describe_images(
            repositoryName=ecr_repository,
            imageIds=[{"imageTag": image_tag}]
        )
        assert len(response["imageDetails"]) == 1


class TestSystemPackagesExist:
    """Verify base system packages are installed."""

    def test_python3_installed(self, docker_image):
        """Test that Python 3 is installed in the container."""
        result = run_command_in_container(docker_image, "which python3")
        assert result.returncode == 0

    def test_git_installed(self, docker_image):
        """Test that git is installed in the container."""
        result = run_command_in_container(docker_image, "which git")
        assert result.returncode == 0

    def test_jq_installed(self, docker_image):
        """Test that jq is installed in the container."""
        result = run_command_in_container(docker_image, "which jq")
        assert result.returncode == 0

    def test_sudo_installed(self, docker_image):
        """Test that sudo is installed in the container."""
        result = run_command_in_container(docker_image, "which sudo")
        assert result.returncode == 0

    def test_tar_installed(self, docker_image):
        """Test that tar is installed in the container."""
        result = run_command_in_container(docker_image, "which tar")
        assert result.returncode == 0

    def test_zip_installed(self, docker_image):
        """Test that zip is installed in the container."""
        result = run_command_in_container(docker_image, "which zip")
        assert result.returncode == 0

    def test_procps_installed(self, docker_image):
        """Test that procps is installed in the container."""
        result = run_command_in_container(docker_image, "which ps")
        assert result.returncode == 0


class TestSystemLibrariesExist:
    """Verify required system libraries are installed."""

    def test_ca_certificates_installed(self, docker_image):
        """Test that CA certificates are installed in the container."""
        result = run_command_in_container(
            docker_image,
            "test -f /etc/ssl/certs/ca-certificates.crt"
        )
        assert result.returncode == 0

    def test_libicu76_installed(self, docker_image):
        """Test that libicu76 is installed in the container."""
        result = run_command_in_container(
            docker_image,
            "dpkg -l | grep -q libicu76"
        )
        assert result.returncode == 0

    def test_libssl3t64_installed(self, docker_image):
        """Test that libssl3t64 is installed in the container."""
        result = run_command_in_container(
            docker_image,
            "dpkg -l | grep -q libssl3t64"
        )
        assert result.returncode == 0

    def test_liblttng_ust1_installed(self, docker_image):
        """Test that liblttng-ust1 is installed in the container."""
        result = run_command_in_container(
            docker_image,
            "dpkg -l | grep -q liblttng-ust1"
        )
        assert result.returncode == 0

    def test_zlib1g_installed(self, docker_image):
        """Test that zlib1g is installed in the container."""
        result = run_command_in_container(
            docker_image,
            "dpkg -l | grep -q zlib1g"
        )
        assert result.returncode == 0


class TestCLIToolsExist:
    """Verify CLI tools are installed."""

    def test_aws_cli_installed(self, docker_image):
        """Test that AWS CLI is installed in the container."""
        result = run_command_in_container(docker_image, "which aws")
        assert result.returncode == 0

    def test_github_cli_installed(self, docker_image):
        """Test that GitHub CLI is installed."""
        result = run_command_in_container(docker_image, "which gh")
        assert result.returncode == 0


class TestNodeJSExists:
    """Verify Node.js and npm are installed."""

    def test_nodejs_installed(self, docker_image):
        """Test that Node.js is installed."""
        result = run_command_in_container(docker_image, "which node")
        assert result.returncode == 0

    def test_npm_installed(self, docker_image):
        """Test that npm is installed."""
        result = run_command_in_container(docker_image, "which npm")
        assert result.returncode == 0

    def test_eslint_installed_globally(self, docker_image):
        """Test that eslint is installed globally."""
        result = run_command_in_container(docker_image, "which eslint")
        assert result.returncode == 0

    def test_jsonlint_installed_globally(self, docker_image):
        """Test that jsonlint is installed globally."""
        result = run_command_in_container(docker_image, "which jsonlint")
        assert result.returncode == 0

    def test_jscpd_installed_globally(self, docker_image):
        """Test that jscpd is installed globally."""
        result = run_command_in_container(docker_image, "which jscpd")
        assert result.returncode == 0


class TestTerraformExists:
    """Verify Terraform is installed."""

    def test_terraform_installed(self, docker_image):
        """Test that Terraform is installed."""
        result = run_command_in_container(docker_image, "which terraform")
        assert result.returncode == 0

    def test_tflint_installed(self, docker_image):
        """Test that tflint is installed."""
        result = run_command_in_container(docker_image, "which tflint")
        assert result.returncode == 0


class TestPythonPackagesExist:
    """Verify Python packages are installed."""

    def test_assert_no_inline_directives_installed(self, docker_image):
        """Test that assert-no-inline-directives is installed."""
        cmd = "python3 -m pip show assert-no-inline-directives"
        result = run_command_in_container(docker_image, cmd)
        assert result.returncode == 0

    def test_assert_no_linter_config_files_installed(self, docker_image):
        """Test that assert-no-linter-config-files is installed."""
        cmd = "python3 -m pip show assert-no-linter-config-files"
        result = run_command_in_container(docker_image, cmd)
        assert result.returncode == 0

    def test_assert_one_assert_per_pytest_installed(self, docker_image):
        """Test that assert-one-assert-per-pytest is installed."""
        cmd = "python3 -m pip show assert-one-assert-per-pytest"
        result = run_command_in_container(docker_image, cmd)
        assert result.returncode == 0

    def test_boto3_installed(self, docker_image):
        """Test that boto3 is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show boto3"
        )
        assert result.returncode == 0

    def test_boto3_stubs_installed(self, docker_image):
        """Test that boto3-stubs is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show boto3-stubs"
        )
        assert result.returncode == 0

    def test_botocore_installed(self, docker_image):
        """Test that botocore is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show botocore"
        )
        assert result.returncode == 0

    def test_dnspython_installed(self, docker_image):
        """Test that dnspython is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show dnspython"
        )
        assert result.returncode == 0

    def test_mypy_installed(self, docker_image):
        """Test that mypy is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show mypy"
        )
        assert result.returncode == 0

    def test_paramiko_installed(self, docker_image):
        """Test that paramiko is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show paramiko"
        )
        assert result.returncode == 0

    def test_pyjwt_installed(self, docker_image):
        """Test that PyJWT is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show PyJWT"
        )
        assert result.returncode == 0

    def test_pylint_installed(self, docker_image):
        """Test that pylint is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show pylint"
        )
        assert result.returncode == 0

    def test_pytest_installed(self, docker_image):
        """Test that pytest is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show pytest"
        )
        assert result.returncode == 0

    def test_pytest_dependency_installed(self, docker_image):
        """Test that pytest-dependency is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show pytest-dependency"
        )
        assert result.returncode == 0

    def test_python_hcl2_installed(self, docker_image):
        """Test that python-hcl2 is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show python-hcl2"
        )
        assert result.returncode == 0

    def test_pyyaml_installed(self, docker_image):
        """Test that PyYAML is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show PyYAML"
        )
        assert result.returncode == 0

    def test_requests_installed(self, docker_image):
        """Test that requests is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show requests"
        )
        assert result.returncode == 0

    def test_types_paramiko_installed(self, docker_image):
        """Test that types-paramiko is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show types-paramiko"
        )
        assert result.returncode == 0

    def test_types_pyyaml_installed(self, docker_image):
        """Test that types-PyYAML is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show types-PyYAML"
        )
        assert result.returncode == 0

    def test_types_requests_installed(self, docker_image):
        """Test that types-requests is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show types-requests"
        )
        assert result.returncode == 0

    def test_yamllint_installed(self, docker_image):
        """Test that yamllint is installed."""
        result = run_command_in_container(
            docker_image, "python3 -m pip show yamllint"
        )
        assert result.returncode == 0

    def test_python3_venv_installed(self, docker_image):
        """Test that Python venv module is installed in the container."""
        result = run_command_in_container(
            docker_image,
            "python3 -m venv --help"
        )
        assert result.returncode == 0


class TestScriptsExist:
    """Verify GitHub runner and entrypoint scripts exist."""

    def test_github_runner_config_script_exists(self, docker_image):
        """Test that GitHub runner config script exists."""
        result = run_command_in_container(docker_image, "test -f /home/runner/config.sh")
        assert result.returncode == 0

    def test_github_runner_run_script_exists(self, docker_image):
        """Test that GitHub runner run script exists."""
        result = run_command_in_container(
            docker_image, "test -f /home/runner/run.sh"
        )
        assert result.returncode == 0

    def test_entrypoint_script_exists(self, docker_image):
        """Test that entrypoint script exists."""
        result = run_command_in_container(docker_image, "test -f /home/runner/entrypoint.py")
        assert result.returncode == 0


class TestRunnerUserExists:
    """Verify runner user exists."""

    def test_runner_user_exists(self, docker_image):
        """Test that the runner user exists in the container."""
        result = run_command_in_container(docker_image, "id runner")
        assert result.returncode == 0

    def test_runner_user_home_directory(self, docker_image):
        """Test that the runner user has a home directory."""
        result = run_command_in_container(
            docker_image,
            "test -d /home/runner"
        )
        assert result.returncode == 0
