"""Layer 1: Existence tests.

These tests verify that all resources created by this deployment exist.
Tests check that AMI exists, instance launches, and all required tools/packages
are installed.
"""
import pytest


class TestAmiExists:
    """Tests for AMI existence."""

    def test_ami_id_provided(self, test_ami_id):
        """Verify TEST_AMI_ID environment variable is provided."""
        assert test_ami_id, "TEST_AMI_ID not provided"

    def test_ami_exists_in_ec2(self, ec2_client, test_ami_id):
        """Verify AMI exists in EC2."""
        if not test_ami_id:
            pytest.fail("TEST_AMI_ID not provided")

        response = ec2_client.describe_images(ImageIds=[test_ami_id])

        assert len(response["Images"]) == 1

    def test_ami_state_is_available(self, fetched_ami):
        """Verify AMI is in available state."""
        if not fetched_ami:
            pytest.fail("AMI details not available")

        assert fetched_ami["State"] == "available"


class TestInstanceLaunches:
    """Tests for instance launch."""

    def test_instance_passes_instance_status_checks(self, ec2_client, test_instance):
        """Verify instance passes EC2 status checks."""
        if not test_instance:
            pytest.fail("Test instance not created")

        waiter = ec2_client.get_waiter("instance_status_ok")
        waiter.wait(InstanceIds=[test_instance])
        assert True  # Explicit pass

    def test_instance_passes_system_status_checks(self, ec2_client, test_instance):
        """Verify instance passes system status checks."""
        if not test_instance:
            pytest.fail("Test instance not created")

        waiter = ec2_client.get_waiter("system_status_ok")
        waiter.wait(InstanceIds=[test_instance])
        assert True  # Explicit pass


class TestSsmAgentInstalled:
    """Tests for SSM agent installation."""

    def test_ssm_agent_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify SSM agent is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which amazon-ssm-agent")

        assert output["Status"] == "Success"

    def test_ssm_agent_returns_path(self, ssm_client, test_instance, run_ssm_command):
        """Verify SSM agent path is returned."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which amazon-ssm-agent")

        assert output["StandardOutputContent"].strip() != ""


class TestDockerInstalled:
    """Tests for Docker installation."""

    def test_docker_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify Docker is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which docker")

        assert output["Status"] == "Success"

    def test_docker_returns_path(self, ssm_client, test_instance, run_ssm_command):
        """Verify Docker path is returned."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which docker")

        assert output["StandardOutputContent"].strip() != ""


class TestCloudwatchAgentInstalled:
    """Tests for CloudWatch agent installation."""

    def test_cloudwatch_agent_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify CloudWatch agent is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "which amazon-cloudwatch-agent-ctl"
        )

        assert output["Status"] == "Success"

    def test_cloudwatch_agent_returns_path(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify CloudWatch agent path is returned."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "which amazon-cloudwatch-agent-ctl"
        )

        assert output["StandardOutputContent"].strip() != ""


class TestGithubRunnerFilesExist:
    """Tests for GitHub runner files existence."""

    RUNNER_DIR = "/home/github-runner/actions-runner"

    def test_github_runner_user_exists(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify github-runner user exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "id github-runner")

        assert output["Status"] == "Success"

    def test_runner_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        """Verify runner directory exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {self.RUNNER_DIR} && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_bin_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        """Verify bin directory exists in runner directory."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {self.RUNNER_DIR}/bin && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_externals_directory_exists(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify externals directory exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {self.RUNNER_DIR}/externals && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"


class TestBuildToolsInstalled:
    """Tests for build tools installation."""

    def test_aws_cli_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify AWS CLI is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which aws")

        assert output["Status"] == "Success"

    def test_curl_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify curl is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which curl")

        assert output["Status"] == "Success"

    def test_docker_buildx_is_available(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify Docker buildx is available."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "docker buildx version")

        assert output["Status"] == "Success"

    def test_git_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify git is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which git")

        assert output["Status"] == "Success"

    def test_jq_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify jq is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which jq")

        assert output["Status"] == "Success"

    def test_pip_is_available(self, ssm_client, test_instance, run_ssm_command):
        """Verify pip is available."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which pip")

        assert output["Status"] == "Success"

    def test_python3_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify Python3 is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which python3")

        assert output["Status"] == "Success"

    def test_unzip_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify unzip is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which unzip")

        assert output["Status"] == "Success"

    def test_yq_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify yq is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which yq")

        assert output["Status"] == "Success"

    def test_gh_cli_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify GitHub CLI is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which gh")

        assert output["Status"] == "Success"

    def test_eslint_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify eslint is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which eslint")

        assert output["Status"] == "Success"

    def test_jsonlint_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify jsonlint is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which jsonlint")

        assert output["Status"] == "Success"

    def test_hadolint_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify hadolint is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which hadolint")

        assert output["Status"] == "Success"

    def test_jscpd_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify jscpd is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which jscpd")

        assert output["Status"] == "Success"

    def test_terraform_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify terraform is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which terraform")

        assert output["Status"] == "Success"

    def test_tflint_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify tflint is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "which tflint")

        assert output["Status"] == "Success"


class TestPipPackagesInstalled:
    """Tests for pip packages installation."""

    def test_assert_no_inline_lint_disables_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify assert-no-inline-lint-disables is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "python3 -m pip show assert-no-inline-lint-disables"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"

    def test_assert_no_linter_config_files_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify assert-no-linter-config-files is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "python3 -m pip show assert-no-linter-config-files"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"

    def test_assert_one_assert_per_pytest_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify assert-one-assert-per-pytest is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "python3 -m pip show assert-one-assert-per-pytest"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"

    def test_boto3_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify boto3 is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show boto3"
        )

        assert output["Status"] == "Success"

    def test_boto3_stubs_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify boto3-stubs is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show boto3-stubs"
        )

        assert output["Status"] == "Success"

    def test_botocore_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify botocore is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show botocore"
        )

        assert output["Status"] == "Success"

    def test_dnspython_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify dnspython is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show dnspython"
        )

        assert output["Status"] == "Success"

    def test_mypy_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify mypy is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show mypy"
        )

        assert output["Status"] == "Success"

    def test_paramiko_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify paramiko is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show paramiko"
        )

        assert output["Status"] == "Success"

    def test_pylint_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify pylint is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show pylint"
        )

        assert output["Status"] == "Success"

    def test_pytest_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify pytest is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show pytest"
        )

        assert output["Status"] == "Success"

    def test_pytest_dependency_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify pytest-dependency is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show pytest-dependency"
        )

        assert output["Status"] == "Success"

    def test_python_hcl2_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify python-hcl2 is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show python-hcl2"
        )

        assert output["Status"] == "Success"

    def test_pyyaml_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify PyYAML is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show PyYAML"
        )

        assert output["Status"] == "Success"

    def test_requests_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify requests is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show requests"
        )

        assert output["Status"] == "Success"

    def test_types_paramiko_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify types-paramiko is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show types-paramiko"
        )

        assert output["Status"] == "Success"

    def test_types_pyyaml_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify types-PyYAML is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show types-PyYAML"
        )

        assert output["Status"] == "Success"

    def test_types_requests_is_installed(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify types-requests is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show types-requests"
        )

        assert output["Status"] == "Success"

    def test_yamllint_is_installed(self, ssm_client, test_instance, run_ssm_command):
        """Verify yamllint is installed."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pip show yamllint"
        )

        assert output["Status"] == "Success"
