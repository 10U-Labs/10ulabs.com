"""Unit tests for setup script function definitions."""
# pylint: disable=missing-function-docstring,missing-class-docstring


class TestSetupScriptMainFunction:
    def test_script_calls_main_function(self, setup_script_content):
        has_call = '__main__ "$@"' in setup_script_content
        assert has_call

    def test_script_defines_main_function(self, setup_script_content):
        has_function = "__main__()" in setup_script_content
        assert has_function

    def test_script_defines_usage_function(self, setup_script_content):
        has_function = "usage()" in setup_script_content
        assert has_function


class TestSetupScriptAddDockerAptRepositoryFunction:
    def test_script_defines_add_docker_apt_repository(self, setup_script_content):
        has_function = "add_docker_apt_repository()" in setup_script_content
        assert has_function

    def test_function_accepts_docker_key_flag(self, setup_script_content):
        has_flag = "--docker-key)" in setup_script_content
        assert has_flag

    def test_function_accepts_version_codename_flag(self, setup_script_content):
        has_flag = "--version-codename)" in setup_script_content
        assert has_flag

    def test_function_validates_docker_key(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --docker-key' in setup_script_content
        assert has_validation

    def test_function_validates_version_codename(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --version-codename' in setup_script_content
        assert has_validation


class TestSetupScriptCleanupTempFilesFunction:
    def test_script_defines_cleanup_temp_files(self, setup_script_content):
        has_function = "cleanup_temp_files()" in setup_script_content
        assert has_function

    def test_function_removes_tmp_files(self, setup_script_content):
        has_cleanup = "rm -rf /tmp/*" in setup_script_content
        assert has_cleanup


class TestSetupScriptCreateRunnerUserFunction:
    def test_script_defines_create_runner_user(self, setup_script_content):
        has_function = "create_runner_user()" in setup_script_content
        assert has_function

    def test_function_validates_runner_user(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --runner-user' in setup_script_content
        assert has_validation


class TestSetupScriptInstallCloudwatchAgentFunction:
    def test_script_defines_install_cloudwatch_agent(self, setup_script_content):
        has_function = "install_cloudwatch_agent()" in setup_script_content
        assert has_function

    def test_function_validates_arch(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation


class TestSetupScriptInstallGithubActionsRunnerFunction:
    def test_script_defines_install_github_actions_runner(self, setup_script_content):
        has_function = "install_github_actions_runner()" in setup_script_content
        assert has_function

    def test_function_validates_arch(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation

    def test_function_validates_runner_user(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --runner-user' in setup_script_content
        assert has_validation

    def test_function_validates_runner_version(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --runner-version' in setup_script_content
        assert has_validation


class TestSetupScriptInstallSsmAgentFunction:
    def test_script_defines_install_ssm_agent(self, setup_script_content):
        has_function = "install_ssm_agent()" in setup_script_content
        assert has_function

    def test_function_validates_arch(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation


class TestSetupScriptInstallYqFunction:
    def test_function_validates_arch(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --arch' in setup_script_content
        assert has_validation

    def test_function_validates_yq_version(self, setup_script_content):
        has_validation = '${FUNCNAME[0]} requires --yq-version' in setup_script_content
        assert has_validation

    def test_script_defines_install_yq(self, setup_script_content):
        has_function = "install_yq()" in setup_script_content
        assert has_function


class TestSetupScriptSimpleInstallFunctions:
    def test_script_defines_install_python_packages(self, setup_script_content):
        has_function = "install_python_packages()" in setup_script_content
        assert has_function

    def test_script_defines_install_system_packages(self, setup_script_content):
        has_function = "install_system_packages()" in setup_script_content
        assert has_function
