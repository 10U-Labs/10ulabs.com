"""Unit tests to verify IAM role and Lambda function names use PascalCase.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import re
from pathlib import Path

import pytest

from naming_conventions import validate_name

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
RACK_DESIGNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_designer"
IAM_FILE = RACK_DESIGNER_SRC / "iam.tf"
LAMBDA_FILE = RACK_DESIGNER_SRC / "lambda.tf"
ANALYTICS_FILE = RACK_DESIGNER_SRC / "analytics.tf"


def get_resource_prefix() -> str:
    """Get the resource prefix from shared Terraform module."""
    shared_locals = REPO_ROOT / "lib" / "terraform" / "modules" / "shared" / "locals.tf"
    with open(shared_locals, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'resource_prefix\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else "TenULabs"


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
        name_match = re.search(r'^\s*name\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            role_name = name_match.group(1)
            resolved = role_name.replace("${local.resource_prefix}", prefix)
            roles.append((resource_name, resolved, tf_file.name))

    return roles


def extract_lambda_function_names(tf_file: Path) -> list:
    """Extract Lambda function names from a Terraform file."""
    if not tf_file.exists():
        return []
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    functions = []
    func_pattern = r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{'

    for match in re.finditer(func_pattern, content):
        resource_name = match.group(1)
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
        name_match = re.search(r'^\s*function_name\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            function_name = name_match.group(1)
            resolved = function_name.replace("${local.resource_prefix}", prefix)
            functions.append((resource_name, resolved, tf_file.name))

    return functions


# Collect from all relevant Terraform files
IAM_ROLES = (
    extract_iam_role_names(IAM_FILE)
    + extract_iam_role_names(ANALYTICS_FILE)
)
LAMBDA_FUNCTIONS = (
    extract_lambda_function_names(LAMBDA_FILE)
    + extract_lambda_function_names(ANALYTICS_FILE)
)


class TestIAMRoleNamingConventions:
    """Tests for IAM role naming conventions."""

    @pytest.mark.parametrize(
        "resource_name,role_name,source_file",
        IAM_ROLES,
        ids=[f"{r[2]}::{r[0]}" for r in IAM_ROLES] if IAM_ROLES else ["no_roles"],
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name, source_file):
        """Verify IAM role name uses PascalCase (no dashes or underscores)."""
        if not IAM_ROLES:
            pytest.skip("No IAM roles found")
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


class TestLambdaFunctionNamingConventions:
    """Tests for Lambda function naming conventions."""

    @pytest.mark.parametrize(
        "resource_name,function_name,source_file",
        LAMBDA_FUNCTIONS,
        ids=[f"{f[2]}::{f[0]}" for f in LAMBDA_FUNCTIONS] if LAMBDA_FUNCTIONS else ["no_functions"],
    )
    def test_lambda_function_name_is_pascalcase(self, resource_name, function_name, source_file):
        """Verify Lambda function name uses PascalCase (no dashes or underscores)."""
        if not LAMBDA_FUNCTIONS:
            pytest.skip("No Lambda functions found")
        error = validate_name(function_name)
        assert error is None, (
            f"Lambda function '{resource_name}' in {source_file} has invalid name '{function_name}': {error}"
        )

    def test_no_lambda_function_names_contain_dashes(self):
        """Verify no Lambda function names contain dashes."""
        violations = [(r, n, f) for r, n, f in LAMBDA_FUNCTIONS if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} Lambda functions with dashes:\n"
            + "\n".join(f"  - {f}::{r}: '{n}'" for r, n, f in violations)
        )
