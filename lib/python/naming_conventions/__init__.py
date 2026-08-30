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
