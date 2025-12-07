"""Unit tests for setup script function definitions."""


class TestSetupScriptMainFunction:
    """Tests for setup script main function."""

    def test_script_calls_main_function(self, setup_script_content):
        """Script calls main function."""

        has_call = '__main__ "$@"' in setup_script_content
        assert has_call

    def test_script_defines_main_function(self, setup_script_content):
        """Script defines main function."""

        has_function = "__main__()" in setup_script_content
        assert has_function

    def test_script_defines_usage_function(self, setup_script_content):
        """Script defines usage function."""

        has_function = "usage()" in setup_script_content
        assert has_function


class TestSetupScriptAddDockerAptRepositoryFunction:
    """Tests for setup script add docker apt repository function."""

    def test_script_defines_add_docker_apt_repository(self, setup_script_content):
        """Script defines add docker apt repository."""

        has_function = "add_docker_apt_repository()" in setup_script_content
        assert has_function

    def test_function_accepts_docker_key_flag(self, setup_script_content):
        """Function accepts docker key flag."""

        has_flag = "--docker-key)" in setup_script_content
        assert has_flag

    def test_function_accepts_version_codename_flag(self, setup_script_content):
        """Function accepts version codename flag."""

        has_flag = "--version-codename)" in setup_script_content
        assert has_flag

    def test_function_validates_docker_key(self, setup_script_content):
        """Function validates docker key."""

        has_validation = '${FUNCNAME[0]} requires --docker-key' in setup_script_content
        assert has_validation

    def test_function_validates_version_codename(self, setup_script_content):
        """Function validates version codename."""

        has_validation = '${FUNCNAME[0]} requires --version-codename' in setup_script_content
        assert has_validation


class TestSetupScriptCleanupTempFilesFunction:
    """Tests for setup script cleanup temp files function."""

    def test_script_defines_cleanup_temp_files(self, setup_script_content):
        """Script defines cleanup temp files."""

        has_function = "cleanup_temp_files()" in setup_script_content
        assert has_function

    def test_function_removes_tmp_files(self, setup_script_content):
        """Function removes tmp files."""

        has_cleanup = "rm -rf /tmp/*" in setup_script_content
        assert has_cleanup


class TestSetupScriptCreateRunnerUserFunction:
    """Tests for setup script create runner user function."""

    def test_script_defines_create_runner_user(self, setup_script_content):
        """Script defines create runner user."""

        has_function = "create_runner_user()" in setup_script_content
        assert has_function

    def test_function_validates_runner_user(self, setup_script_content):
        """Function validates runner user."""

        has_validation = '${FUNCNAME[0]} requires --runner-user' in setup_script_content
        assert has_validation


class TestSetupScriptInstallCloudwatchAgentFunction:
    """Tests for setup script install cloudwatch agent function."""

    def test_script_defines_install_cloudwatch_agent(self, setup_script_content):
        """Script defines install cloudwatch agent."""

        has_function = "install_cloudwatch_agent()" in setup_script_content
        assert has_function

    def test_function_validates_arch(self, setup_script_content):
        """Function validates arch."""

        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation


class TestSetupScriptInstallGithubActionsRunnerFunction:
    """Tests for setup script install github actions runner function."""

    def test_script_defines_install_github_actions_runner(self, setup_script_content):
        """Script defines install github actions runner."""

        has_function = "install_github_actions_runner()" in setup_script_content
        assert has_function

    def test_function_validates_arch(self, setup_script_content):
        """Function validates arch."""

        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation

    def test_function_validates_runner_user(self, setup_script_content):
        """Function validates runner user."""

        has_validation = '${FUNCNAME[0]} requires --runner-user' in setup_script_content
        assert has_validation

    def test_function_validates_runner_version(self, setup_script_content):
        """Function validates runner version."""

        has_validation = '${FUNCNAME[0]} requires --runner-version' in setup_script_content
        assert has_validation


class TestSetupScriptInstallSsmAgentFunction:
    """Tests for setup script install ssm agent function."""

    def test_script_defines_install_ssm_agent(self, setup_script_content):
        """Script defines install ssm agent."""

        has_function = "install_ssm_agent()" in setup_script_content
        assert has_function

    def test_function_validates_arch(self, setup_script_content):
        """Function validates arch."""

        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation


class TestSetupScriptInstallYqFunction:
    """Tests for setup script install yq function."""

    def test_function_validates_arch(self, setup_script_content):
        """Function validates arch."""

        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation

    def test_function_validates_yq_version(self, setup_script_content):
        """Function validates yq version."""

        has_validation = '${FUNCNAME[0]} requires --yq-version' in setup_script_content
        assert has_validation

    def test_script_defines_install_yq(self, setup_script_content):
        """Script defines install yq."""

        has_function = "install_yq()" in setup_script_content
        assert has_function


class TestSetupScriptSimpleInstallFunctions:
    """Tests for setup script simple install functions."""

    def test_script_defines_install_python_packages(self, setup_script_content):
        """Script defines install python packages."""

        has_function = "install_python_packages()" in setup_script_content
        assert has_function

    def test_script_defines_install_system_packages(self, setup_script_content):
        """Script defines install system packages."""

        has_function = "install_system_packages()" in setup_script_content
        assert has_function
