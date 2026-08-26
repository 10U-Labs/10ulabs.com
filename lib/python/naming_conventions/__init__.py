import re
from typing import Optional


def validate_name(name: str) -> Optional[str]:
    if not name:
        return "Name is empty"

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
    if not name:
        return "Name is empty"

    if '-' not in name:
        return f"Name '{name}' must contain hyphens for kebab-case format"

    parts = name.split('-', 1)
    prefix, rest = parts[0], parts[1] if len(parts) > 1 else ""

    if not prefix or not prefix[0].isupper() or not prefix.isalnum():
        return f"Name '{name}' prefix must be PascalCase (alphanumeric, starts uppercase)"

    if not rest or not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', rest):
        return f"Name '{name}' suffix must be lowercase words separated by hyphens"

    return None
