import importlib.util
import os
import re
from pathlib import Path
from unittest.mock import MagicMock
import pytest

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_REGION'] = 'us-east-1'

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def load_module(module_name, *path_parts):
    module_path = PROJECT_ROOT / "src" / "api" / Path(*path_parts)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_tfvars():
    tfvars_path = PROJECT_ROOT / "src" / "api" / "terraform.tfvars"
    config = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('['):
                        value = eval(value)
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    config[key] = value
    return config


@pytest.fixture(scope="module")
def tfvars():
    return get_tfvars()


@pytest.fixture(scope="module")
def aws_region(tfvars):
    return tfvars["aws_region"]


@pytest.fixture
def v1_handler():
    return load_module("v1_handler", "lambdas", "v1.py")


@pytest.fixture
def wait_for_status_checks():
    return load_module("wait_for_status_checks", "packer", "image_for_ec2_runners_post", "wait_for_status_checks.py")


@pytest.fixture
def promote_ami():
    return load_module("promote_ami", "packer", "image_for_ec2_runners_post", "promote_ami.py")


@pytest.fixture
def mock_ec2_client():
    return MagicMock()
