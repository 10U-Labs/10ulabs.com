"""Pytest fixtures for diagnostics endpoint tests."""
import re
from typing import Dict

import boto3
import pytest
from repo_utils import REPO_ROOT

# Use shared layer marker plugin
pytest_plugins = ['pytest_layers']

DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"


@pytest.fixture(scope="module")
def logs_client(aws_region):
    """Create a CloudWatch Logs client."""
    return boto3.client("logs", region_name=aws_region)


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Load configuration from terraform.tfvars and shared outputs."""
    tfvars_path = DIAGNOSTICS_SRC / "terraform.tfvars"
    result: Dict[str, str] = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    result[key] = value.strip('"')
    result['aws_region'] = shared_config.get('aws_region', 'us-east-1')
    result['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    return result
