"""Shared pytest fixtures and utilities for API tests."""
import re
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

REPO_ROOT = Path(__file__).parent.parent.parent

# Add lib directory to sys.path for runner_labels and other lib imports
LIB_DIR = REPO_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


def parse_shared_config() -> Dict[str, Any]:
    """Parse the shared runners configuration from etc/runners.yml."""
    config_path = REPO_ROOT / "etc" / "runners.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_runner_labels() -> Dict[str, str]:
    """Get runner labels from the shared configuration."""
    shared_config = parse_shared_config()
    return shared_config.get('runner_labels', {})


def parse_shared_module_outputs() -> Dict[str, str]:
    """Parse Terraform outputs from the shared module."""
    outputs_path = REPO_ROOT / "lib" / "terraform" / "outputs.tf"
    config = {}
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    matches = re.findall(pattern, content)
    for key, value in matches:
        config[key] = value
    return config
