import os
import re
import pytest


SHARED_OUTPUTS_PATH = os.path.join(os.path.dirname(__file__), '../../../src/modules/shared/outputs.tf')
ECR_DIR = os.path.join(os.path.dirname(__file__), '../../../src/ecr')


def parse_tf_output(file_path, output_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    return match.group(1) if match else None


@pytest.fixture(name="ecr_dir", scope="session")
def ecr_dir_fixture():
    return ECR_DIR


@pytest.fixture(name="ecr_repository_name", scope="session")
def ecr_repository_name_fixture():
    return parse_tf_output(SHARED_OUTPUTS_PATH, "ecr_repository_name")
