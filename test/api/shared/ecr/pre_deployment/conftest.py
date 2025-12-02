import os

import pytest


@pytest.fixture(name="backend_tf_content", scope="session")
def backend_tf_content_fixture(ecr_dir):
    path = os.path.join(ecr_dir, 'backend.tf')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture(name="main_tf_content", scope="session")
def main_tf_content_fixture(ecr_dir):
    path = os.path.join(ecr_dir, 'main.tf')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture(name="outputs_tf_content", scope="session")
def outputs_tf_content_fixture(ecr_dir):
    path = os.path.join(ecr_dir, 'outputs.tf')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
