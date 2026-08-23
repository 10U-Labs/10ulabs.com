"""
Naming convention validation module.

This module provides functions to validate AWS resource naming conventions,
specifically for ensuring IAM roles and Lambda functions use PascalCase,
and infrastructure resources use kebab-case.

Example usage:
    from naming_conventions import validate_name, validate_kebab_name

    # Validate and get error message
    validate_name("TenULabs-MyFunction")  # Returns error string

    # Validate kebab-case name
    validate_kebab_name("TenULabs-my-resource")  # Returns None (valid)
"""

import re
from typing import Optional


def validate_name(name: str) -> Optional[str]:
    """Validate a resource name and return an error message if invalid.

    Args:
        name: The name to validate.

    Returns:
        None if valid, or an error message string describing the issue.
    """
    if not name:
        return "Name is empty"

    # Define validation rules as (condition, error_message) tuples
    violations = [
        (not name[0].isupper(), f"Name '{name}' must start with uppercase letter"),
        ('-' in name, f"Name '{name}' contains dash (-), use PascalCase instead"),
        ('_' in name, f"Name '{name}' contains underscore (_), use PascalCase instead"),
        (' ' in name, f"Name '{name}' contains space, use PascalCase instead"),
        (not name.isalnum(), f"Name '{name}' contains non-alphanumeric characters"),
    ]

    for condition, error_msg in violations:
        if condition:
            return error_msg

    return None


def validate_kebab_name(name: str) -> Optional[str]:
    """Validate a kebab-case resource name and return an error message if invalid.

    Expected format: PascalCasePrefix-lowercase-words-with-hyphens
    Example: TenULabs-rack-configurations-backup

    Args:
        name: The name to validate.

    Returns:
        None if valid, or an error message string describing the issue.
    """
    if not name:
        return "Name is empty"

    if '-' not in name:
        return f"Name '{name}' must contain hyphens for kebab-case format"

    parts = name.split('-', 1)
    prefix, rest = parts[0], parts[1] if len(parts) > 1 else ""

    # Validate prefix
    if not prefix or not prefix[0].isupper() or not prefix.isalnum():
        return f"Name '{name}' prefix must be PascalCase (alphanumeric, starts uppercase)"

    # Validate rest
    if not rest or not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', rest):
        return f"Name '{name}' suffix must be lowercase words separated by hyphens"

    return None
