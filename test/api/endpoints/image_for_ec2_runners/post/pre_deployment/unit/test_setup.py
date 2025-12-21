"""Unit tests for setup.py module."""
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


def _create_popen_with_output_mock():
    """Create a mock Popen process that outputs lines to stdout."""
    mock_process = MagicMock()
    mock_process.stdout = iter(["line1\n", "line2\n"])
    mock_process.returncode = 0
    mock_process.__enter__ = MagicMock(return_value=mock_process)
    mock_process.__exit__ = MagicMock(return_value=False)
    return mock_process


class TestRun:
    """Tests for the run function."""

    def test_run_executes_command(self, setup_module):
        """Run executes command."""
        with patch.object(setup_module.subprocess, "Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter([])
            mock_process.returncode = 0
            mock_process.__enter__ = MagicMock(return_value=mock_process)
            mock_process.__exit__ = MagicMock(return_value=False)
            mock_popen.return_value = mock_process
            setup_module.run("echo hello")
            mock_popen.assert_called_once_with(
                "echo hello",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

    def test_run_raises_on_failure(self, setup_module):
        """Run raises on failure."""
        with patch.object(setup_module.subprocess, "Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = iter([])
            mock_process.returncode = 1
            mock_process.__enter__ = MagicMock(return_value=mock_process)
            mock_process.__exit__ = MagicMock(return_value=False)
            mock_popen.return_value = mock_process
            with pytest.raises(subprocess.CalledProcessError):
                setup_module.run("false")

    def test_run_writes_output_to_stdout(self, setup_module):
        """Run writes output to stdout."""
        with patch.object(setup_module.subprocess, "Popen") as mock_popen, \
             patch.object(setup_module.sys, "stdout") as mock_stdout:
            mock_popen.return_value = _create_popen_with_output_mock()
            setup_module.run("echo hello")
            assert mock_stdout.write.call_count >= 2

    def test_run_flushes_stdout(self, setup_module):
        """Run flushes stdout after each line."""
        with patch.object(setup_module.subprocess, "Popen") as mock_popen, \
             patch.object(setup_module.sys, "stdout") as mock_stdout:
            mock_popen.return_value = _create_popen_with_output_mock()
            setup_module.run("echo hello")
            assert mock_stdout.flush.call_count >= 2


class TestGetArch:
    """Tests for the get_arch function."""

    def test_get_arch_returns_architecture(self, setup_module):
        """Get arch returns architecture."""
        with patch.object(setup_module.subprocess, "check_output") as mock_output:
            mock_output.return_value = b"arm64\n"
            result = setup_module.get_arch()
            assert result == "arm64"

    def test_get_arch_calls_dpkg(self, setup_module):
        """Get arch calls dpkg."""
        with patch.object(setup_module.subprocess, "check_output") as mock_output:
            mock_output.return_value = b"amd64\n"
            setup_module.get_arch()
            mock_output.assert_called_once_with(["dpkg", "--print-architecture"])


class TestGetVersionCodename:
    """Tests for the get_version_codename function."""

    def test_get_version_codename_extracts_codename(self, setup_module):
        """Get version codename extracts codename."""
        with patch.object(setup_module.Path, "__new__") as mock_path_new:
            mock_path = MagicMock()
            mock_path.read_text.return_value = "NAME=Debian\nVERSION_CODENAME=bookworm\n"
            mock_path_new.return_value = mock_path
            result = setup_module.get_version_codename()
            assert result == "bookworm"

    def test_get_version_codename_raises_if_not_found(self, setup_module):
        """Get version codename raises if not found."""
        with patch.object(setup_module.Path, "__new__") as mock_path_new:
            mock_path = MagicMock()
            mock_path.read_text.return_value = "NAME=Debian\n"
            mock_path_new.return_value = mock_path
            with pytest.raises(RuntimeError, match="VERSION_CODENAME not found"):
                setup_module.get_version_codename()


class TestAddDockerAptRepository:
    """Tests for the add_docker_apt_repository function."""

    def test_adds_docker_repository(self, setup_module):
        """Adds docker repository."""
        with patch.object(setup_module, "run") as mock_run, \
             patch.object(setup_module, "Path") as mock_path:
            mock_file = MagicMock()
            mock_path.return_value = mock_file
            setup_module.add_docker_apt_repository("bookworm")
            assert mock_run.call_count == 3

    def test_writes_docker_sources_file(self, setup_module):
        """Writes docker sources file."""
        with patch.object(setup_module, "run"), \
             patch.object(setup_module, "Path") as mock_path:
            mock_file = MagicMock()
            mock_path.return_value = mock_file
            setup_module.add_docker_apt_repository("bookworm")
            mock_file.write_text.assert_called_once()
            written = mock_file.write_text.call_args[0][0]
            assert "docker.com/linux/debian" in written


class TestAddGithubCliAptRepository:
    """Tests for the add_github_cli_apt_repository function."""

    def test_adds_github_cli_repository(self, setup_module):
        """Adds github cli repository."""
        with patch.object(setup_module, "run") as mock_run, \
             patch.object(setup_module, "get_arch", return_value="arm64"), \
             patch.object(setup_module, "Path") as mock_path:
            mock_file = MagicMock()
            mock_path.return_value = mock_file
            setup_module.add_github_cli_apt_repository()
            assert mock_run.call_count == 3

    def test_writes_github_cli_sources_file(self, setup_module):
        """Writes github cli sources file."""
        with patch.object(setup_module, "run"), \
             patch.object(setup_module, "get_arch", return_value="arm64"), \
             patch.object(setup_module, "Path") as mock_path:
            mock_file = MagicMock()
            mock_path.return_value = mock_file
            setup_module.add_github_cli_apt_repository()
            written = mock_file.write_text.call_args[0][0]
            assert "cli.github.com/packages" in written


class TestInstallSystemPackages:
    """Tests for the install_system_packages function."""

    def test_installs_required_packages(self, setup_module):
        """Installs required packages."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_system_packages()
            calls = [str(c) for c in mock_run.call_args_list]
            apt_install_call = [c for c in calls if "apt-get install" in c][0]
            assert "docker-ce" in apt_install_call

    def test_installs_gh_cli(self, setup_module):
        """Installs gh cli."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_system_packages()
            calls = [str(c) for c in mock_run.call_args_list]
            apt_install_call = [c for c in calls if "apt-get install" in c][0]
            assert "gh" in apt_install_call

    def test_enables_docker_service(self, setup_module):
        """Enables docker service."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_system_packages()
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("systemctl enable docker" in c for c in calls)


class TestInstallPythonPackages:
    """Tests for the install_python_packages function."""

    def test_installs_pip_packages(self, setup_module):
        """Installs pip packages."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_python_packages()
            calls = [str(c) for c in mock_run.call_args_list]
            pip_call = [c for c in calls if "pip install" in c][0]
            assert "boto3" in pip_call

    def test_installs_pytest(self, setup_module):
        """Installs pytest."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_python_packages()
            calls = [str(c) for c in mock_run.call_args_list]
            pip_call = [c for c in calls if "pip install" in c][0]
            assert "pytest" in pip_call


def test_install_eslint_installs_globally(setup_module):
    """Test install_eslint installs eslint globally via npm."""
    with patch.object(setup_module, "run") as mock_run:
        setup_module.install_eslint()
        mock_run.assert_called_once_with("npm install -g eslint")


def test_install_jsonlint_installs_globally(setup_module):
    """Test install_jsonlint installs jsonlint globally via npm."""
    with patch.object(setup_module, "run") as mock_run:
        setup_module.install_jsonlint()
        mock_run.assert_called_once_with("npm install -g jsonlint")


def test_install_jscpd_installs_globally(setup_module):
    """Test install_jscpd installs jscpd globally via npm."""
    with patch.object(setup_module, "run") as mock_run:
        setup_module.install_jscpd()
        mock_run.assert_called_once_with("npm install -g jscpd")


class TestInstallHadolint:
    """Tests for the install_hadolint function."""

    def test_downloads_hadolint(self, setup_module):
        """Downloads hadolint binary."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_hadolint("arm64")
            calls = [str(c) for c in mock_run.call_args_list]
            download_call = [c for c in calls if "curl" in c][0]
            assert "hadolint-Linux-arm64" in download_call

    def test_installs_to_usr_local_bin(self, setup_module):
        """Installs to usr local bin."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_hadolint("arm64")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("/usr/local/bin/hadolint" in c for c in calls)

    def test_makes_executable(self, setup_module):
        """Makes executable."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_hadolint("arm64")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("chmod +x" in c for c in calls)


class TestInstallTerraform:
    """Tests for the install_terraform function."""

    def test_downloads_correct_version(self, setup_module):
        """Downloads correct version."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_terraform("arm64", "1.10.3")
            calls = [str(c) for c in mock_run.call_args_list]
            download_call = [c for c in calls if "curl" in c][0]
            assert "terraform_1.10.3_linux_arm64.zip" in download_call

    def test_extracts_to_usr_local_bin(self, setup_module):
        """Extracts to usr local bin."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_terraform("arm64", "1.10.3")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("unzip" in c and "/usr/local/bin" in c for c in calls)

    def test_cleans_up_zip_file(self, setup_module):
        """Cleans up zip file."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_terraform("arm64", "1.10.3")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("rm /tmp/terraform.zip" in c for c in calls)


class TestInstallTflint:
    """Tests for the install_tflint function."""

    def _run_install(self, setup_module):
        """Run install_tflint and return the mock run calls as strings."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_tflint("arm64")
            return [str(c) for c in mock_run.call_args_list]

    def test_downloads_tflint(self, setup_module):
        """Downloads tflint binary."""
        calls = self._run_install(setup_module)
        download_call = [c for c in calls if "curl" in c][0]
        assert "tflint_linux_arm64.zip" in download_call

    def test_extracts_to_usr_local_bin(self, setup_module):
        """Extracts tflint to usr local bin."""
        calls = self._run_install(setup_module)
        assert any("unzip" in c and "/usr/local/bin" in c for c in calls)

    def test_cleans_up_zip_file(self, setup_module):
        """Cleans up tflint zip file."""
        calls = self._run_install(setup_module)
        assert any("rm /tmp/tflint.zip" in c for c in calls)


class TestInstallYq:
    """Tests for the install_yq function."""

    def test_downloads_correct_version(self, setup_module):
        """Downloads correct version."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_yq("arm64", "4.44.1")
            calls = [str(c) for c in mock_run.call_args_list]
            download_call = [c for c in calls if "curl" in c][0]
            assert "v4.44.1" in download_call

    def test_installs_to_usr_local_bin(self, setup_module):
        """Installs to usr local bin."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_yq("arm64", "4.44.1")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("/usr/local/bin/yq" in c for c in calls)

    def test_makes_executable(self, setup_module):
        """Makes executable."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_yq("arm64", "4.44.1")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("chmod +x" in c for c in calls)


class TestCreateRunnerUser:
    """Tests for the create_runner_user function."""

    def test_creates_user(self, setup_module):
        """Creates user."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.create_runner_user("github-runner")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("useradd" in c and "github-runner" in c for c in calls)

    def test_adds_to_docker_group(self, setup_module):
        """Adds to docker group."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.create_runner_user("github-runner")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("usermod -aG docker" in c for c in calls)


class TestInstallGithubActionsRunner:
    """Tests for the install_github_actions_runner function."""

    def test_downloads_runner(self, setup_module):
        """Downloads runner."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_github_actions_runner("arm64", "github-runner", "2.330.0")
            calls = [str(c) for c in mock_run.call_args_list]
            download_call = [c for c in calls if "curl" in c][0]
            assert "actions-runner-linux-arm64-2.330.0" in download_call

    def test_extracts_to_home_directory(self, setup_module):
        """Extracts to home directory."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_github_actions_runner("arm64", "github-runner", "2.330.0")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("/home/github-runner/actions-runner" in c for c in calls)

    def test_runs_install_dependencies(self, setup_module):
        """Runs install dependencies."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_github_actions_runner("arm64", "github-runner", "2.330.0")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("installdependencies.sh" in c for c in calls)


class TestInstallSsmAgent:
    """Tests for the install_ssm_agent function."""

    def test_downloads_agent(self, setup_module):
        """Downloads agent."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_ssm_agent("arm64")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("amazon-ssm-agent.deb" in c for c in calls)

    def test_enables_service(self, setup_module):
        """Enables service."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_ssm_agent("arm64")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("systemctl enable amazon-ssm-agent" in c for c in calls)


class TestInstallCloudwatchAgent:
    """Tests for the install_cloudwatch_agent function."""

    def test_downloads_agent(self, setup_module):
        """Downloads agent."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_cloudwatch_agent("arm64")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("amazon-cloudwatch-agent.deb" in c for c in calls)

    def test_installs_via_dpkg(self, setup_module):
        """Installs via dpkg."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.install_cloudwatch_agent("arm64")
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("dpkg -i" in c for c in calls)


class TestCleanupTempFiles:
    """Tests for the cleanup_temp_files function."""

    def test_removes_tmp(self, setup_module):
        """Removes tmp."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.cleanup_temp_files()
            mock_run.assert_called_once_with("rm -rf /tmp/*")

    def test_calls_run_once(self, setup_module):
        """Calls run once."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.cleanup_temp_files()
            assert mock_run.call_count == 1


class TestConfigureCloudwatchAgent:
    """Tests for the configure_cloudwatch_agent function."""

    def test_copies_config_file(self, setup_module):
        """Copies config file to agent directory."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.configure_cloudwatch_agent()
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("amazon-cloudwatch-agent.json" in c for c in calls)

    def test_copies_to_etc_directory(self, setup_module):
        """Copies to /opt/aws/amazon-cloudwatch-agent/etc."""
        with patch.object(setup_module, "run") as mock_run:
            setup_module.configure_cloudwatch_agent()
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("/opt/aws/amazon-cloudwatch-agent/etc" in c for c in calls)


class TestMain:
    """Tests for the main function."""

    def test_parses_required_arguments(self, setup_module, loaded_config):
        """Parses required arguments."""
        test_args = [
            "setup.py",
            "--runner-user", loaded_config["runner_user"],
            "--runner-version", loaded_config["runner_version"],
            "--terraform-version", loaded_config["terraform_version"],
            "--yq-version", loaded_config["yq_version"],
        ]
        with patch.object(sys, "argv", test_args), \
             patch.object(setup_module, "get_arch", return_value="arm64"), \
             patch.object(setup_module, "get_version_codename", return_value="bookworm"), \
             patch.object(setup_module, "add_docker_apt_repository"), \
             patch.object(setup_module, "add_github_cli_apt_repository"), \
             patch.object(setup_module, "install_system_packages"), \
             patch.object(setup_module, "install_python_packages"), \
             patch.object(setup_module, "install_yq"), \
             patch.object(setup_module, "install_eslint"), \
             patch.object(setup_module, "install_jsonlint"), \
             patch.object(setup_module, "install_jscpd"), \
             patch.object(setup_module, "install_hadolint"), \
             patch.object(setup_module, "install_terraform"), \
             patch.object(setup_module, "install_tflint"), \
             patch.object(setup_module, "create_runner_user"), \
             patch.object(setup_module, "install_github_actions_runner"), \
             patch.object(setup_module, "install_ssm_agent"), \
             patch.object(setup_module, "install_cloudwatch_agent"), \
             patch.object(setup_module, "configure_cloudwatch_agent"), \
             patch.object(setup_module, "cleanup_temp_files"):
            setup_module.main()

    def test_calls_all_install_functions(self, setup_module, loaded_config):
        """Calls all install functions."""
        test_args = [
            "setup.py",
            "--runner-user", loaded_config["runner_user"],
            "--runner-version", loaded_config["runner_version"],
            "--terraform-version", loaded_config["terraform_version"],
            "--yq-version", loaded_config["yq_version"],
        ]
        mocks = {}
        with patch.object(sys, "argv", test_args), \
             patch.object(setup_module, "get_arch", return_value="arm64"), \
             patch.object(setup_module, "get_version_codename", return_value="bookworm"), \
             patch.object(setup_module, "add_docker_apt_repository") as mocks["docker"], \
             patch.object(setup_module, "add_github_cli_apt_repository") as mocks["gh"], \
             patch.object(setup_module, "install_system_packages") as mocks["sys"], \
             patch.object(setup_module, "install_python_packages") as mocks["pip"], \
             patch.object(setup_module, "install_yq") as mocks["yq"], \
             patch.object(setup_module, "install_eslint") as mocks["eslint"], \
             patch.object(setup_module, "install_jsonlint") as mocks["jsonlint"], \
             patch.object(setup_module, "install_jscpd") as mocks["jscpd"], \
             patch.object(setup_module, "install_hadolint") as mocks["hadolint"], \
             patch.object(setup_module, "install_terraform") as mocks["terraform"], \
             patch.object(setup_module, "install_tflint") as mocks["tflint"], \
             patch.object(setup_module, "create_runner_user") as mocks["user"], \
             patch.object(setup_module, "install_github_actions_runner") as mocks["runner"], \
             patch.object(setup_module, "install_ssm_agent") as mocks["ssm"], \
             patch.object(setup_module, "install_cloudwatch_agent") as mocks["cw"], \
             patch.object(setup_module, "configure_cloudwatch_agent") as mocks["cw_cfg"], \
             patch.object(setup_module, "cleanup_temp_files") as mocks["cleanup"]:
            setup_module.main()
        self._verify_install_calls(mocks, loaded_config)

    def _verify_install_calls(self, mocks, config):
        """Verify all install functions were called correctly."""
        mocks["docker"].assert_called_once_with("bookworm")
        mocks["gh"].assert_called_once()
        mocks["sys"].assert_called_once()
        mocks["pip"].assert_called_once()
        mocks["yq"].assert_called_once_with("arm64", config["yq_version"])
        mocks["eslint"].assert_called_once()
        mocks["jsonlint"].assert_called_once()
        mocks["jscpd"].assert_called_once()
        mocks["hadolint"].assert_called_once_with("arm64")
        mocks["terraform"].assert_called_once_with("arm64", config["terraform_version"])
        mocks["tflint"].assert_called_once_with("arm64")
        mocks["user"].assert_called_once_with(config["runner_user"])
        mocks["runner"].assert_called_once_with(
            "arm64", config["runner_user"], config["runner_version"]
        )
        mocks["ssm"].assert_called_once_with("arm64")
        mocks["cw"].assert_called_once_with("arm64")
        mocks["cw_cfg"].assert_called_once()
        mocks["cleanup"].assert_called_once()
