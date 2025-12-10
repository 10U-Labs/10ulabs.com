"""
Terraform configuration parsing module.

This module provides functions to parse values from the shared Terraform module,
providing a single source of truth for configuration values across tests and tools.

Example usage:
    from terraform_config import get_shared_config, TEST_AWS_REGION

    config = get_shared_config()
    region = config['aws_region']
    bucket = config['name_for_terraform_state_bucket']

    # For unit test mock data (fake ARNs, URLs, etc.):
    mock_arn = f'arn:aws:sns:{TEST_AWS_REGION}:123456789012:test-topic'
"""

import re
from pathlib import Path
from typing import Any, Dict


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


REPO_ROOT = _find_repo_root()
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


def _parse_map_block(content: str, map_name: str) -> Dict[str, str]:
    """Parse a map/object block from Terraform HCL content.

    Args:
        content: The full file content.
        map_name: Name of the map variable to parse.

    Returns:
        Dict mapping keys to their string values within the map block.
    """
    pattern = rf'{map_name}\s*=\s*\{{'
    match = re.search(pattern, content)
    if not match:
        return {}

    start_pos = match.end() - 1
    brace_count = 0
    end_pos = start_pos
    for i, char in enumerate(content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_pos = start_pos + i + 1
                break

    block_content = content[start_pos:end_pos]
    values = {}
    entry_pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for entry_match in re.finditer(entry_pattern, block_content):
        key, value = entry_match.groups()
        values[key] = value
    return values


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


def parse_lambda_handler_names() -> Dict[str, str]:
    """Parse lambda_handler_names map from shared Terraform module.

    Returns:
        Dict mapping handler keys (e.g., 'ecs_runner') to function names.
    """
    locals_path = SHARED_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()

    raw_values = _parse_map_block(content, "lambda_handler_names")

    # Resolve ${local.resource_prefix} references
    locals_dict = parse_locals()
    resource_prefix = locals_dict.get("resource_prefix", "")

    resolved = {}
    for key, value in raw_values.items():
        resolved[key] = value.replace("${local.resource_prefix}", resource_prefix)
    return resolved


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


def get_shared_config() -> Dict[str, Any]:
    """Get all configuration values from the shared Terraform module.

    Combines locals and outputs into a single dict. Output values take
    precedence over locals if there are naming conflicts.

    Returns:
        Dict with all configuration values from the shared module.
    """
    config: Dict[str, Any] = parse_locals()
    config.update(parse_outputs())
    config["lambda_handler_names"] = parse_lambda_handler_names()
    return config


# Single source of truth for AWS region - derived from Terraform shared module.
# Use this constant in unit tests for mock data (fake ARNs, URLs, etc.)
# instead of hardcoding region strings.
TEST_AWS_REGION = parse_locals().get("aws_region", "us-east-2")
