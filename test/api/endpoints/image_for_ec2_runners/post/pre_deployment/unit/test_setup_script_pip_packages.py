"""Unit tests for pip package installations in setup script."""
# pylint: disable=missing-function-docstring,missing-class-docstring


class TestSetupScriptPipAwsPackages:
    def test_script_installs_boto3(self, setup_script_content):
        has_package = "boto3" in setup_script_content
        assert has_package

    def test_script_installs_botocore(self, setup_script_content):
        has_package = "botocore" in setup_script_content
        assert has_package


class TestSetupScriptPipDevelopmentPackages:
    def test_script_installs_mypy(self, setup_script_content):
        has_package = "mypy" in setup_script_content
        assert has_package

    def test_script_installs_pylint(self, setup_script_content):
        has_package = "pylint" in setup_script_content
        assert has_package

    def test_script_installs_pytest(self, setup_script_content):
        has_package = "pytest" in setup_script_content
        assert has_package

    def test_script_installs_yamllint(self, setup_script_content):
        has_package = "yamllint" in setup_script_content
        assert has_package


class TestSetupScriptPipUtilityPackages:
    def test_script_installs_paramiko(self, setup_script_content):
        has_package = "paramiko" in setup_script_content
        assert has_package

    def test_script_installs_pyyaml(self, setup_script_content):
        has_package = "pyyaml" in setup_script_content
        assert has_package

    def test_script_installs_requests(self, setup_script_content):
        has_package = "requests" in setup_script_content
        assert has_package
