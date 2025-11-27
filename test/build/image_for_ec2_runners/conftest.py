import ast
import importlib.util
import os
import re
from pathlib import Path
from unittest.mock import MagicMock
import pytest
import yaml

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['EC2_AMI_PURPOSE_TAG'] = 'Purpose'
os.environ['EC2_AMI_PURPOSE_VALUE'] = 'GitHub self-hosted EC2 runner'
os.environ['EC2_AMI_STABLE_TAG'] = 'Stable'

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def load_module_from_path(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_shared_outputs():
    outputs_path = PROJECT_ROOT / "src" / "modules" / "shared" / "outputs.tf"
    outputs = {}
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    for match in re.finditer(r'output\s+"(\w+)"\s*\{[^}]*value\s*=\s*"([^"]*)"', content):
        outputs[match.group(1)] = match.group(2)
    return outputs


def get_runner_config():
    config_path = PROJECT_ROOT / "src" / "build" / "image_for_ec2_runners" / "config.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_config():
    tfvars_path = PROJECT_ROOT / "src" / "api" / "terraform.tfvars"
    result = get_shared_outputs()
    runner_config = get_runner_config()
    source_ami = runner_config.get("source_ami", "")
    source_ami_parts = source_ami.split("-")
    result["os_family"] = source_ami_parts[0] if source_ami_parts else ""
    result["os_version"] = source_ami_parts[1] if len(source_ami_parts) > 1 else ""
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('['):
                        value = ast.literal_eval(value)
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    result[key] = value
    if "fargate_cpu_architecture" in result:
        result["os_architecture"] = result["fargate_cpu_architecture"].lower()
    return result


@pytest.fixture(scope="session")
def config():
    return get_config()


@pytest.fixture(scope="session")
def aws_region(request):
    data = request.getfixturevalue("config")
    return data["aws_region"]


@pytest.fixture
def v1_handler():
    return load_module_from_path("v1_handler", PROJECT_ROOT / "src" / "api" / "lambdas" / "v1.py")


@pytest.fixture
def promote_ami():
    return load_module_from_path("promote_ami", PROJECT_ROOT / "src" / "build" / "image_for_ec2_runners" / "promote_ami.py")


@pytest.fixture
def mock_ec2_client():
    return MagicMock()


@pytest.fixture
def raise_runtime_error():
    return pytest.raises(RuntimeError)
