import ast
import re
from pathlib import Path
import pytest


@pytest.fixture(name="tfvars", scope="module")
def tfvars_fixture():
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    config = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    config[key] = value.strip('"')
    return config


@pytest.fixture(name="cfg")
def cfg_fixture():
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    tfvars = {}
    with open(tfvars_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('['):
                    value = ast.literal_eval(value)
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                tfvars[key] = value

    return {
        "aws": {
            "account_id": tfvars.get("aws_account_id"),
            "region": tfvars.get("aws_region")
        },
        "naming": {
            "vpc_name": tfvars.get("vpc_name")
        },
        "github": {
            "runner_version": tfvars.get("github_runner_version")
        }
    }
