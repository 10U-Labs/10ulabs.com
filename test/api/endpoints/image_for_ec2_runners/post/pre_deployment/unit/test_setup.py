"""Unit tests for setup.py module."""
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


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
            mock_process = MagicMock()
            mock_process.stdout = iter(["line1\n", "line2\n"])
            mock_process.returncode = 0
            mock_process.__enter__ = MagicMock(return_value=mock_process)
            mock_process.__exit__ = MagicMock(return_value=False)
            mock_popen.return_value = mock_process
            setup_module.run("echo hello")
            assert mock_stdout.write.call_count >= 2

    def test_run_flushes_stdout(self, setup_module):
        """Run flushes stdout after each line."""
        with patch.object(setup_module.subprocess, "Popen") as mock_popen, \
             patch.object(setup_module.sys, "stdout") as mock_stdout:
            mock_process = MagicMock()
            mock_process.stdout = iter(["line1\n", "line2\n"])
            mock_process.returncode = 0
            mock_process.__enter__ = MagicMock(return_value=mock_process)
            mock_process.__exit__ = MagicMock(return_value=False)
            mock_popen.return_value = mock_process
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
             patch.object(setup_module, "install_jsonlint"), \
             patch.object(setup_module, "install_hadolint"), \
             patch.object(setup_module, "install_terraform"), \
             patch.object(setup_module, "create_runner_user"), \
             patch.object(setup_module, "install_github_actions_runner"), \
             patch.object(setup_module, "install_ssm_agent"), \
             patch.object(setup_module, "install_cloudwatch_agent"), \
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
        with patch.object(sys, "argv", test_args), \
             patch.object(setup_module, "get_arch", return_value="arm64"), \
             patch.object(setup_module, "get_version_codename", return_value="bookworm"), \
             patch.object(setup_module, "add_docker_apt_repository") as mock_docker, \
             patch.object(setup_module, "add_github_cli_apt_repository") as mock_gh, \
             patch.object(setup_module, "install_system_packages") as mock_sys, \
             patch.object(setup_module, "install_python_packages") as mock_pip, \
             patch.object(setup_module, "install_yq") as mock_yq, \
             patch.object(setup_module, "install_jsonlint") as mock_jsonlint, \
             patch.object(setup_module, "install_hadolint") as mock_hadolint, \
             patch.object(setup_module, "install_terraform") as mock_terraform, \
             patch.object(setup_module, "create_runner_user") as mock_user, \
             patch.object(setup_module, "install_github_actions_runner") as mock_runner, \
             patch.object(setup_module, "install_ssm_agent") as mock_ssm, \
             patch.object(setup_module, "install_cloudwatch_agent") as mock_cw, \
             patch.object(setup_module, "cleanup_temp_files") as mock_cleanup:
            setup_module.main()
            mock_docker.assert_called_once_with("bookworm")
            mock_gh.assert_called_once()
            mock_sys.assert_called_once()
            mock_pip.assert_called_once()
            mock_yq.assert_called_once_with("arm64", loaded_config["yq_version"])
            mock_jsonlint.assert_called_once()
            mock_hadolint.assert_called_once_with("arm64")
            mock_terraform.assert_called_once_with("arm64", loaded_config["terraform_version"])
            mock_user.assert_called_once_with(loaded_config["runner_user"])
            mock_runner.assert_called_once_with(
                "arm64", loaded_config["runner_user"], loaded_config["runner_version"]
            )
            mock_ssm.assert_called_once_with("arm64")
            mock_cw.assert_called_once_with("arm64")
            mock_cleanup.assert_called_once()
