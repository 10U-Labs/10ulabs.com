import re
from pathlib import Path
from typing import Dict
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
SIMULATION_SOC_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "simulation_soc"


def parse_shared_module_outputs() -> Dict[str, str]:
    outputs_path = REPO_ROOT / "lib" / "terraform" / "outputs.tf"
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
    shared = parse_shared_module_outputs()
    result['aws_region'] = shared.get('aws_region', 'us-east-1')
    result['api_fqdn'] = f"api.{shared.get('domain_name', '')}"
    return result
