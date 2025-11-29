import os
import pytest


BASE_DIR = os.path.join(os.path.dirname(__file__), '../../src/ecr')
SHARED_OUTPUTS_PATH = os.path.join(os.path.dirname(__file__), '../../src/modules/shared/outputs.tf')


def parse_tf_output(file_path, output_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    import re
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    return match.group(1) if match else None


@pytest.fixture(name="config", scope="session")
def config_fixture():
    return {
        "aws_region": parse_tf_output(SHARED_OUTPUTS_PATH, "aws_region"),
        "ecr_repository_name": parse_tf_output(SHARED_OUTPUTS_PATH, "ecr_repository_name"),
    }
