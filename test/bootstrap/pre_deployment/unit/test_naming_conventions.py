import re

import pytest

from naming_conventions import validate_name
from repo_utils import REPO_ROOT
from terraform_config import get_resource_prefix

BOOTSTRAP_SRC = REPO_ROOT / "src" / "bootstrap"


def extract_iam_role_names_from_bootstrap_locals() -> list:
    locals_file = BOOTSTRAP_SRC / "locals.tf"
    if not locals_file.exists():
        return []

    with open(locals_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    roles = []

    for match in re.finditer(r'(name_for_\w*role\w*)\s*=\s*"([^"]*)"', content, re.I):
        local_name, value = match.groups()
        resolved = value.replace("${local.resource_prefix}", prefix)
        roles.append((local_name, resolved, "locals.tf"))

    return roles


IAM_ROLES = extract_iam_role_names_from_bootstrap_locals()


class TestIAMRoleNamingConventions:
    @pytest.mark.parametrize(
        "resource_name,role_name,source_file",
        IAM_ROLES if IAM_ROLES else [("NONE", "NONE", "NONE")],
        ids=([f"{r[2]}::{r[0]}" for r in IAM_ROLES]
             if IAM_ROLES else ["no_roles_found"]),
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name, source_file):
        if resource_name == "NONE":
            pytest.fail("No IAM roles found in bootstrap - check Terraform files")
        error = validate_name(role_name)
        assert error is None, (
            f"IAM role '{resource_name}' in {source_file} has invalid name "
            f"'{role_name}': {error}"
        )

    def test_no_iam_role_names_contain_dashes(self):
        violations = [(r, n, f) for r, n, f in IAM_ROLES if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with dashes:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )

    def test_no_iam_role_names_contain_underscores(self):
        violations = [(r, n, f) for r, n, f in IAM_ROLES if '_' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with underscores:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )

    def test_all_iam_role_names_start_with_uppercase(self):
        violations = [(r, n, f) for r, n, f in IAM_ROLES if n and not n[0].isupper()]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles not starting with uppercase:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )
