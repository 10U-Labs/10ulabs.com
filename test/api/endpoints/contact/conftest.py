"""Pytest fixtures for contact endpoint tests."""
import re
from pathlib import Path
from typing import Dict

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
CONTACT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Create configuration fixture from terraform.tfvars and shared outputs."""
    tfvars_path = CONTACT_SRC / "terraform.tfvars"
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
    result['domain_name'] = shared_config.get('domain_name', '')
    return result
