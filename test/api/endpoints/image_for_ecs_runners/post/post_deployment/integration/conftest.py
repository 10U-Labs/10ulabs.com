"""Test fixtures for ECS runner image integration tests."""
import subprocess

from test.api.endpoints.image_for_ecs_runners.conftest import CONFIG_PATH

import pytest
import yaml


def _read_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


ENTRYPOINT_IMPORT = (
    'import sys; sys.path.insert(0, "/home/runner"); import entrypoint; '
)


def run_command_in_container(tag, command):
    """Execute a command inside a Docker container."""
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "--entrypoint", "/bin/bash",
            tag, "-c", command
        ],
        check=False,
        capture_output=True,
        text=True
    )
    return result


@pytest.fixture(scope="module")
def config_node_version():
    """Fixture that provides the configured Node.js version."""
    config = _read_config()
    return config["node_version"]


@pytest.fixture(scope="module")
def config_terraform_version():
    """Fixture that provides the configured Terraform version."""
    config = _read_config()
    return config["terraform_version"]
