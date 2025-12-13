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


def get_resource_prefix() -> str:
    """Get the resource prefix from shared Terraform module."""
    return parse_locals().get("resource_prefix", "TenULabs")


def get_runners_resource_names(prefix: str | None = None) -> Dict[str, str]:
    """Get all resource names for the runners endpoint.

    Computes DynamoDB table names, SQS queue names, etc. from the resource prefix
    and lambda handler names. This is the single source of truth for runners
    resource naming.

    Args:
        prefix: Resource prefix. If None, reads from shared Terraform module.

    Returns:
        Dict mapping resource keys to their full names.
    """
    if prefix is None:
        prefix = get_resource_prefix()
    handler_names = parse_lambda_handler_names()
    webhook_handler = handler_names.get('webhook', f"{prefix}WebhookHandler")
    return {
        # DynamoDB tables (idempotency uses webhook handler name per locals.tf)
        'idempotency_table': f"{webhook_handler}-idempotency",
        'circuit_breaker_state_table': f"{prefix}-circuit-breaker-state",
        'workflow_runners_table': f"{prefix}-workflow-runners",
        'incidents_table': f"{prefix}-incidents",
        # SQS queues (PascalCase naming convention)
        'job_queue': f"{webhook_handler}Jobs",
        'job_dlq': f"{webhook_handler}JobDlq",
        'webhook_dlq': f"{webhook_handler}Dlq",
        'drift_recovery_queue': f"{prefix}DriftRecovery.fifo",
    }


def _resolve_prefix_refs(value: str, prefix: str) -> str:
    """Resolve resource_prefix references in a Terraform string value."""
    value = value.replace("${module.shared.resource_prefix}", prefix)
    value = value.replace("${local.resource_prefix}", prefix)
    return value


def _resolve_all_refs(value: str, prefix: str, handler_names: Dict[str, str]) -> str:
    """Resolve all module.shared references in a Terraform string value."""
    value = _resolve_prefix_refs(value, prefix)
    # Resolve ${module.shared.lambda_handler_names.X} interpolations
    for handler_key, handler_value in handler_names.items():
        value = value.replace(
            f"${{module.shared.lambda_handler_names.{handler_key}}}",
            handler_value
        )
    return value


def get_endpoint_local_values(tf_dir: Path) -> Dict[str, str]:
    """Extract local values from locals.tf in the given endpoint directory.

    Resolves ${module.shared.resource_prefix} and ${local.resource_prefix}
    references using the shared module's resource_prefix. Also resolves
    module.shared.lambda_handler_names.X references (both direct and interpolated).

    Args:
        tf_dir: Path to the endpoint's Terraform directory (e.g., src/api/endpoints/foo)

    Returns:
        Dict mapping local variable names to their resolved string values.
    """
    locals_file = tf_dir / "locals.tf"
    if not locals_file.exists():
        return {}
    with open(locals_file, encoding="utf-8") as f:
        content = f.read()
    locals_dict = {}
    prefix = get_resource_prefix()
    handler_names = parse_lambda_handler_names()

    # Parse quoted string values and resolve all interpolations
    for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', content):
        locals_dict[match.group(1)] = _resolve_all_refs(match.group(2), prefix, handler_names)

    # Parse module.shared.lambda_handler_names references (direct, not interpolated)
    for match in re.finditer(r'(\w+)\s*=\s*module\.shared\.lambda_handler_names\.(\w+)', content):
        local_name, handler_key = match.groups()
        if handler_key in handler_names:
            locals_dict[local_name] = handler_names[handler_key]

    return locals_dict


def _extract_block_content(content: str, start_pos: int) -> str:
    """Extract content of a Terraform block starting at the given brace position."""
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[start_pos:start_pos + i + 1]
    return content[start_pos:]


def extract_iam_role_names(tf_file: Path) -> list:
    """Extract IAM role names from a Terraform file.

    Handles both quoted strings (name = "Value") and local references
    (name = local.var_name).

    Args:
        tf_file: Path to the Terraform file (typically iam.tf)

    Returns:
        List of (resource_name, resolved_role_name) tuples.
    """
    if not tf_file.exists():
        return []
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    local_values = get_endpoint_local_values(tf_file.parent)
    roles = []

    for match in re.finditer(r'resource\s+"aws_iam_role"\s+"([^"]+)"\s*\{', content):
        block_content = _extract_block_content(content, match.end() - 1)
        name_match = re.search(r'^\s*name\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            role_name = _resolve_prefix_refs(name_match.group(1), prefix)
            roles.append((match.group(1), role_name))
        else:
            local_match = re.search(
                r'^\s*name\s*=\s*local\.(\w+)', block_content, re.MULTILINE
            )
            if local_match and local_match.group(1) in local_values:
                roles.append((match.group(1), local_values[local_match.group(1)]))

    return roles


def extract_lambda_function_names(tf_file: Path, use_handler_names: bool = False) -> list:
    """Extract Lambda function names from a Terraform file.

    Handles quoted strings, local references, and optionally module.shared references.

    Args:
        tf_file: Path to the Terraform file (typically lambda.tf)
        use_handler_names: If True, also resolve module.shared.lambda_handler_names refs

    Returns:
        List of (resource_name, resolved_function_name) tuples.
    """
    if not tf_file.exists():
        return []
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    local_values = get_endpoint_local_values(tf_file.parent)
    handler_names = parse_lambda_handler_names() if use_handler_names else {}
    functions = []

    for match in re.finditer(r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{', content):
        block_content = _extract_block_content(content, match.end() - 1)
        name_match = re.search(
            r'^\s*function_name\s*=\s*"([^"]+)"', block_content, re.MULTILINE
        )
        if name_match:
            func_name = _resolve_prefix_refs(name_match.group(1), prefix)
            functions.append((match.group(1), func_name))
        else:
            local_match = re.search(
                r'^\s*function_name\s*=\s*local\.(\w+)', block_content, re.MULTILINE
            )
            if local_match and local_match.group(1) in local_values:
                functions.append((match.group(1), local_values[local_match.group(1)]))
            elif use_handler_names:
                module_match = re.search(
                    r'^\s*function_name\s*=\s*module\.shared\.lambda_handler_names\.(\w+)',
                    block_content, re.MULTILINE
                )
                if module_match and module_match.group(1) in handler_names:
                    functions.append((match.group(1), handler_names[module_match.group(1)]))

    return functions


def extract_sqs_queue_names(tf_file: Path) -> list:
    """Extract SQS queue names from a Terraform file.

    Handles quoted strings and local references.

    Args:
        tf_file: Path to the Terraform file (typically sqs.tf)

    Returns:
        List of (resource_name, resolved_queue_name) tuples.
    """
    if not tf_file.exists():
        return []
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    local_values = get_endpoint_local_values(tf_file.parent)
    queues = []

    for match in re.finditer(r'resource\s+"aws_sqs_queue"\s+"([^"]+)"\s*\{', content):
        block_content = _extract_block_content(content, match.end() - 1)
        name_match = re.search(r'^\s*name\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            queue_name = _resolve_prefix_refs(name_match.group(1), prefix)
            queues.append((match.group(1), queue_name))
        else:
            local_match = re.search(
                r'^\s*name\s*=\s*local\.(\w+)', block_content, re.MULTILINE
            )
            if local_match and local_match.group(1) in local_values:
                queues.append((match.group(1), local_values[local_match.group(1)]))

    return queues
