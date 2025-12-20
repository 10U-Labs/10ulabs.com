"""Pytest fixtures for simulation-soc API tests."""
import re
from typing import Dict

import pytest
from repo_utils import REPO_ROOT

SIMULATION_SOC_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "simulation_soc"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Load test configuration from terraform.tfvars and shared outputs."""
    tfvars_path = SIMULATION_SOC_SRC / "terraform.tfvars"
    result = {}
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
