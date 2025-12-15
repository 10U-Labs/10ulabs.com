"""Unit tests to verify IAM role names use PascalCase in bootstrap.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import re
from pathlib import Path

import pytest

from naming_conventions import validate_name

REPO_ROOT = Path(__file__).parent.parent.parent.parent
BOOTSTRAP_SRC = REPO_ROOT / "src" / "bootstrap"


def get_resource_prefix() -> str:
    """Get the resource prefix from shared Terraform module."""
    shared_locals = REPO_ROOT / "lib" / "terraform" / "modules" / "shared" / "locals.tf"
    with open(shared_locals, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'resource_prefix\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else "TenULabs"


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
    """Extract IAM role names from a Terraform file."""
    if not tf_file.exists():
        return []
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    roles = []
    role_pattern = r'resource\s+"aws_iam_role"\s+"([^"]+)"\s*\{'

    for match in re.finditer(role_pattern, content):
        resource_name = match.group(1)
        block_content = _extract_block_content(content, match.end() - 1)
        name_match = re.search(r'^\s*name\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            role_name = name_match.group(1)
            resolved = role_name.replace("${local.resource_prefix}", prefix)
            roles.append((resource_name, resolved, tf_file.name))

    return roles


def find_all_tf_files_with_iam_roles() -> list:
    """Find all Terraform files in bootstrap that define IAM roles."""
    all_roles = []
    for tf_file in BOOTSTRAP_SRC.rglob("*.tf"):
        roles = extract_iam_role_names(tf_file)
        all_roles.extend(roles)
    return all_roles


IAM_ROLES = find_all_tf_files_with_iam_roles()


class TestIAMRoleNamingConventions:
    """Tests for IAM role naming conventions in bootstrap."""

    @pytest.mark.parametrize(
        "resource_name,role_name,source_file",
        IAM_ROLES if IAM_ROLES else [("NONE", "NONE", "NONE")],
        ids=[f"{r[2]}::{r[0]}" for r in IAM_ROLES] if IAM_ROLES else ["no_roles_found"],
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name, source_file):
        """Verify IAM role name uses PascalCase (no dashes or underscores)."""
        if resource_name == "NONE":
            pytest.fail("No IAM roles found in bootstrap - check Terraform files")
        error = validate_name(role_name)
        assert error is None, (
            f"IAM role '{resource_name}' in {source_file} has invalid name '{role_name}': {error}"
        )

    def test_no_iam_role_names_contain_dashes(self):
        """Verify no IAM role names contain dashes."""
        violations = [(r, n, f) for r, n, f in IAM_ROLES if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with dashes:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )

    def test_no_iam_role_names_contain_underscores(self):
        """Verify no IAM role names contain underscores."""
        violations = [(r, n, f) for r, n, f in IAM_ROLES if '_' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with underscores:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )

    def test_all_iam_role_names_start_with_uppercase(self):
        """Verify all IAM role names start with an uppercase letter."""
        violations = [(r, n, f) for r, n, f in IAM_ROLES if n and not n[0].isupper()]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles not starting with uppercase:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )
