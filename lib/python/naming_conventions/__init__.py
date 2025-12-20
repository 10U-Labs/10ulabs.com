"""
Naming convention validation module.

This module provides functions to validate AWS resource naming conventions,
specifically for ensuring IAM roles and Lambda functions use PascalCase.

Example usage:
    from naming_conventions import is_pascalcase, validate_name, find_violations

    # Check if a name is PascalCase
    is_pascalcase("TenULabsMyFunction")  # True
    is_pascalcase("TenULabs-MyFunction")  # False (contains dash)

    # Validate and get error message
    validate_name("TenULabs-MyFunction")  # Returns error string

    # Find violations in a list of names
    violations = find_violations(["TenULabsGood", "Bad-Name"])
"""

import re
from typing import List, Optional, Tuple

from repo_utils import extract_brace_block


def is_pascalcase(name: str) -> bool:
    """Check if a name follows PascalCase naming convention.

    PascalCase requirements:
    - Starts with an uppercase letter
    - Contains only alphanumeric characters (no dashes, underscores, spaces)
    - Each word starts with an uppercase letter

    Args:
        name: The name to validate.

    Returns:
        True if the name is valid PascalCase, False otherwise.
    """
    if not name:
        return False

    # Must start with uppercase letter
    if not name[0].isupper():
        return False

    # Must contain only alphanumeric characters
    if not name.isalnum():
        return False

    return True


def validate_name(name: str) -> Optional[str]:
    """Validate a resource name and return an error message if invalid.

    Args:
        name: The name to validate.

    Returns:
        None if valid, or an error message string describing the issue.
    """
    if not name:
        return "Name is empty"

    if not name[0].isupper():
        return f"Name '{name}' must start with uppercase letter"

    # Check for common violations
    if '-' in name:
        return f"Name '{name}' contains dash (-), use PascalCase instead"

    if '_' in name:
        return f"Name '{name}' contains underscore (_), use PascalCase instead"

    if ' ' in name:
        return f"Name '{name}' contains space, use PascalCase instead"

    if not name.isalnum():
        return f"Name '{name}' contains non-alphanumeric characters"

    return None


def find_violations(names: List[str]) -> List[Tuple[str, str]]:
    """Find all naming convention violations in a list of names.

    Args:
        names: List of names to check.

    Returns:
        List of tuples (name, error_message) for each violation.
    """
    violations = []
    for name in names:
        error = validate_name(name)
        if error:
            violations.append((name, error))
    return violations


def extract_iam_role_names_from_terraform(content: str) -> List[Tuple[str, str]]:
    """Extract IAM role names from Terraform file content.

    Parses both hardcoded role names and interpolated names.

    Args:
        content: Raw content of a Terraform .tf file.

    Returns:
        List of tuples (resource_name, role_name) found in the file.
    """
    roles = []
    role_block_pattern = r'resource\s+"aws_iam_role"\s+"([^"]+)"\s*\{'

    for match in re.finditer(role_block_pattern, content):
        resource_name = match.group(1)
        block_content = extract_brace_block(content, match.end() - 1)

        name_pattern = r'name\s*=\s*"([^"]+)"'
        name_match = re.search(name_pattern, block_content)
        if name_match:
            roles.append((resource_name, name_match.group(1)))

    return roles


def extract_lambda_function_names_from_terraform(content: str) -> List[Tuple[str, str]]:
    """Extract Lambda function names from Terraform file content.

    Parses both hardcoded function names and interpolated names.

    Args:
        content: Raw content of a Terraform .tf file.

    Returns:
        List of tuples (resource_name, function_name) found in the file.
    """
    functions = []
    function_block_pattern = r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{'

    for match in re.finditer(function_block_pattern, content):
        resource_name = match.group(1)
        block_content = extract_brace_block(content, match.end() - 1)

        name_pattern = r'function_name\s*=\s*"?([^"\n]+)"?'
        name_match = re.search(name_pattern, block_content)
        if name_match:
            function_name = name_match.group(1).strip()
            if not function_name.startswith('var.'):
                functions.append((resource_name, function_name))

    return functions


def resolve_terraform_interpolation(
    name: str,
    locals_dict: dict,
    resource_prefix: str = "TenULabs"
) -> str:
    """Resolve Terraform interpolation in a name string.

    Handles patterns like:
    - ${local.resource_prefix}SomeName -> TenULabsSomeName
    - ${local.resource_prefix}-SomeName -> TenULabs-SomeName

    Args:
        name: The name containing potential interpolations.
        locals_dict: Dict of local values for resolution.
        resource_prefix: Default resource prefix if not in locals.

    Returns:
        The resolved name with interpolations replaced.
    """
    prefix = locals_dict.get('resource_prefix', resource_prefix)

    # Replace ${local.resource_prefix} pattern
    resolved = re.sub(r'\$\{local\.resource_prefix\}', prefix, name)

    # Replace local.resource_prefix pattern (without braces)
    resolved = re.sub(r'local\.resource_prefix', prefix, resolved)

    return resolved
