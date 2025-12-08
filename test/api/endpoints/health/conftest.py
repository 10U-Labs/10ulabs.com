"""Pytest fixtures for health endpoint tests."""
import re
from pathlib import Path
from typing import Dict

from test.api.conftest import parse_shared_module_outputs

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
HEALTH_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "health"


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, str]:
    """Create configuration fixture from terraform.tfvars and shared outputs."""
    tfvars_path = HEALTH_SRC / "terraform.tfvars"
    result: Dict[str, str] = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    result[key] = value.strip('"')
    shared = parse_shared_module_outputs()
    result['aws_region'] = shared.get('aws_region', 'us-east-1')
    result['api_fqdn'] = f"api.{shared.get('domain_name', '')}"
    return result
