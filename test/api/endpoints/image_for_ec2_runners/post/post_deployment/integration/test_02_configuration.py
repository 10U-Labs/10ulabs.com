"""Layer 2: Configuration tests.

These tests verify that all resources are configured correctly.
Assumes existence (Layer 1) has passed.
"""
import pytest


RUNNER_DIR = "/home/github-runner/actions-runner"


class TestAmiProperties:
    """Tests for AMI properties configuration."""

    def test_ami_architecture_matches_expected(self, fetched_ami, config):
        """Verify AMI architecture matches expected."""
        if not fetched_ami:
            pytest.fail("AMI details not available")

        expected_architecture = config["os_architecture"]

        assert fetched_ami["Architecture"] == expected_architecture

    def test_ami_has_root_device_mapping(self, fetched_ami):
        """Verify AMI has root device mapping."""
        if not fetched_ami:
            pytest.fail("AMI details not available")

        assert "BlockDeviceMappings" in fetched_ami

    def test_ami_root_device_is_ebs(self, fetched_ami):
        """Verify AMI root device is EBS."""
        if not fetched_ami:
            pytest.fail("AMI details not available")

        assert fetched_ami["RootDeviceType"] == "ebs"


class TestAmiTags:
    """Tests for AMI tags configuration."""

    def test_ami_has_purpose_tag(self, ami_tags_dict):
        """Verify AMI has Purpose tag."""
        if not ami_tags_dict:
            pytest.fail("AMI details not available")

        assert "Purpose" in ami_tags_dict

    def test_ami_purpose_tag_value(self, ami_purpose_tag):
        """Verify AMI Purpose tag has correct value."""
        if ami_purpose_tag is None:
            pytest.fail("AMI details not available")

        assert ami_purpose_tag == "GitHub self-hosted EC2 runner"

    def test_ami_has_os_family_tag(self, ami_tags_dict):
        """Verify AMI has OSFamily tag."""
        if not ami_tags_dict:
            pytest.fail("AMI details not available")

        assert "OSFamily" in ami_tags_dict

    def test_ami_os_family_matches_expected(self, ami_os_family_tag, config):
        """Verify AMI OSFamily tag matches expected."""
        if ami_os_family_tag is None:
            pytest.fail("AMI details not available")

        expected_os_family = config["os_family"].title()

        assert ami_os_family_tag == expected_os_family

    def test_ami_has_os_version_tag(self, ami_tags_dict):
        """Verify AMI has OSVersion tag."""
        if not ami_tags_dict:
            pytest.fail("AMI details not available")

        assert "OSVersion" in ami_tags_dict

    def test_ami_os_version_matches_expected(self, ami_os_version_tag, config):
        """Verify AMI OSVersion tag matches expected."""
        if ami_os_version_tag is None:
            pytest.fail("AMI details not available")

        expected_os_version = config["os_version"]

        assert ami_os_version_tag == expected_os_version

    def test_ami_has_os_architecture_tag(self, ami_tags_dict):
        """Verify AMI has OSArchitecture tag."""
        if not ami_tags_dict:
            pytest.fail("AMI details not available")

        assert "OSArchitecture" in ami_tags_dict

    def test_ami_os_architecture_matches_expected(self, ami_os_architecture_tag, config):
        """Verify AMI OSArchitecture tag matches expected."""
        if ami_os_architecture_tag is None:
            pytest.fail("AMI details not available")

        expected_os_architecture = config["os_architecture"]

        assert ami_os_architecture_tag == expected_os_architecture


class TestBuildToolVersions:
    """Tests for build tool versions."""

    def test_python3_version_is_3_13(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify Python3 version is 3.13."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "python3 --version")

        assert "Python 3.13" in output["StandardOutputContent"]

    def test_aws_cli_version_is_v2(self, ssm_client, test_instance, run_ssm_command):
        """Verify AWS CLI is version 2."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "aws --version")

        assert "aws-cli/2" in output["StandardOutputContent"]

    def test_pytest_can_run_version_check(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify pytest can run version check."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "pytest --version")

        assert output["Status"] == "Success"

    def test_mypy_can_run_version_check(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify mypy can run version check."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "python3 -m mypy --version")

        assert output["Status"] == "Success"

    def test_pylint_can_run_version_check(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify pylint can run version check."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m pylint --version"
        )

        assert output["Status"] == "Success"

    def test_yamllint_can_run_version_check(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify yamllint can run version check."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "python3 -m yamllint --version"
        )

        assert output["Status"] == "Success"

    def test_gh_cli_version_succeeds(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify GitHub CLI version check succeeds."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "gh --version")

        assert output["Status"] == "Success"

    def test_gh_cli_version_format(self, ssm_client, test_instance, run_ssm_command):
        """Verify GitHub CLI version format."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "gh --version")

        assert "gh version" in output["StandardOutputContent"]

    def test_yq_can_parse_yaml(self, ssm_client, test_instance, run_ssm_command):
        """Verify yq can parse YAML."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(
            ssm_client, test_instance, "echo 'foo: bar' | yq '.foo'"
        )

        assert output["Status"] == "Success"

    def test_terraform_version_succeeds(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify terraform version check succeeds."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "terraform --version")

        assert output["Status"] == "Success"


class TestCloudwatchAgentConfiguration:
    """Tests for CloudWatch agent configuration."""

    def test_cloudwatch_agent_config_exists(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify CloudWatch agent config file exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "test -f /etc/amazon-cloudwatch-agent.json && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_cloudwatch_agent_config_has_metrics_namespace(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify CloudWatch agent config has metrics namespace."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "grep -q 'namespace' /etc/amazon-cloudwatch-agent.json && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"


class TestGithubRunnerScriptsExecutable:
    """Tests for GitHub runner scripts being executable."""

    def test_config_script_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify config.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/config.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_run_script_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify run.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/run.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_env_script_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify env.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/env.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_run_helper_template_exists(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify run-helper.sh.template exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -f {RUNNER_DIR}/run-helper.sh.template && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_safe_sleep_script_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify safe_sleep.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/safe_sleep.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_installdependencies_script_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify installdependencies.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/installdependencies.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"


class TestGithubRunnerBinariesExecutable:
    """Tests for GitHub runner binaries being executable."""

    def test_runner_listener_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify Runner.Listener binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/Runner.Listener && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_worker_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify Runner.Worker binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/Runner.Worker && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_plugin_host_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify Runner.PluginHost binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/Runner.PluginHost && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_listener_executes(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify Runner.Listener binary can execute."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"{RUNNER_DIR}/bin/Runner.Listener --version"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"
