import importlib.util
import os
import re
import sys
from dockerfile_parse import DockerfileParser
import pytest


BASE_DIR = os.path.join(os.path.dirname(__file__), '../../../../src/build/image_for_docker_runners')
sys.path.insert(0, BASE_DIR)
entrypoint_path = os.path.join(BASE_DIR, 'entrypoint.py')
entrypoint_spec = importlib.util.spec_from_file_location("entrypoint", entrypoint_path)
if entrypoint_spec is None or entrypoint_spec.loader is None:
    raise ImportError("Could not load entrypoint module")
entrypoint = importlib.util.module_from_spec(entrypoint_spec)
entrypoint_spec.loader.exec_module(entrypoint)

DOCKERFILE_PATH = os.path.join(BASE_DIR, 'Dockerfile')


@pytest.fixture
def dockerfile_content():
    with open(DOCKERFILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def dockerfile_parser():
    return DockerfileParser(path=DOCKERFILE_PATH)


@pytest.fixture
def apt_get_install_packages(dockerfile_content):
    match = re.search(r'apt-get install.*?(?=&&\s*rm|$)', dockerfile_content, re.DOTALL)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def pip3_install_packages(dockerfile_content):
    match = re.search(r'pip3 install.*?(?=&&\s*rm|$)', dockerfile_content, re.DOTALL)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def npm_install_packages(dockerfile_content):
    match = re.search(r'npm install.*', dockerfile_content)
    if match:
        return match.group(0)
    return ""


@pytest.fixture
def dockerfile_node_version(dockerfile_content):
    match = re.search(r'ARG\s+NODE_VERSION=(.+)', dockerfile_content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_terraform_version(dockerfile_content):
    match = re.search(r'ARG\s+TERRAFORM_VERSION=(.+)', dockerfile_content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_runner_version(dockerfile_content):
    match = re.search(r'ARG\s+RUNNER_VERSION=(.+)', dockerfile_content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_runner_arch(dockerfile_content):
    match = re.search(r'ARG\s+RUNNER_ARCH=(.+)', dockerfile_content)
    if match:
        return match.group(1)
    return ""


@pytest.fixture
def dockerfile_run_commands_joined(dockerfile_parser):
    commands = []
    structure = dockerfile_parser.structure
    i = 0
    while i < len(structure):
        if structure[i]['instruction'] == 'RUN':
            commands.append(structure[i]['value'])
        i += 1
    return ' '.join(commands)
