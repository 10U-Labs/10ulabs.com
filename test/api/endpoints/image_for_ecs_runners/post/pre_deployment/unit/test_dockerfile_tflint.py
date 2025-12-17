"""Tests for Dockerfile TFLint installation."""


def test_dockerfile_installs_tflint(dockerfile_run_commands_joined):
    """Test that Dockerfile installs TFLint."""
    assert 'tflint' in dockerfile_run_commands_joined


def test_dockerfile_downloads_tflint_from_official_source(dockerfile_content):
    """Test that Dockerfile downloads TFLint from official GitHub releases."""
    assert 'github.com/terraform-linters/tflint/releases' in dockerfile_content


def test_dockerfile_uses_tflint_version_build_arg(dockerfile_content):
    """Test that Dockerfile uses TFLINT_VERSION build arg."""
    assert 'ARG TFLINT_VERSION' in dockerfile_content


def test_dockerfile_tflint_url_uses_version_variable(dockerfile_content):
    """Test that TFLint download uses version variable, not API query."""
    assert 'api.github.com/repos/terraform-linters/tflint/releases/latest' \
        not in dockerfile_content
