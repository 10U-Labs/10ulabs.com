"""Tests for Dockerfile GitHub CLI installation."""


def test_dockerfile_installs_github_cli(dockerfile_run_commands_joined):
    """Test that Dockerfile installs GitHub CLI."""
    assert 'gh' in dockerfile_run_commands_joined


def test_dockerfile_downloads_github_cli_from_official_source(dockerfile_content):
    """Test that Dockerfile downloads GitHub CLI from official GitHub releases."""
    assert 'github.com/cli/cli/releases' in dockerfile_content


def test_dockerfile_extracts_github_cli_to_staging(dockerfile_content):
    """Test that Dockerfile extracts gh binary to staging directory."""
    assert 'bin/gh' in dockerfile_content


def test_dockerfile_uses_gh_version_build_arg(dockerfile_content):
    """Test that Dockerfile uses GH_VERSION build arg."""
    assert 'ARG GH_VERSION' in dockerfile_content


def test_dockerfile_gh_url_uses_version_variable(dockerfile_content):
    """Test that GitHub CLI download uses version variable, not API query."""
    assert 'api.github.com/repos/cli/cli/releases/latest' not in dockerfile_content
