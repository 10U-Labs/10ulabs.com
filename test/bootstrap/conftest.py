from pathlib import Path
import pytest


@pytest.fixture
def bootstrap_dir():
    return Path(__file__).parent.parent.parent / "src" / "bootstrap"


@pytest.fixture
def config(bootstrap_dir):
    tfvars_path = bootstrap_dir / "terraform.tfvars"
    config_dict = {}
    with open(tfvars_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                config_dict[key] = value
    return config_dict
