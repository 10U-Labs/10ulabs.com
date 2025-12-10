"""Unit tests to verify IAM role and Lambda function names use PascalCase.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import re
from pathlib import Path

import pytest

from naming_conventions import validate_name

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
IMAGE_ECS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ecs_runners"
IAM_FILE = IMAGE_ECS_SRC / "iam.tf"
LAMBDA_FILE = IMAGE_ECS_SRC / "lambda.tf"


def get_resource_prefix() -> str:
    """Get the resource prefix from shared Terraform module."""
    shared_locals = REPO_ROOT / "lib" / "terraform" / "modules" / "shared" / "locals.tf"
    with open(shared_locals, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'resource_prefix\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else "TenULabs"


def extract_block_content(content: str, start_pos: int) -> str:
    """Extract the content of a Terraform block starting at the given brace position."""
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

    for match in re.finditer(r'resource\s+"aws_iam_role"\s+"([^"]+)"\s*\{', content):
        block_content = extract_block_content(content, match.end() - 1)
        name_match = re.search(r'^\s*name\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            role_name = name_match.group(1).replace("${local.resource_prefix}", prefix)
            roles.append((match.group(1), role_name))

    return roles


def extract_lambda_function_names(tf_file: Path) -> list:
    """Extract Lambda function names from a Terraform file."""
    if not tf_file.exists():
        return []
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()

    prefix = get_resource_prefix()
    functions = []

    for match in re.finditer(r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{', content):
        block_content = extract_block_content(content, match.end() - 1)
        name_match = re.search(r'^\s*function_name\s*=\s*"([^"]+)"', block_content, re.MULTILINE)
        if name_match:
            func_name = name_match.group(1).replace("${local.resource_prefix}", prefix)
            functions.append((match.group(1), func_name))

    return functions


IAM_ROLES = extract_iam_role_names(IAM_FILE)
LAMBDA_FUNCTIONS = extract_lambda_function_names(LAMBDA_FILE)


class TestIAMRoleNamingConventions:
    """Tests for IAM role naming conventions."""

    @pytest.mark.parametrize(
        "resource_name,role_name",
        IAM_ROLES,
        ids=[f"iam_role_{r[0]}" for r in IAM_ROLES] if IAM_ROLES else ["no_roles"],
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
        """Verify IAM role name uses PascalCase (no dashes or underscores)."""
        if not IAM_ROLES:
            pytest.skip("No IAM roles found in iam.tf")
        error = validate_name(role_name)
        assert error is None, (
            f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
        )

    def test_no_iam_role_names_contain_dashes(self):
        """Verify no IAM role names contain dashes."""
        violations = [(r, n) for r, n in IAM_ROLES if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with dashes:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )


class TestLambdaFunctionNamingConventions:
    """Tests for Lambda function naming conventions."""

    @pytest.mark.parametrize(
        "resource_name,function_name",
        LAMBDA_FUNCTIONS,
        ids=[f"lambda_{f[0]}" for f in LAMBDA_FUNCTIONS] if LAMBDA_FUNCTIONS else ["no_functions"],
    )
    def test_lambda_function_name_is_pascalcase(self, resource_name, function_name):
        """Verify Lambda function name uses PascalCase (no dashes or underscores)."""
        if not LAMBDA_FUNCTIONS:
            pytest.skip("No Lambda functions found in lambda.tf")
        error = validate_name(function_name)
        assert error is None, (
            f"Lambda function '{resource_name}' has invalid name '{function_name}': {error}"
        )

    def test_no_lambda_function_names_contain_dashes(self):
        """Verify no Lambda function names contain dashes."""
        violations = [(r, n) for r, n in LAMBDA_FUNCTIONS if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} Lambda functions with dashes:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )
