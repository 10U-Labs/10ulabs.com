"""Tests for Dockerfile Node.js installation."""


def test_dockerfile_installs_nodejs(dockerfile_run_commands_joined):
    """Test that Dockerfile installs Node.js."""
    assert dockerfile_run_commands_joined.find('node-v') != -1


def test_dockerfile_declares_node_version_arg(dockerfile_content):
    """Test that Dockerfile declares NODE_VERSION ARG."""
    assert dockerfile_content.find('ARG NODE_VERSION') != -1


def test_dockerfile_installs_jsonlint_via_npm(npm_install_packages):
    """Test that Dockerfile installs jsonlint via npm."""
    assert npm_install_packages.find('jsonlint') != -1


def test_dockerfile_installs_npm_packages_globally(npm_install_packages):
    """Test that Dockerfile installs npm packages globally."""
    assert npm_install_packages.find('-g') != -1
