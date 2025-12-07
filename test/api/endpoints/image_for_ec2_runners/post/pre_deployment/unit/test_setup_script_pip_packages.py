"""Unit tests for pip package installations in setup script."""


class TestSetupScriptPipAwsPackages:
    """Tests for setup script pip aws packages."""

    def test_script_installs_boto3(self, setup_script_content):
        """Script installs boto3."""
        has_package = "boto3" in setup_script_content
        assert has_package

    def test_script_installs_botocore(self, setup_script_content):
        """Script installs botocore."""
        has_package = "botocore" in setup_script_content
        assert has_package


class TestSetupScriptPipDevelopmentPackages:
    """Tests for setup script pip development packages."""

    def test_script_installs_mypy(self, setup_script_content):
        """Script installs mypy."""
        has_package = "mypy" in setup_script_content
        assert has_package

    def test_script_installs_pylint(self, setup_script_content):
        """Script installs pylint."""
        has_package = "pylint" in setup_script_content
        assert has_package

    def test_script_installs_pytest(self, setup_script_content):
        """Script installs pytest."""
        has_package = "pytest" in setup_script_content
        assert has_package

    def test_script_installs_yamllint(self, setup_script_content):
        """Script installs yamllint."""
        has_package = "yamllint" in setup_script_content
        assert has_package


class TestSetupScriptPipUtilityPackages:
    """Tests for setup script pip utility packages."""

    def test_script_installs_paramiko(self, setup_script_content):
        """Script installs paramiko."""
        has_package = "paramiko" in setup_script_content
        assert has_package

    def test_script_installs_pyyaml(self, setup_script_content):
        """Script installs pyyaml."""
        has_package = "pyyaml" in setup_script_content
        assert has_package

    def test_script_installs_requests(self, setup_script_content):
        """Script installs requests."""
        has_package = "requests" in setup_script_content
        assert has_package
