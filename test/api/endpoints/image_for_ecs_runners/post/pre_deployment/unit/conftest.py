"""Fixtures for pre-deployment tests of ECS runner Docker image."""
import importlib.util
import os
import re
import sys
from test.api.endpoints.image_for_ecs_runners.conftest import (
    BASE_DIR,
    FILES_DIR,
    DOCKERFILE_PATH,
)

from dockerfile_parse import DockerfileParser
import pytest

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, FILES_DIR)
entrypoint_path = os.path.join(FILES_DIR, 'entrypoint.py')
entrypoint_spec = importlib.util.spec_from_file_location("entrypoint", entrypoint_path)
if entrypoint_spec is None or entrypoint_spec.loader is None:
    raise ImportError("Could not load entrypoint module")
entrypoint = importlib.util.module_from_spec(entrypoint_spec)
sys.modules['entrypoint'] = entrypoint
entrypoint_spec.loader.exec_module(entrypoint)

promote_path = os.path.join(FILES_DIR, 'promote_docker_image.py')
promote_spec = importlib.util.spec_from_file_location("promote_docker_image", promote_path)
if promote_spec is None or promote_spec.loader is None:
    raise ImportError("Could not load promote_docker_image module")
promote_docker_image = importlib.util.module_from_spec(promote_spec)
sys.modules['promote_docker_image'] = promote_docker_image
promote_spec.loader.exec_module(promote_docker_image)


def _read_dockerfile():
    """Read and return the Dockerfile contents."""
    with open(DOCKERFILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def dockerfile_content():
    """Fixture providing the raw Dockerfile content."""
    return _read_dockerfile()


@pytest.fixture
def dockerfile_parser():
    """Fixture providing a DockerfileParser instance."""
    return DockerfileParser(path=DOCKERFILE_PATH)


@pytest.fixture
def apt_get_install_packages():
    """Fixture extracting apt-get install packages from runtime stage."""
    content = _read_dockerfile()
    # Split at runtime stage (second FROM) and search in runtime portion only
    parts = content.split('# Runtime stage')
    runtime_content = parts[1] if len(parts) > 1 else content
    # Match from apt-get install to the && that follows the package list
    match = re.search(r'apt-get install.*?&& \\', runtime_content, re.DOTALL)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def pip3_install_packages():
    """Fixture extracting pip3 install packages from Dockerfile."""
    content = _read_dockerfile()
    match = re.search(r'python3 -m pip install.*', content, re.DOTALL)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def npm_install_packages():
    """Fixture extracting npm install packages from Dockerfile."""
    content = _read_dockerfile()
    match = re.search(r'npm install.*', content)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def dockerfile_node_version():
    """Fixture extracting NODE_VERSION ARG from Dockerfile."""
    content = _read_dockerfile()
    match = re.search(r'ARG\s+NODE_VERSION=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_terraform_version():
    """Fixture extracting TERRAFORM_VERSION ARG from Dockerfile."""
    content = _read_dockerfile()
    match = re.search(r'ARG\s+TERRAFORM_VERSION=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_runner_version():
    """Fixture extracting RUNNER_VERSION ARG from Dockerfile."""
    content = _read_dockerfile()
    match = re.search(r'ARG\s+RUNNER_VERSION=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_runner_arch():
    """Fixture extracting RUNNER_ARCH ARG from Dockerfile."""
    content = _read_dockerfile()
    match = re.search(r'ARG\s+RUNNER_ARCH=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_run_commands_joined():
    """Fixture providing all RUN commands joined as a single string."""
    parser = DockerfileParser(path=DOCKERFILE_PATH)
    commands = []
    structure = parser.structure
    i = 0
    while i < len(structure):
        if structure[i]['instruction'] == 'RUN':
            commands.append(structure[i]['value'])
        i += 1
    return ' '.join(commands)
