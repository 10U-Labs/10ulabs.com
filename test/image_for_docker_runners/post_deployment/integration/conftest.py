import subprocess
import yaml
import pytest

from test.image_for_docker_runners.conftest import CONFIG_PATH


def _read_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_command_in_container(tag, command):
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/bin/bash", tag, "-c", command],
        check=False,
        capture_output=True,
        text=True
    )
    return result


@pytest.fixture(scope="module")
def config_node_version():
    config = _read_config()
    return config["node_version"]


@pytest.fixture(scope="module")
def config_terraform_version():
    config = _read_config()
    return config["terraform_version"]
