"""Pytest configuration and fixtures for rack designer tests."""
import re
from pathlib import Path
from typing import Dict

import pytest


def parse_shared_module_outputs() -> Dict[str, str]:
    """Parse shared module outputs from terraform outputs.tf file."""
    base_path = Path(__file__).parent.parent.parent.parent.parent
    outputs_path = base_path / "lib" / "terraform" / "modules" / "shared" / "outputs.tf"
    config = {}
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    matches = re.findall(pattern, content)
    for key, value in matches:
        config[key] = value
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, str]:
    """Provide rack designer configuration for tests."""
    shared = parse_shared_module_outputs()
    result = {
        'aws_region': shared.get('aws_region', ''),
        'aws_account_id': shared.get('aws_account_id', ''),
        'domain_name': shared.get('domain_name', ''),
        'api_fqdn': f"api.{shared.get('domain_name', '')}",
        'resource_prefix': shared.get('resource_prefix', '')
    }
    return result
