"""Unit tests to verify IAM role names use PascalCase in bootstrap.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
from pathlib import Path

import pytest

from naming_conventions import validate_name
from terraform_config import extract_iam_role_names

REPO_ROOT = Path(__file__).parent.parent.parent.parent
BOOTSTRAP_SRC = REPO_ROOT / "src" / "bootstrap"


def find_all_tf_files_with_iam_roles() -> list:
    """Find all Terraform files in bootstrap that define IAM roles."""
    all_roles = []
    for tf_file in BOOTSTRAP_SRC.rglob("*.tf"):
        # Skip non-iam files and subdirectory modules
        if tf_file.name != "iam.tf":
            continue
        roles = extract_iam_role_names(tf_file)
        for resource_name, role_name in roles:
            all_roles.append((resource_name, role_name, tf_file.name))
    return all_roles


IAM_ROLES = find_all_tf_files_with_iam_roles()


class TestIAMRoleNamingConventions:
    """Tests for IAM role naming conventions in bootstrap."""

    @pytest.mark.parametrize(
        "resource_name,role_name,source_file",
        IAM_ROLES if IAM_ROLES else [("NONE", "NONE", "NONE")],
        ids=([f"{r[2]}::{r[0]}" for r in IAM_ROLES]
             if IAM_ROLES else ["no_roles_found"]),
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name, source_file):
        """Verify IAM role name uses PascalCase (no dashes or underscores)."""
        if resource_name == "NONE":
            pytest.fail("No IAM roles found in bootstrap - check Terraform files")
        error = validate_name(role_name)
        assert error is None, (
            f"IAM role '{resource_name}' in {source_file} has invalid name "
            f"'{role_name}': {error}"
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
