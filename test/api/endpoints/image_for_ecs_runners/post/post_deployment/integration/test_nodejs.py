"""Tests for Node.js installation in ECS runner image."""
from .conftest import run_command_in_container


def test_nodejs_installed(docker_image):
    """Test that Node.js is installed."""
    result = run_command_in_container(docker_image, "which node")

    assert result.returncode == 0


def test_nodejs_version_matches(docker_image, config_node_version):
    """Test that Node.js version matches configuration."""
    result = run_command_in_container(
        docker_image,
        f"node --version | grep -q 'v{config_node_version}'"
    )

    assert result.returncode == 0


def test_npm_installed(docker_image):
    """Test that npm is installed."""
    result = run_command_in_container(docker_image, "which npm")

    assert result.returncode == 0


def test_eslint_installed_globally(docker_image):
    """Test that eslint is installed globally."""
    result = run_command_in_container(docker_image, "which eslint")

    assert result.returncode == 0


def test_jsonlint_installed_globally(docker_image):
    """Test that jsonlint is installed globally."""
    result = run_command_in_container(docker_image, "which jsonlint")

    assert result.returncode == 0


def test_node_path_includes_global_modules(docker_image):
    """Test that NODE_PATH includes global node_modules."""
    result = run_command_in_container(
        docker_image,
        "echo $NODE_PATH | grep -q '/usr/local/lib/node_modules'"
    )

    assert result.returncode == 0


def test_node_modules_symlink_exists(docker_image):
    """Test that node_modules symlink exists in WORKDIR for ESM resolution."""
    result = run_command_in_container(
        docker_image,
        "test -L /home/runner/node_modules"
    )

    assert result.returncode == 0


def test_esm_import_resolves_eslint_js(docker_image):
    """Test that ESM import can resolve @eslint/js from global node_modules."""
    cmd = (
        "node --input-type=module -e "
        "\"import js from '@eslint/js'; "
        "console.log(js.configs.recommended ? 'OK' : 'FAIL')\""
    )
    result = run_command_in_container(docker_image, cmd)

    assert result.returncode == 0


def test_esm_import_resolves_globals(docker_image):
    """Test that ESM import can resolve globals from global node_modules."""
    cmd = (
        "node --input-type=module -e "
        "\"import globals from 'globals'; "
        "console.log(globals.node ? 'OK' : 'FAIL')\""
    )
    result = run_command_in_container(docker_image, cmd)

    assert result.returncode == 0
