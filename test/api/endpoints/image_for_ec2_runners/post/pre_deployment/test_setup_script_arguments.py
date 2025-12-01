import pytest


class TestSetupScriptRunnerVersionArgument:
    def test_script_accepts_runner_version_flag(self, setup_script_content):
        has_flag = "--runner-version)" in setup_script_content
        assert has_flag

    def test_script_requires_runner_version(self, setup_script_content):
        has_validation = 'if [[ -z "$RUNNER_VERSION" ]]' in setup_script_content
        assert has_validation


class TestSetupScriptYqVersionArgument:
    def test_script_accepts_yq_version_flag(self, setup_script_content):
        has_flag = "--yq-version)" in setup_script_content
        assert has_flag

    def test_script_requires_yq_version(self, setup_script_content):
        has_validation = 'if [[ -z "$YQ_VERSION" ]]' in setup_script_content
        assert has_validation


class TestSetupScriptRunnerUserArgument:
    def test_script_accepts_runner_user_flag(self, setup_script_content):
        has_flag = "--runner-user)" in setup_script_content
        assert has_flag

    def test_script_requires_runner_user(self, setup_script_content):
        has_validation = 'if [[ -z "$RUNNER_USER" ]]' in setup_script_content
        assert has_validation


class TestSetupScriptUnknownArguments:
    def test_script_rejects_unknown_arguments(self, setup_script_content):
        has_unknown_handler = "Unknown argument" in setup_script_content
        assert has_unknown_handler
