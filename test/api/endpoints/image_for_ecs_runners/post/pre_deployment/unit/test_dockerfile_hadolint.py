"""Tests for Dockerfile Hadolint installation."""


def test_dockerfile_installs_hadolint(dockerfile_run_commands_joined):
    """Test that Dockerfile installs Hadolint."""
    assert 'hadolint' in dockerfile_run_commands_joined


def test_dockerfile_downloads_hadolint_from_official_source(dockerfile_content):
    """Test that Dockerfile downloads Hadolint from official GitHub releases."""
    assert 'github.com/hadolint/hadolint/releases' in dockerfile_content


def test_dockerfile_uses_hadolint_version_build_arg(dockerfile_content):
    """Test that Dockerfile uses HADOLINT_VERSION build arg."""
    assert 'ARG HADOLINT_VERSION' in dockerfile_content


def test_dockerfile_hadolint_url_uses_version_variable(dockerfile_content):
    """Test that Hadolint download uses version variable, not API query."""
    assert 'api.github.com/repos/hadolint/hadolint/releases/latest' \
        not in dockerfile_content
