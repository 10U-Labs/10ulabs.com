import importlib.util
import os
import re
import sys

from test.image_for_docker_runners.conftest import BASE_DIR, FILES_DIR, DOCKERFILE_PATH

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
    with open(DOCKERFILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def dockerfile_content():
    return _read_dockerfile()


@pytest.fixture
def dockerfile_parser():
    return DockerfileParser(path=DOCKERFILE_PATH)


@pytest.fixture
def apt_get_install_packages():
    content = _read_dockerfile()
    match = re.search(r'apt-get install.*?(?=&&\s*rm|$)', content, re.DOTALL)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def pip3_install_packages():
    content = _read_dockerfile()
    match = re.search(r'python3 -m pip install.*', content, re.DOTALL)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def npm_install_packages():
    content = _read_dockerfile()
    match = re.search(r'npm install.*', content)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def dockerfile_node_version():
    content = _read_dockerfile()
    match = re.search(r'ARG\s+NODE_VERSION=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_terraform_version():
    content = _read_dockerfile()
    match = re.search(r'ARG\s+TERRAFORM_VERSION=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_runner_version():
    content = _read_dockerfile()
    match = re.search(r'ARG\s+RUNNER_VERSION=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_runner_arch():
    content = _read_dockerfile()
    match = re.search(r'ARG\s+RUNNER_ARCH=(.+)', content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_run_commands_joined():
    parser = DockerfileParser(path=DOCKERFILE_PATH)
    commands = []
    structure = parser.structure
    i = 0
    while i < len(structure):
        if structure[i]['instruction'] == 'RUN':
            commands.append(structure[i]['value'])
        i += 1
    return ' '.join(commands)
