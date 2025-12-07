"""Unit tests for setup script command line arguments."""


class TestSetupScriptRunnerVersionArgument:
    """Tests for setup script runner version argument."""

    def test_script_accepts_runner_version_flag(self, setup_script_content):
        """Script accepts runner version flag."""

        has_flag = "--runner-version)" in setup_script_content
        assert has_flag

    def test_script_requires_runner_version(self, setup_script_content):
        """Script requires runner version."""

        has_validation = 'if [[ -z "$runner_version" ]]' in setup_script_content or \
                         'elif [[ -z "$runner_version" ]]' in setup_script_content
        assert has_validation


class TestSetupScriptYqVersionArgument:
    """Tests for setup script yq version argument."""

    def test_script_accepts_yq_version_flag(self, setup_script_content):
        """Script accepts yq version flag."""

        has_flag = "--yq-version)" in setup_script_content
        assert has_flag

    def test_script_requires_yq_version(self, setup_script_content):
        """Script requires yq version."""

        has_validation = 'if [[ -z "$yq_version" ]]' in setup_script_content or \
                         'elif [[ -z "$yq_version" ]]' in setup_script_content
        assert has_validation


class TestSetupScriptRunnerUserArgument:
    """Tests for setup script runner user argument."""

    def test_script_accepts_runner_user_flag(self, setup_script_content):
        """Script accepts runner user flag."""

        has_flag = "--runner-user)" in setup_script_content
        assert has_flag

    def test_script_rejects_unknown_arguments(self, setup_script_content):
        """Script rejects unknown arguments."""

        has_unknown_handler = "Unknown argument" in setup_script_content
        assert has_unknown_handler

    def test_script_requires_runner_user(self, setup_script_content):
        """Script requires runner user."""

        has_validation = 'if [[ -z "$runner_user" ]]' in setup_script_content or \
                         'elif [[ -z "$runner_user" ]]' in setup_script_content
        assert has_validation
