"""
Terraform configuration parsing module.

This module provides functions to parse values from the shared Terraform module,
providing a single source of truth for configuration values across tests and tools.

Example usage:
    from terraform_config import get_shared_config

    config = get_shared_config()
    region = config['aws_region']
    bucket = config['name_for_terraform_state_bucket']
"""

import re
from pathlib import Path
from typing import Dict


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


REPO_ROOT = _find_repo_root()
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


def parse_locals() -> Dict[str, str]:
    """Parse locals from the shared Terraform module's locals.tf file.

    Returns:
        Dict mapping local variable names to their string values.
        Only simple string assignments are parsed (key = "value").
    """
    locals_path = SHARED_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()

    values = {}
    pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        key, value = match.groups()
        values[key] = value
    return values


def parse_outputs() -> Dict[str, str]:
    """Parse outputs from the shared Terraform module's outputs.tf file.

    Resolves local.* references using values from locals.tf.

    Returns:
        Dict mapping output names to their resolved string values.
    """
    outputs_path = SHARED_MODULE_DIR / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()

    locals_dict = parse_locals()
    values = {}

    # Match outputs with literal string values
    literal_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    for match in re.findall(literal_pattern, content):
        output_name, value = match
        values[output_name] = value

    # Match outputs that reference local.* and resolve them
    local_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*local\.(\w+)'
    for match in re.findall(local_pattern, content):
        output_name, local_name = match
        if local_name in locals_dict:
            values[output_name] = locals_dict[local_name]

    return values


def get_shared_config() -> Dict[str, str]:
    """Get all configuration values from the shared Terraform module.

    Combines locals and outputs into a single dict. Output values take
    precedence over locals if there are naming conflicts.

    Returns:
        Dict with all configuration values from the shared module.
    """
    config = parse_locals()
    config.update(parse_outputs())
    return config
